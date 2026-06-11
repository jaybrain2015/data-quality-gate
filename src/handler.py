"""Lambda entry point: triggered when a CSV lands in the S3 landing bucket.

Flow: S3 put -> download CSV -> parse -> run checks -> build a result record
(metadata + lineage + verdict) -> store in DynamoDB -> alert Slack on failure.

parse_csv and build_record are pure (no AWS) so they unit-test locally.
process_object does the AWS I/O around them.
"""
from __future__ import annotations
import csv
import io
import os

import yaml

from checks import run_checks
from metadata import extract_metadata, make_result_id, build_lineage
from notify import notify_slack

CONFIG_PATH = os.environ.get("CONFIG_PATH", "config.yaml")
RESULTS_TABLE = os.environ.get("RESULTS_TABLE", "dq-gate-results")


def load_config(path=CONFIG_PATH):
    with open(path) as f:
        return yaml.safe_load(f)


def parse_csv(body_bytes):
    """Turn raw CSV bytes into (headers, rows). Pure: no AWS."""
    reader = csv.DictReader(io.StringIO(body_bytes.decode("utf-8")))
    rows = list(reader)
    headers = reader.fieldnames or []
    return headers, rows


def build_record(headers, rows, source_key, config):
    """Run checks + assemble the full result record. Pure: unit-testable."""
    results = run_checks(headers, rows, config.get("checks", {}))
    meta = extract_metadata(headers, rows, source_key)
    result_id = make_result_id(source_key, meta["extracted_at"])
    lineage = build_lineage(source_key, result_id)
    passed = all(r.passed for r in results)
    return {
        "result_id": result_id,
        "source_key": source_key,
        "passed": passed,
        "checks": [r.to_dict() for r in results],
        "metadata": meta,
        "lineage": lineage,
    }


def process_object(bucket, key, config):
    """Download one object from S3, evaluate it, store + alert. AWS I/O lives here."""
    import boto3
    s3 = boto3.client("s3")
    dynamodb = boto3.resource("dynamodb")

    obj = s3.get_object(Bucket=bucket, Key=key)
    headers, rows = parse_csv(obj["Body"].read())
    record = build_record(headers, rows, key, config)

    dynamodb.Table(RESULTS_TABLE).put_item(Item=record)

    if not record["passed"]:
        failed = ", ".join(c["name"] for c in record["checks"] if not c["passed"])
        notify_slack(f":rotating_light: Data quality FAILED for `{key}` -- {failed}")
    return record


def handler(event, context):
    config = load_config()
    processed = [
        process_object(rec["s3"]["bucket"]["name"], rec["s3"]["object"]["key"], config)
        for rec in event.get("Records", [])
    ]
    return {"processed": len(processed),
            "result_ids": [p["result_id"] for p in processed]}
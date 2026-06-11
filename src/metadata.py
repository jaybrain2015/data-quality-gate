"""Metadata + lineage extraction. Pure functions: no AWS, unit-testable."""
from __future__ import annotations
import hashlib
from datetime import datetime, timezone


def extract_metadata(headers, rows, source_key):
    return {
        "columns": headers,
        "column_count": len(headers),
        "row_count": len(rows),
        "source_key": source_key,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }


def make_result_id(source_key, extracted_at):
    raw = f"{source_key}:{extracted_at}".encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def build_lineage(source_key, result_id):
    return {
        "input": source_key,
        "output_record": result_id,
        "transform": "data-quality-gate",
    }
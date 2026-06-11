import os
import handler

SAMPLE = os.path.join(os.path.dirname(__file__), "sample_data")
CFG = {
    "checks": {
        "row_count": {"min_rows": 10},
        "required_columns": ["id", "amount", "currency"],
        "null_fraction": {"amount": {"max": 0.0}},
    }
}


def _read(name):
    with open(os.path.join(SAMPLE, name), "rb") as f:
        return f.read()


def test_parse_csv():
    headers, rows = handler.parse_csv(_read("good.csv"))
    assert headers == ["id", "amount", "currency"]
    assert len(rows) == 12


def test_build_record_good_passes():
    headers, rows = handler.parse_csv(_read("good.csv"))
    record = handler.build_record(headers, rows, "incoming/good.csv", CFG)
    assert record["passed"] is True
    assert record["metadata"]["row_count"] == 12
    assert record["lineage"]["input"] == "incoming/good.csv"


def test_build_record_bad_fails():
    headers, rows = handler.parse_csv(_read("bad.csv"))
    record = handler.build_record(headers, rows, "incoming/bad.csv", CFG)
    assert record["passed"] is False
from metadata import extract_metadata, make_result_id, build_lineage


def test_extract_metadata():
    headers = ["id", "amount"]
    rows = [{"id": "1", "amount": "10"}, {"id": "2", "amount": "20"}]
    meta = extract_metadata(headers, rows, "incoming/file.csv")
    assert meta["columns"] == ["id", "amount"]
    assert meta["column_count"] == 2
    assert meta["row_count"] == 2
    assert meta["source_key"] == "incoming/file.csv"
    assert "extracted_at" in meta


def test_make_result_id_is_stable():
    a = make_result_id("file.csv", "2026-06-11T09:00:00+00:00")
    b = make_result_id("file.csv", "2026-06-11T09:00:00+00:00")
    assert a == b
    assert len(a) == 16


def test_make_result_id_differs_by_input():
    assert make_result_id("file1.csv", "t") != make_result_id("file2.csv", "t")


def test_build_lineage():
    lin = build_lineage("incoming/file.csv", "abc123")
    assert lin["input"] == "incoming/file.csv"
    assert lin["output_record"] == "abc123"
    assert lin["transform"] == "data-quality-gate"
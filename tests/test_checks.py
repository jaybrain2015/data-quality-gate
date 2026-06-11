from checks import (
    check_row_count,
    check_required_columns,
    check_null_fraction,
    run_checks,
)


def test_row_count_pass():
    assert check_row_count([{}] * 10, 10).passed


def test_row_count_fail():
    assert not check_row_count([{}] * 3, 10).passed


def test_required_columns():
    assert check_required_columns(["id", "amount"], ["id"]).passed
    assert not check_required_columns(["id"], ["id", "amount"]).passed


def test_null_fraction():
    rows = [{"amount": "5"}, {"amount": ""}, {"amount": "7"}, {"amount": "9"}]
    assert not check_null_fraction(rows, "amount", 0.0).passed
    assert check_null_fraction(rows, "amount", 0.5).passed


def test_run_checks_all_pass():
    headers = ["id", "amount", "currency"]
    rows = [{"id": str(i), "amount": "10", "currency": "EUR"} for i in range(12)]
    cfg = {
        "row_count": {"min_rows": 10},
        "required_columns": ["id", "amount", "currency"],
        "null_fraction": {"amount": {"max": 0.0}},
    }
    assert all(r.passed for r in run_checks(headers, rows, cfg))


def test_run_checks_detects_bad_file():
    headers = ["id", "amount", "currency"]
    rows = [
        {"id": "1", "amount": "100", "currency": "EUR"},
        {"id": "2", "amount": "", "currency": "EUR"},
        {"id": "3", "amount": "75", "currency": ""},
    ]
    cfg = {
        "row_count": {"min_rows": 10},
        "required_columns": ["id", "amount", "currency"],
        "null_fraction": {"amount": {"max": 0.0}},
    }
    results = run_checks(headers, rows, cfg)
    assert not all(r.passed for r in results)
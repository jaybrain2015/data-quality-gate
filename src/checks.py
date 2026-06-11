"""Data quality checks. Pure functions: no AWS, no I/O, fully unit-testable."""
from __future__ import annotations
from dataclasses import dataclass, asdict


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str

    def to_dict(self):
        return asdict(self)


def check_row_count(rows, min_rows):
    n = len(rows)
    return CheckResult("row_count", n >= min_rows, f"{n} rows (min {min_rows})")


def check_required_columns(headers, required):
    missing = [c for c in required if c not in headers]
    passed = not missing
    detail = "all present" if passed else f"missing: {', '.join(missing)}"
    return CheckResult("required_columns", passed, detail)


def check_null_fraction(rows, column, max_null_fraction):
    if not rows:
        return CheckResult(f"null_fraction[{column}]", False, "no rows")
    total = len(rows)
    nulls = sum(1 for r in rows if (r.get(column) or "").strip() == "")
    frac = nulls / total
    passed = frac <= max_null_fraction
    return CheckResult(
        f"null_fraction[{column}]",
        passed,
        f"{frac:.2%} null (max {max_null_fraction:.2%})",
    )


def run_checks(headers, rows, config):
    """config is the 'checks' block from config.yaml."""
    results = []
    rc = config.get("row_count")
    if rc:
        results.append(check_row_count(rows, rc.get("min_rows", 1)))
    req = config.get("required_columns")
    if req:
        results.append(check_required_columns(headers, req))
    for col, rule in (config.get("null_fraction") or {}).items():
        results.append(check_null_fraction(rows, col, rule.get("max", 0.0)))
    return results
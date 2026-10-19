import json
from pathlib import Path

from verifier import verify_cases


HERE = Path(__file__).parent


def main() -> int:
    cases = json.loads((HERE / "fixtures.json").read_text(encoding="utf-8"))
    results = verify_cases(cases)
    expected = {case["case_id"]: case["expected_verdict"] for case in cases}
    for result in results:
        result["expected_verdict"] = expected[result["case_id"]]
        result["fixture_pass"] = result["verdict"] == result["expected_verdict"]
    print(json.dumps(results, indent=2))
    return 0 if all(item["fixture_pass"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

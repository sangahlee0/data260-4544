"""Verify the local HW11 Stock Watch deliverables."""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STOCK = ROOT / "stock-watch"
REPORTS = ROOT / "reports" / "hw11"
OUTPUT = REPORTS / "verification.json"


def check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "pass": bool(passed), "detail": detail}


def main() -> None:
    checks = []
    sources_path = STOCK / "sources.json"
    gold_path = STOCK / "golden" / "gold_template.json"
    fixture_dir = STOCK / "fixtures" / "hw_template"
    required = [
        STOCK / "watch.py",
        STOCK / "policy.md",
        sources_path,
        gold_path,
        fixture_dir / "newswire.xml",
        fixture_dir / "edgar_8k.xml",
        fixture_dir / "prices_nbrx.us.csv",
        fixture_dir / "prices_cbds.us.csv",
        fixture_dir / "prices_lksp.us.csv",
        REPORTS / "AI_USE.md",
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    checks.append(check("required_files", not missing, f"Missing: {missing}" if missing else "All HW11 files exist."))

    sources = json.loads(sources_path.read_text(encoding="utf-8"))
    live_price = next(s for s in sources["sources"] if s["id"] == "prices_live")
    live_edgar = next(s for s in sources["sources"] if s["id"] == "edgar_live")
    tickers = {t.split(".")[0].upper() for t in live_price["tickers"]}
    ciks = set(live_edgar["ciks"])
    checks.append(check("watchlist_and_ciks", tickers == {"AAPL", "NVDA", "MSFT"} and ciks == tickers,
                        f"Tickers: {sorted(tickers)}, CIKs: {sorted(ciks)}"))

    policy = (STOCK / "policy.md").read_text(encoding="utf-8")
    required_policy_terms = ["notify", "digest", "ask", "quiet", "1.01", "2.02", "5.02", "5%", "NVDA"]
    checks.append(check("materiality_policy", all(term in policy for term in required_policy_terms),
                        "Policy contains decision types, thresholds, and SEC item guidance."))

    gold = json.loads(gold_path.read_text(encoding="utf-8"))
    cases = gold.get("cases", [])
    categories = [case.get("category") for case in cases]
    counts = {category: categories.count(category) for category in sorted(set(categories))}
    valid_expected = {"notify", "digest", "ask", "quiet", "not_retrieved"}
    labels_ok = all(case.get("match_title") and case.get("expected") in valid_expected for case in cases)
    checks.append(check("golden_set", len(cases) == 12 and all(n == 2 for n in counts.values()) and labels_ok,
                        f"Cases: {len(cases)}, categories: {counts}"))

    xml_ok = True
    xml_counts = {}
    for name in ("newswire.xml", "edgar_8k.xml"):
        try:
            root = ET.parse(fixture_dir / name).getroot()
            xml_counts[name] = len(root.findall(".//item")) + len(root.findall(".//{*}entry"))
        except (ET.ParseError, OSError):
            xml_ok = False
    csv_ok = True
    for name in ("prices_nbrx.us.csv", "prices_cbds.us.csv", "prices_lksp.us.csv"):
        try:
            with (fixture_dir / name).open(encoding="utf-8", newline="") as source:
                csv_ok = csv_ok and bool(list(csv.DictReader(source)))
        except OSError:
            csv_ok = False
    checks.append(check("fixture_validity", xml_ok and csv_ok, f"XML counts: {xml_counts}; CSV files parsed."))

    all_passed = all(item["pass"] for item in checks)
    result = {
        "homework": 11,
        "sid4": "4544",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "all_passed": all_passed,
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if all_passed else 1)


if __name__ == "__main__":
    main()

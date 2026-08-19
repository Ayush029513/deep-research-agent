from pathlib import Path


def save_report(report: str, filename: str = "report.md"):
    reports_dir = Path("app/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    path = reports_dir / filename

    path.write_text(report, encoding="utf-8")

    return path
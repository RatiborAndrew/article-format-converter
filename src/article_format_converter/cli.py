from __future__ import annotations

import argparse
import json
from pathlib import Path

from article_format_converter.service import analyze_docx, analyze_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check an article against journal formatting requirements.")
    parser.add_argument("input", help="Path to a .docx or .txt article draft.")
    parser.add_argument("--profile", default="pravoslavny-teolog", help="Journal profile id.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        parser.error(f"Input file does not exist: {input_path}")

    if input_path.suffix.lower() == ".docx":
        report = analyze_docx(input_path, profile_id=args.profile)
    else:
        report = analyze_text(input_path.read_text(encoding="utf-8"), profile_id=args.profile)

    indent = 2 if args.pretty else None
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=indent))
    return 0

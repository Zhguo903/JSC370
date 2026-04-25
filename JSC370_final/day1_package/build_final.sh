#!/usr/bin/env bash
set -euo pipefail

# Run from JSC370_final/day1_package
python scripts/03_day2_modeling.py
python scripts/04_day2_topic_modeling.py
python scripts/05_day2_interactive_viz.py
python scripts/06_generate_report_text.py

if command -v quarto >/dev/null 2>&1; then
  quarto render
  quarto render report.qmd --to pdf
  cp -f report.pdf docs/report.pdf
  echo "Rendered Quarto website and PDF."
else
  echo "Quarto not found. Install Quarto or render report.qmd manually."
fi

# JSC370 Final Project

**Title:** From Technology Story to Public Issue: Modeling The Guardian's AI Coverage, 2021–2025

This project studies how AI-related coverage in *The Guardian* changed between 2021 and 2025. It builds a broad search corpus and a stricter AI-focused corpus using the Guardian Content API, validates corpus precision through a manual audit, and then uses classification models and LDA topic modeling to analyze how AI coverage is framed.

## Website

After GitHub Pages is enabled, the website should be available at:

https://zhguo903.github.io/JSC370/

## Data source

The data are collected from the Guardian Content API:

https://open-platform.theguardian.com/

The final project uses saved CSV files in `data/` so that the report can be reproduced without rerunning the API download. If the API download is rerun, set the API key as an environment variable rather than writing it in code:

```bash
export GUARDIAN_API_KEY="your_key_here"
```

## Reproducibility

Install dependencies:

```bash
pip install -r requirements_final.txt
```

Run the final scripts from the project folder:

```bash
python scripts/03_day2_modeling.py
python scripts/04_day2_topic_modeling.py
python scripts/05_day2_interactive_viz.py
python scripts/06_generate_report_text.py
```

Render the website and report using Quarto:

```bash
quarto render
quarto render report.qmd --to pdf
cp report.pdf docs/report.pdf
```

If the Git repository root is one level above the project folder, copy the rendered website to the root `docs/` folder for GitHub Pages:

```bash
python scripts/07_copy_docs_to_repo_root.py
```

## Main files

- `data/guardian_ai_articles_broad_final.csv`: broad AI-related search corpus.
- `data/guardian_ai_articles_final.csv`: strict AI-focused corpus used for modeling.
- `data/manual_audit_completed.csv`: manually reviewed audit sample.
- `scripts/03_day2_modeling.py`: classification models.
- `scripts/04_day2_topic_modeling.py`: LDA topic model.
- `scripts/05_day2_interactive_viz.py`: Plotly interactive visualizations.
- `report.qmd`: written report.
- `index.qmd` and `viz.qmd`: website pages.

# Day 1 Final Project Package

Project: **From Technology Story to Public Issue: Modeling The Guardian's AI Coverage, 2021–2025**

This package completes the Day 1 setup for the final project:

1. final research questions and hypotheses
2. revised search-term justification
3. strict corpus construction rules
4. manual audit sampling protocol
5. target variable definition for later modeling
6. feature engineering for final prediction models
7. Day 1 figures: monthly volume, top sections, and section share over time

## Where to put these files

Copy the contents of this folder into the root of your final GitHub repository, for example:

```text
JSC370-finalproject/
├── README_DAY1.md
├── report_day1_draft.qmd
├── requirements_day1.txt
├── scripts/
├── report_text/
├── data/
├── figures/
└── outputs/
```

## Option A: Use your existing midterm data cache

If your midterm project already generated a file such as:

```text
data/guardian_articles_full.pkl
```

or

```text
data/guardian_articles_full.csv
```

place it in the `data/` folder. Then run:

```bash
python scripts/01_day1_build_dataset_features_figures.py --no-fetch-if-missing
```

This will build the final strict corpus, target variable, features, audit sample, and figures from the existing data.

## Option B: Fetch data again from The Guardian API

Set your API key in your shell:

```bash
export GUARDIAN_API_KEY="your_key_here"
```

Then run:

```bash
python scripts/01_day1_build_dataset_features_figures.py --fetch-if-missing
```

The script will query the Guardian Content API month by month and save the broad corpus before creating the strict final corpus.

## Expected Day 1 outputs

After running `01_day1_build_dataset_features_figures.py`, you should have:

```text
data/guardian_ai_articles_broad_final.csv
 data/guardian_ai_articles_strict_final.csv
 data/guardian_ai_articles_final.csv
 data/manual_audit_sample.csv
 outputs/day1_dataset_summary.csv
 outputs/day1_monthly_counts.csv
 outputs/day1_top_sections_strict.csv
 figures/figure1_monthly_volume_broad_vs_strict.png
 figures/figure2_top_sections_strict.png
 figures/figure3_section_share_over_time_strict.png
```

## Manual audit

Open:

```text
data/manual_audit_sample.csv
```

Fill in the `reviewer_label` column using exactly one of:

```text
core_ai_article
incidental_ai_mention
unclear
```

Then save the completed file as:

```text
data/manual_audit_completed.csv
```

Run:

```bash
python scripts/02_day1_summarize_manual_audit.py
```

This creates:

```text
outputs/manual_audit_summary.csv
figures/figure0_manual_audit_precision.png
```

## What to write in the final report after Day 1

Use `report_text/day1_introduction_methods_summary.md` and `report_day1_draft.qmd` as copy-ready text for your final report. The text directly addresses the midterm feedback: it adds motivation, explains search-term choices, defines the final prediction target, and describes the manual audit and feature engineering strategy.

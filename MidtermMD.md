# Midterm Project — The Guardian Open Platform

Author: Zihan Guo

## Project overview

This project studies how *The Guardian*'s coverage of artificial intelligence changed from 2021-01-01 to 2025-12-31 using the Guardian Content API.

The analysis builds a monthly article corpus from the union of five AI-related search terms:

- `artificial intelligence`
- `machine learning`
- `generative AI`
- `large language model`
- `ChatGPT`

After downloading all available API pages for each term and month, articles are deduplicated by Guardian article ID. The notebook then produces descriptive analyses of:

- monthly article volume
- broad versus strict corpus comparison
- section distribution
- section mix over time
- Guardian editorial-format tags
- keyword tags
- sentiment over time
- sentiment across sections

A stricter corpus is also defined using AI-related keyword tags and headline/trail-text pattern matching to reduce incidental mentions.

## Data source

The project uses the [Guardian Open Platform](https://open-platform.theguardian.com/), specifically the `/search` endpoint from the Guardian Content API.

The notebook requests:

- all months from January 2021 through December 2025
- all available pages for each month-query combination
- article fields: `headline`, `trailText`, `wordcount`, `byline`
- tag types: `keyword`, `tone`

## Research questions

The notebook addresses three main questions:

1. How has the monthly number of AI-related Guardian articles changed over time?
2. Which sections publish the most AI-related articles, and how does section composition vary?
3. How does sentiment vary over time and across sections?

In addition, Guardian API “tone” tags are treated as editorial-format labels rather than direct measures of positive or negative sentiment.

## Quick start

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
export GUARDIAN_API_KEY="your_key_here"
quarto render midterm.qmd
```

## API key setup
The notebook includes a placeholder example:

```python
import os
os.environ["GUARDIAN_API_KEY"] = "YOUR_KEY_HERE"
```

For reproducibility and security, it is better to set the key in your shell environment before rendering.

## How to run the project

### Render the Quarto notebook to HTML

```bash
quarto render midterm.qmd --to html
```
## License and usage

This repository is for course project use. Please check Guardian Open Platform terms separately if redistributing downloaded data.
#!/usr/bin/env python3
"""
Day 1 builder for JSC370 final project.

This script creates the final Day 1 data products from either:
  1. an existing midterm data cache in data/guardian_articles_full.pkl or .csv, or
  2. a fresh Guardian API download when GUARDIAN_API_KEY is available.

Outputs:
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
"""

from __future__ import annotations

import argparse
import ast
import html as ihtml
import math
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

GUARDIAN_BASE = "https://content.guardianapis.com"

# Expanded query list. Standalone "AI" is intentionally not used as a broad API query.
DEFAULT_SEARCH_TERMS = [
    "artificial intelligence",
    "machine learning",
    "generative AI",
    "large language model",
    "ChatGPT",
    "deep learning",
    "neural network",
    "LLM",
    "OpenAI",
    "Google Gemini",
    "Google DeepMind",
    "Claude AI",
    "DALL-E",
    "Midjourney",
]

AI_KEYWORD_PATTERNS = [
    r"\bai\b",
    r"artificial intelligence",
    r"machine learning",
    r"deep learning",
    r"neural network",
    r"large language model",
    r"large language models",
    r"llm",
    r"llms",
    r"generative ai",
    r"chatgpt",
    r"openai",
    r"google gemini",
    r"gemini ai",
    r"google deepmind",
    r"deepmind",
    r"claude ai",
    r"anthropic",
    r"dall-e",
    r"dalle",
    r"midjourney",
]

AI_TEXT_DIRECT_PATTERNS = [
    r"\bartificial intelligence\b",
    r"\bmachine learning\b",
    r"\bdeep learning\b",
    r"\bneural network(?:s)?\b",
    r"\bgenerative ai\b",
    r"\blarge language model(s)?\b",
    r"\bllm(s)?\b",
    r"\bchatgpt\b",
    r"\bopenai\b",
    r"\bgoogle gemini\b",
    r"\bgemini ai\b",
    r"\bgoogle deepmind\b",
    r"\bdeepmind\b",
    r"\bclaude ai\b",
    r"\banthropic\b",
    r"\bdall[- ]?e\b",
    r"\bmidjourney\b",
]

AI_CONTEXT_WORDS_FOR_STANDALONE_AI = [
    "artificial", "intelligence", "machine", "learning", "model", "models",
    "algorithm", "algorithms", "chatbot", "chatbots", "generative", "automation",
    "automated", "technology", "software", "tool", "tools", "regulation", "regulate",
    "risk", "risks", "ethics", "copyright", "jobs", "workers", "education",
    "openai", "chatgpt", "llm", "neural", "deep learning",
]

KEYWORD_FLAG_PATTERNS = {
    "has_chatgpt": r"\bchatgpt\b",
    "has_openai": r"\bopenai\b",
    "has_llm": r"\bllm(?:s)?\b|\blarge language model(?:s)?\b",
    "has_generative_ai": r"\bgenerative ai\b",
    "has_machine_learning": r"\bmachine learning\b",
    "has_deep_learning": r"\bdeep learning\b",
    "has_neural_network": r"\bneural network(?:s)?\b",
    "has_gemini": r"\bgemini\b|\bgoogle gemini\b",
    "has_claude": r"\bclaude\b|\banthropic\b",
    "has_dalle_midjourney": r"\bdall[- ]?e\b|\bmidjourney\b",
    "has_regulation": r"\bregulat(?:e|ion|ions|ory)\b|\blaw(?:s)?\b|\bpolicy\b|\bgovernance\b",
    "has_jobs_labor": r"\bjob(?:s)?\b|\blabou?r\b|\bworker(?:s)?\b|\bemployment\b|\bautomation\b",
    "has_education": r"\beducation\b|\bschool(?:s)?\b|\bstudent(?:s)?\b|\bexam(?:s)?\b|\buniversit(?:y|ies)\b",
    "has_copyright_creativity": r"\bcopyright\b|\bartist(?:s)?\b|\bwriter(?:s)?\b|\bcreative\b|\bmusic\b|\bfilm\b|\bbook(?:s)?\b",
    "has_risk_ethics": r"\brisk(?:s)?\b|\bethic(?:s|al)?\b|\bharm(?:s)?\b|\bdanger(?:s|ous)?\b|\bsafety\b",
    "has_election_misinformation": r"\belection(?:s)?\b|\bmisinformation\b|\bdisinformation\b|\bfake\b|\bdeepfake(?:s)?\b",
}

FORMAT_FLAGS = {
    "format_news": "news",
    "format_comment": "comment",
    "format_features": "features",
    "format_reviews": "reviews",
    "format_analysis": "analysis",
    "format_explainers": "explainers",
    "format_interviews": "interviews",
}


def strip_html(x: Any) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ""
    x = str(x)
    x = re.sub(r"<[^>]+>", " ", x)
    x = ihtml.unescape(x)
    x = re.sub(r"\s+", " ", x).strip()
    return x


def parse_list_like(x: Any) -> list[str]:
    """Convert list-like CSV/pickle cells into a clean list of strings."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return []
    if isinstance(x, list):
        return [str(v) for v in x if str(v).strip()]
    if isinstance(x, tuple) or isinstance(x, set):
        return [str(v) for v in x if str(v).strip()]
    s = str(x).strip()
    if not s or s.lower() in {"nan", "none", "[]"}:
        return []
    if s.startswith("[") and s.endswith("]"):
        try:
            out = ast.literal_eval(s)
            if isinstance(out, list):
                return [str(v) for v in out if str(v).strip()]
        except Exception:
            pass
    if ";" in s:
        return [v.strip() for v in s.split(";") if v.strip()]
    if "|" in s:
        return [v.strip() for v in s.split("|") if v.strip()]
    return [s]


def month_table(from_date: str, to_date: str) -> pd.DataFrame:
    start = pd.to_datetime(from_date)
    end = pd.to_datetime(to_date)
    month_starts = pd.date_range(start=start.replace(day=1), end=end.replace(day=1), freq="MS")
    month_ends = month_starts + pd.offsets.MonthEnd(0)
    month_ends = month_ends.where(month_ends <= end, end)
    return pd.DataFrame({"month_start": pd.to_datetime(month_starts), "month_end": pd.to_datetime(month_ends)})


def require_api_key() -> str:
    key = os.getenv("GUARDIAN_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "GUARDIAN_API_KEY is not set. Either place an existing data file in data/ "
            "or set the API key and rerun with --fetch-if-missing."
        )
    return key


def guardian_get_json(path: str = "search", query: dict[str, Any] | None = None, max_tries: int = 6) -> dict[str, Any]:
    api_key = require_api_key()
    query = dict(query or {})
    query["api-key"] = api_key
    url = f"{GUARDIAN_BASE}/{path.lstrip('/')}"
    headers = {"User-Agent": "JSC370-final-project-day1"}
    for i in range(1, max_tries + 1):
        try:
            r = requests.get(url, params=query, headers=headers, timeout=30)
        except requests.RequestException:
            wait = min(2 ** (i - 1), 30)
            time.sleep(wait)
            continue
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 500, 502, 503, 504):
            wait = min(2 ** (i - 1), 30)
            time.sleep(wait)
            continue
        raise RuntimeError(f"Guardian API error HTTP {r.status_code}: {r.text[:500]}")
    raise RuntimeError("Guardian API request failed after retries.")


def tags_to_list(tags: list[dict[str, Any]], tag_type: str) -> list[str]:
    out: list[str] = []
    for t in tags or []:
        if (t or {}).get("type") == tag_type:
            title = (t or {}).get("webTitle")
            if title:
                out.append(str(title))
    return out


def parse_results(results: list[dict[str, Any]], source_query: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for x in results:
        fields = x.get("fields", {}) or {}
        tags = x.get("tags", []) or []
        pub_dt = pd.to_datetime(x.get("webPublicationDate", None), utc=True, errors="coerce")
        headline = fields.get("headline") or x.get("webTitle") or ""
        trail = strip_html(fields.get("trailText") or "")
        rows.append({
            "id": x.get("id"),
            "source_query": source_query,
            "section_id": x.get("sectionId"),
            "section_name": x.get("sectionName"),
            "pillar_id": x.get("pillarId"),
            "pillar_name": x.get("pillarName"),
            "web_url": x.get("webUrl"),
            "web_title": x.get("webTitle"),
            "publication_datetime_utc": pub_dt,
            "publication_date": pub_dt.date() if pd.notnull(pub_dt) else pd.NaT,
            "headline": headline,
            "trail_text": trail,
            "byline": fields.get("byline"),
            "wordcount": pd.to_numeric(fields.get("wordcount"), errors="coerce"),
            "keywords": tags_to_list(tags, "keyword"),
            "format_tags": tags_to_list(tags, "tone"),
        })
    return pd.DataFrame(rows)


def fetch_month_page(
    from_date: str,
    to_date: str,
    q: str,
    page_size: int,
    order_by: str,
    show_fields: str,
    show_tags: str,
    page: int = 1,
) -> tuple[int, int, pd.DataFrame]:
    params_q = {
        "q": q,
        "from-date": from_date,
        "to-date": to_date,
        "page-size": int(page_size),
        "page": int(page),
        "order-by": order_by,
        "show-fields": show_fields,
        "show-tags": show_tags,
    }
    dat = guardian_get_json("search", params_q)
    resp = dat.get("response", {})
    total = int(resp.get("total", 0))
    pages = int(resp.get("pages", 1))
    results = resp.get("results", []) or []
    df = parse_results(results, source_query=q)
    return total, pages, df


def fetch_month_query_all_pages(
    from_date: str,
    to_date: str,
    q: str,
    page_size: int,
    order_by: str,
    show_fields: str,
    show_tags: str,
    sleep_s: float = 1.05,
) -> pd.DataFrame:
    _, pages, df1 = fetch_month_page(from_date, to_date, q, page_size, order_by, show_fields, show_tags, page=1)
    dfs = [df1]
    for p in range(2, pages + 1):
        _, _, dfi = fetch_month_page(from_date, to_date, q, page_size, order_by, show_fields, show_tags, page=p)
        dfs.append(dfi)
        time.sleep(float(sleep_s))
    out = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    if not out.empty and "id" in out.columns:
        out = out.drop_duplicates(subset=["id"])
    return out


def fetch_all_articles(args: argparse.Namespace) -> pd.DataFrame:
    months = month_table(args.from_date, args.to_date)
    cache_dir = Path(args.data_dir) / "guardian_month_cache_final"
    cache_dir.mkdir(parents=True, exist_ok=True)
    month_frames: list[pd.DataFrame] = []
    search_terms = [t.strip() for t in args.search_terms.split("||") if t.strip()]
    if not search_terms:
        search_terms = DEFAULT_SEARCH_TERMS

    for _, row in months.iterrows():
        m_from = row["month_start"].strftime("%Y-%m-%d")
        m_to = row["month_end"].strftime("%Y-%m-%d")
        month_key = row["month_start"].strftime("%Y_%m")
        cache_file = cache_dir / f"guardian_articles_{month_key}.pkl"
        if cache_file.exists() and not args.refresh:
            dfi = pd.read_pickle(cache_file)
        else:
            dfs = []
            print(f"Fetching {month_key} ...")
            for term in search_terms:
                print(f"  query: {term}")
                term_df = fetch_month_query_all_pages(
                    from_date=m_from,
                    to_date=m_to,
                    q=term,
                    page_size=args.page_size,
                    order_by=args.order_by,
                    show_fields="headline,trailText,wordcount,byline",
                    show_tags="keyword,tone",
                    sleep_s=args.sleep_s,
                )
                dfs.append(term_df)
                time.sleep(args.sleep_s)
            dfi = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
            if not dfi.empty:
                dfi = dfi.drop_duplicates(subset=["id"])
            dfi.to_pickle(cache_file)
        month_stamp = row["month_start"].to_period("M").to_timestamp()
        dfi["month"] = month_stamp
        dfi["year"] = month_stamp.year
        month_frames.append(dfi)
    articles = pd.concat(month_frames, ignore_index=True) if month_frames else pd.DataFrame()
    if not articles.empty:
        articles = articles.drop_duplicates(subset=["id"]).reset_index(drop=True)
    return articles


def load_existing_data(data_dir: Path) -> pd.DataFrame | None:
    candidates = [
        data_dir / "guardian_articles_full.pkl",
        data_dir / "guardian_ai_articles_broad_final.pkl",
        data_dir / "guardian_articles_full.csv",
        data_dir / "guardian_ai_articles_broad_final.csv",
    ]
    for p in candidates:
        if p.exists():
            print(f"Loading existing data: {p}")
            if p.suffix == ".pkl":
                return pd.read_pickle(p)
            return pd.read_csv(p)
    return None


def normalize_articles(articles: pd.DataFrame) -> pd.DataFrame:
    if articles.empty:
        raise RuntimeError("Article data is empty.")
    articles = articles.copy()
    if "id" not in articles.columns:
        raise RuntimeError("Data must contain an 'id' column for Guardian article IDs.")

    for col in ["headline", "trail_text", "web_title", "section_name", "section_id", "web_url"]:
        if col not in articles.columns:
            articles[col] = ""

    if "publication_date" not in articles.columns:
        if "publication_datetime_utc" in articles.columns:
            articles["publication_date"] = pd.to_datetime(articles["publication_datetime_utc"], errors="coerce").dt.date
        else:
            articles["publication_date"] = pd.NaT
    articles["publication_date"] = pd.to_datetime(articles["publication_date"], errors="coerce")

    if "month" not in articles.columns:
        articles["month"] = articles["publication_date"].dt.to_period("M").dt.to_timestamp()
    else:
        articles["month"] = pd.to_datetime(articles["month"], errors="coerce").dt.to_period("M").dt.to_timestamp()

    if "year" not in articles.columns:
        articles["year"] = articles["month"].dt.year

    if "wordcount" not in articles.columns:
        articles["wordcount"] = np.nan
    articles["wordcount"] = pd.to_numeric(articles["wordcount"], errors="coerce")

    if "keywords" not in articles.columns:
        articles["keywords"] = [[] for _ in range(len(articles))]
    if "format_tags" not in articles.columns:
        articles["format_tags"] = [[] for _ in range(len(articles))]

    articles["keywords"] = articles["keywords"].apply(parse_list_like)
    articles["format_tags"] = articles["format_tags"].apply(parse_list_like)
    articles["headline"] = articles["headline"].fillna("").astype(str).apply(strip_html)
    articles["trail_text"] = articles["trail_text"].fillna("").astype(str).apply(strip_html)
    articles["web_title"] = articles["web_title"].fillna("").astype(str).apply(strip_html)
    articles["section_name"] = articles["section_name"].fillna("Unknown").replace("", "Unknown")
    articles["headline_trail_text"] = (articles["headline"] + " " + articles["trail_text"]).str.strip()
    articles = articles.drop_duplicates(subset=["id"]).reset_index(drop=True)
    return articles


def has_ai_keyword(keywords: list[str]) -> bool:
    kw_text = " | ".join(str(k).lower() for k in keywords or [])
    return any(re.search(p, kw_text, flags=re.IGNORECASE) for p in AI_KEYWORD_PATTERNS)


def has_ai_text_signal(text: str) -> bool:
    raw = text or ""
    lower = raw.lower()
    if any(re.search(p, lower, flags=re.IGNORECASE) for p in AI_TEXT_DIRECT_PATTERNS):
        return True
    # Standalone AI is allowed only with context words to avoid overinclusive matching.
    if re.search(r"\bai\b", lower, flags=re.IGNORECASE):
        return any(cw in lower for cw in AI_CONTEXT_WORDS_FOR_STANDALONE_AI)
    # Also catch A.I. with context.
    if re.search(r"\ba\.i\.\b", lower, flags=re.IGNORECASE):
        return any(cw in lower for cw in AI_CONTEXT_WORDS_FOR_STANDALONE_AI)
    return False


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def add_final_features(articles: pd.DataFrame) -> pd.DataFrame:
    articles = articles.copy()
    articles["ai_keyword_hit"] = articles["keywords"].apply(has_ai_keyword)
    articles["ai_text_hit"] = articles["headline_trail_text"].apply(has_ai_text_signal)
    articles["ai_strict"] = articles["ai_keyword_hit"] | articles["ai_text_hit"]

    strict = articles[articles["ai_strict"]].copy().reset_index(drop=True)
    strict["section_name"] = strict["section_name"].fillna("Unknown").replace("", "Unknown")
    strict["section_name_lower"] = strict["section_name"].str.lower()
    strict["tech_business_frame"] = strict["section_name_lower"].isin(["technology", "business"]).astype(int)
    strict["frame_label"] = np.where(strict["tech_business_frame"] == 1, "technology_business", "broader_public_issue")

    strict["publication_date"] = pd.to_datetime(strict["publication_date"], errors="coerce")
    strict["month"] = pd.to_datetime(strict["month"], errors="coerce").dt.to_period("M").dt.to_timestamp()
    strict["year"] = strict["month"].dt.year.astype("Int64")
    strict["month_num"] = strict["month"].dt.month.astype("Int64")
    strict["post_chatgpt_period"] = (strict["publication_date"] >= pd.Timestamp("2022-11-30")).astype(int)

    strict["headline_word_count"] = strict["headline"].apply(count_words)
    strict["trail_word_count"] = strict["trail_text"].apply(count_words)
    strict["text_word_count"] = strict["headline_trail_text"].apply(count_words)
    strict["n_keyword_tags"] = strict["keywords"].apply(lambda x: len(x or []))
    strict["n_format_tags"] = strict["format_tags"].apply(lambda x: len(x or []))

    text_lower = strict["headline_trail_text"].fillna("").str.lower()
    for col, pat in KEYWORD_FLAG_PATTERNS.items():
        strict[col] = text_lower.str.contains(pat, regex=True).astype(int)

    format_text = strict["format_tags"].apply(lambda xs: " | ".join(str(x).lower() for x in xs or []))
    for col, pat in FORMAT_FLAGS.items():
        strict[col] = format_text.str.contains(pat, regex=True).astype(int)

    # Predictor columns for Day 2. section_name is intentionally not in this list to avoid leakage.
    feature_cols = [
        "year", "month_num", "post_chatgpt_period", "wordcount",
        "headline_word_count", "trail_word_count", "text_word_count",
        "n_keyword_tags", "n_format_tags",
        *KEYWORD_FLAG_PATTERNS.keys(),
        *FORMAT_FLAGS.keys(),
    ]
    strict["day2_model_feature_columns"] = ",".join(feature_cols)
    return strict


def save_csv_with_lists(df: pd.DataFrame, path: Path) -> None:
    out = df.copy()
    for col in ["keywords", "format_tags"]:
        if col in out.columns:
            out[col] = out[col].apply(lambda xs: "; ".join(str(x) for x in (xs or [])) if isinstance(xs, list) else xs)
    out.to_csv(path, index=False)


def full_months_from_data(articles: pd.DataFrame) -> pd.DataFrame:
    min_month = pd.to_datetime(articles["month"], errors="coerce").min()
    max_month = pd.to_datetime(articles["month"], errors="coerce").max()
    if pd.isna(min_month) or pd.isna(max_month):
        return pd.DataFrame({"month": []})
    months = pd.date_range(min_month.to_period("M").to_timestamp(), max_month.to_period("M").to_timestamp(), freq="MS")
    return pd.DataFrame({"month": months})


def make_monthly_counts(broad: pd.DataFrame, strict: pd.DataFrame) -> pd.DataFrame:
    full_months = full_months_from_data(broad)
    broad_counts = broad.groupby("month", as_index=False).agg(broad_articles=("id", "nunique"))
    strict_counts = strict.groupby("month", as_index=False).agg(strict_articles=("id", "nunique"))
    out = full_months.merge(broad_counts, on="month", how="left").merge(strict_counts, on="month", how="left")
    out[["broad_articles", "strict_articles"]] = out[["broad_articles", "strict_articles"]].fillna(0).astype(int)
    return out


def figure_monthly_counts(counts: pd.DataFrame, fig_dir: Path) -> None:
    plt.figure(figsize=(10, 4.5))
    plt.plot(counts["month"], counts["broad_articles"], marker="o", linewidth=1.4, label="Broad corpus")
    plt.plot(counts["month"], counts["strict_articles"], marker="o", linewidth=1.4, label="Strict corpus")
    plt.title("Monthly AI-related article volume: broad vs strict corpus")
    plt.xlabel("")
    plt.ylabel("Unique articles in month")
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_dir / "figure1_monthly_volume_broad_vs_strict.png", dpi=200)
    plt.close()


def figure_top_sections(strict: pd.DataFrame, fig_dir: Path) -> pd.DataFrame:
    top_sections = strict["section_name"].fillna("Unknown").value_counts().reset_index()
    top_sections.columns = ["section_name", "n"]
    top_sections["share"] = top_sections["n"] / top_sections["n"].sum()
    plot_sections = top_sections.head(12).iloc[::-1]
    plt.figure(figsize=(9, 5.5))
    plt.barh(plot_sections["section_name"], plot_sections["n"])
    plt.title("Most common sections in strict AI corpus")
    plt.xlabel("Number of articles")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(fig_dir / "figure2_top_sections_strict.png", dpi=200)
    plt.close()
    return top_sections


def figure_section_share(strict: pd.DataFrame, top_sections: pd.DataFrame, fig_dir: Path) -> None:
    section_month = (
        strict.dropna(subset=["month", "section_name"])
        .groupby(["month", "section_name"])
        .size()
        .reset_index(name="n")
    )
    if section_month.empty:
        return
    section_month["share"] = section_month.groupby("month")["n"].transform(lambda s: s / s.sum())
    top_names = top_sections["section_name"].head(6).tolist()
    section_month_top = section_month[section_month["section_name"].isin(top_names)].copy()
    plt.figure(figsize=(10, 5.2))
    for sec in top_names:
        tmp = section_month_top[section_month_top["section_name"] == sec]
        plt.plot(tmp["month"], tmp["share"], marker="o", linewidth=1.4, label=sec)
    plt.title("Section share over time in strict AI corpus")
    plt.xlabel("")
    plt.ylabel("Share of monthly strict-corpus articles")
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_dir / "figure3_section_share_over_time_strict.png", dpi=200)
    plt.close()


def make_manual_audit_sample(articles: pd.DataFrame, strict: pd.DataFrame, audit_n: int, seed: int) -> pd.DataFrame:
    strict_ids = set(strict["id"].dropna().astype(str))
    broad = articles.copy()
    broad["id_str"] = broad["id"].astype(str)
    broad["corpus_group"] = np.where(broad["id_str"].isin(strict_ids), "strict", "broad_not_strict")

    sample_frames = []
    rng = np.random.default_rng(seed)
    for group in ["strict", "broad_not_strict"]:
        dfg = broad[broad["corpus_group"] == group].copy()
        n = min(audit_n, len(dfg))
        if n == 0:
            continue
        idx = rng.choice(dfg.index.to_numpy(), size=n, replace=False)
        sample_frames.append(dfg.loc[idx].copy())
    audit = pd.concat(sample_frames, ignore_index=True) if sample_frames else pd.DataFrame()
    keep_cols = [
        "corpus_group", "id", "publication_date", "month", "section_name", "web_title",
        "headline", "trail_text", "web_url", "ai_keyword_hit", "ai_text_hit",
    ]
    for col in keep_cols:
        if col not in audit.columns:
            audit[col] = ""
    audit = audit[keep_cols].copy()
    audit.insert(0, "audit_id", range(1, len(audit) + 1))
    audit["reviewer_label"] = ""
    audit["reviewer_notes"] = ""
    audit["allowed_labels"] = "core_ai_article | incidental_ai_mention | unclear"
    return audit


def dataset_summary(broad: pd.DataFrame, strict: pd.DataFrame) -> pd.DataFrame:
    broad_n = int(broad["id"].nunique())
    strict_n = int(strict["id"].nunique())
    return pd.DataFrame({
        "metric": [
            "broad_unique_articles",
            "strict_unique_articles",
            "strict_share_of_broad",
            "months",
            "technology_business_articles_in_strict",
            "broader_public_issue_articles_in_strict",
        ],
        "value": [
            broad_n,
            strict_n,
            strict_n / broad_n if broad_n else np.nan,
            broad["month"].nunique(),
            int(strict["tech_business_frame"].sum()) if "tech_business_frame" in strict.columns else np.nan,
            int((strict["tech_business_frame"] == 0).sum()) if "tech_business_frame" in strict.columns else np.nan,
        ],
    })


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Day 1 final project data, features, audit sample, and figures.")
    parser.add_argument("--data-dir", default="data", help="Directory for data files.")
    parser.add_argument("--fig-dir", default="figures", help="Directory for figures.")
    parser.add_argument("--outputs-dir", default="outputs", help="Directory for output summaries.")
    parser.add_argument("--from-date", default="2021-01-01")
    parser.add_argument("--to-date", default="2025-12-31")
    parser.add_argument("--search-terms", default="||".join(DEFAULT_SEARCH_TERMS), help="Search terms separated by ||")
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--order-by", default="newest")
    parser.add_argument("--sleep-s", type=float, default=1.05)
    parser.add_argument("--audit-n", type=int, default=100)
    parser.add_argument("--seed", type=int, default=370)
    parser.add_argument("--refresh", action="store_true", help="Refresh cached API files.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--fetch-if-missing", action="store_true", help="Fetch from Guardian API if no local data is found.")
    group.add_argument("--no-fetch-if-missing", action="store_true", help="Do not fetch from API if no local data is found.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data_dir = Path(args.data_dir)
    fig_dir = Path(args.fig_dir)
    outputs_dir = Path(args.outputs_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    articles = load_existing_data(data_dir)
    if articles is None:
        if args.no_fetch_if_missing or not args.fetch_if_missing:
            print(
                "No existing data file found in data/. Place guardian_articles_full.pkl/csv there, "
                "or rerun with --fetch-if-missing after setting GUARDIAN_API_KEY.",
                file=sys.stderr,
            )
            return 2
        articles = fetch_all_articles(args)

    articles = normalize_articles(articles)
    strict = add_final_features(articles)

    if strict.empty:
        print("Strict corpus is empty. Check the input data and strict AI rules.", file=sys.stderr)
        return 3

    save_csv_with_lists(articles, data_dir / "guardian_ai_articles_broad_final.csv")
    articles.to_pickle(data_dir / "guardian_ai_articles_broad_final.pkl")
    save_csv_with_lists(strict, data_dir / "guardian_ai_articles_strict_final.csv")
    save_csv_with_lists(strict, data_dir / "guardian_ai_articles_final.csv")

    counts = make_monthly_counts(articles, strict)
    counts.to_csv(outputs_dir / "day1_monthly_counts.csv", index=False)
    figure_monthly_counts(counts, fig_dir)

    top_sections = figure_top_sections(strict, fig_dir)
    top_sections.to_csv(outputs_dir / "day1_top_sections_strict.csv", index=False)
    figure_section_share(strict, top_sections, fig_dir)

    audit = make_manual_audit_sample(articles, strict, args.audit_n, args.seed)
    audit.to_csv(data_dir / "manual_audit_sample.csv", index=False)

    summary = dataset_summary(articles, strict)
    summary.to_csv(outputs_dir / "day1_dataset_summary.csv", index=False)

    print("\nDay 1 build complete.")
    print(summary.to_string(index=False))
    print("\nCreated:")
    for p in [
        data_dir / "guardian_ai_articles_broad_final.csv",
        data_dir / "guardian_ai_articles_strict_final.csv",
        data_dir / "guardian_ai_articles_final.csv",
        data_dir / "manual_audit_sample.csv",
        outputs_dir / "day1_dataset_summary.csv",
        outputs_dir / "day1_monthly_counts.csv",
        outputs_dir / "day1_top_sections_strict.csv",
        fig_dir / "figure1_monthly_volume_broad_vs_strict.png",
        fig_dir / "figure2_top_sections_strict.png",
        fig_dir / "figure3_section_share_over_time_strict.png",
    ]:
        print(f"  - {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

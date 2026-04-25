#!/usr/bin/env python3
"""
Create interactive Plotly visualizations.

Outputs:
  docs/viz_monthly_volume.html
  docs/viz_section_share.html
  docs/viz_topic_prevalence.html
"""
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd
import plotly.express as px


def missing(path: Path, title: str, message: str) -> None:
    path.write_text(f"<!doctype html><html><body><h1>{title}</h1><p>{message}</p></body></html>", encoding="utf-8")


def monthly(counts_file: Path, docs: Path) -> None:
    out = docs / "viz_monthly_volume.html"
    if not counts_file.exists():
        missing(out, "Monthly volume", f"Missing {counts_file}.")
        return
    counts = pd.read_csv(counts_file)
    counts["month"] = pd.to_datetime(counts["month"], errors="coerce")
    value_vars = [c for c in ["broad_articles", "strict_articles"] if c in counts.columns]
    long = counts.melt(id_vars="month", value_vars=value_vars, var_name="corpus", value_name="article_count")
    long["corpus"] = long["corpus"].replace({"broad_articles": "Broad corpus", "strict_articles": "Strict corpus"})
    fig = px.line(long, x="month", y="article_count", color="corpus", markers=True,
                  title="Monthly AI-related Guardian article volume",
                  labels={"month": "Month", "article_count": "Unique articles", "corpus": "Corpus"})
    fig.update_layout(hovermode="x unified")
    fig.write_html(out, include_plotlyjs="cdn", full_html=True)


def section_share(strict_file: Path, docs: Path, top_sections: int) -> None:
    out = docs / "viz_section_share.html"
    if not strict_file.exists():
        missing(out, "Section share", f"Missing {strict_file}.")
        return
    df = pd.read_csv(strict_file)
    if "section_name" not in df.columns:
        missing(out, "Section share", "Missing section_name.")
        return
    if "month" in df.columns:
        df["month"] = pd.to_datetime(df["month"], errors="coerce").dt.to_period("M").dt.to_timestamp()
    else:
        df["month"] = pd.to_datetime(df["publication_date"], errors="coerce").dt.to_period("M").dt.to_timestamp()
    df["section_name"] = df["section_name"].fillna("Unknown")
    top = df["section_name"].value_counts().head(top_sections).index.tolist()
    df = df[df["section_name"].isin(top)]
    sm = df.groupby(["month", "section_name"]).size().reset_index(name="n")
    totals = df.groupby("month").size().reset_index(name="month_total")
    sm = sm.merge(totals, on="month", how="left")
    sm["share"] = sm["n"] / sm["month_total"]
    fig = px.line(sm, x="month", y="share", color="section_name", markers=True,
                  title="Section composition over time in the strict AI corpus",
                  labels={"month": "Month", "share": "Share of strict-corpus articles", "section_name": "Section"})
    fig.update_layout(hovermode="x unified")
    fig.write_html(out, include_plotlyjs="cdn", full_html=True)



def clean_topic_label(label: str) -> str:
    if pd.isna(label):
        return "Unknown topic"

    label = str(label).strip()
    lower = label.lower()

    direct_map = {
        "AI tools and ChatGPT": "AI tools & ChatGPT",
        "Topic 2: chatgpt, images, just": "ChatGPT & image generation",
        "Topic 3: openai, musk, media": "OpenAI, Musk & media",
        "Topic 4: intelligence, artificial, artificial intelligence": "General AI discourse",
        "Topic 5: nvidia, company, openai": "AI business competition",
        "Education and work": "Education & work",
    }

    if label in direct_map:
        return direct_map[label]

    if "nvidia" in lower or "company" in lower or "business" in lower:
        return "AI business competition"
    if "education" in lower or "school" in lower or "student" in lower or "work" in lower:
        return "Education & work"
    if "openai" in lower and ("musk" in lower or "media" in lower):
        return "OpenAI, Musk & media"
    if "chatgpt" in lower and ("image" in lower or "images" in lower):
        return "ChatGPT & image generation"
    if "chatgpt" in lower:
        return "AI tools & ChatGPT"
    if "intelligence" in lower and "artificial" in lower:
        return "General AI discourse"
    if "copyright" in lower or "artist" in lower or "music" in lower or "film" in lower:
        return "Creative work & copyright"
    if "regulation" in lower or "government" in lower or "law" in lower or "policy" in lower:
        return "Regulation & policy"
    if "risk" in lower or "misinformation" in lower or "election" in lower:
        return "Risk & misinformation"

    if len(label) > 36:
        return label[:33].rstrip() + "..."

    return label


def topics(topic_file: Path, docs: Path) -> None:
    out = docs / "viz_topic_prevalence.html"

    if not topic_file.exists():
        missing(out, "Topic prevalence", f"Missing {topic_file}. Run topic modeling first.")
        return

    df = pd.read_csv(topic_file)

    required_cols = {"month", "topic_share", "topic_label"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        missing(out, "Topic prevalence", f"Missing columns: {', '.join(sorted(missing_cols))}.")
        return

    df["month"] = pd.to_datetime(df["month"], errors="coerce")
    df = df.dropna(subset=["month", "topic_share", "topic_label"]).copy()

    df["topic_label_short"] = df["topic_label"].apply(clean_topic_label)

    df = df.sort_values(["topic_label_short", "month"]).copy()
    df["topic_share_smoothed"] = (
        df.groupby("topic_label_short")["topic_share"]
        .transform(lambda s: s.rolling(window=3, min_periods=1).mean())
    )

    topic_order = (
        df.groupby("topic_label_short")["topic_share_smoothed"]
        .mean()
        .sort_values(ascending=False)
        .index
        .tolist()
    )

    fig = px.line(
        df,
        x="month",
        y="topic_share_smoothed",
        color="topic_label_short",
        category_orders={"topic_label_short": topic_order},
        title="LDA topic prevalence over time",
        labels={
            "month": "Month",
            "topic_share_smoothed": "Average topic share, 3-month rolling mean",
            "topic_label_short": "Topic",
        },
        hover_data={
            "topic_label": True,
            "topic_label_short": False,
            "topic_share": ":.3f",
            "topic_share_smoothed": ":.3f",
            "month": "|%Y-%m",
        },
    )

    fig.update_traces(
        mode="lines",
        line=dict(width=3),
        opacity=0.9,
    )

    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        autosize=True,
        height=700,
        margin=dict(l=80, r=40, t=80, b=155),
        legend=dict(
            title="Topic",
            orientation="h",
            yanchor="top",
            y=-0.13,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
        ),
    )

    fig.update_xaxes(title_text="Month", title_standoff=22, ticklabelstandoff=8)
    fig.update_yaxes(
        title_text="Average topic share",
        tickformat=".0%",
        range=[0, 0.40],
        dtick=0.05,
        title_standoff=22,
        automargin=True
    )

    fig.write_html(
        out,
        include_plotlyjs="cdn",
        full_html=True,
        config={"responsive": True},
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--strict-file", default="data/guardian_ai_articles_final.csv")
    p.add_argument("--monthly-counts", default="outputs/day1_monthly_counts.csv")
    p.add_argument("--topic-prevalence", default="outputs/topic_prevalence_by_month.csv")
    p.add_argument("--docs-dir", default="docs")
    p.add_argument("--top-sections", type=int, default=8)
    args = p.parse_args()

    docs = Path(args.docs_dir)
    docs.mkdir(exist_ok=True, parents=True)
    monthly(Path(args.monthly_counts), docs)
    section_share(Path(args.strict_file), docs, args.top_sections)
    topics(Path(args.topic_prevalence), docs)

    print("Interactive visualization files created:")
    for pth in ["viz_monthly_volume.html", "viz_section_share.html", "viz_topic_prevalence.html"]:
        print(f"  - {docs / pth}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

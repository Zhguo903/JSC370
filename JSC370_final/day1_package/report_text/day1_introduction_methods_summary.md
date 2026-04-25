# Day 1 Written Material for Final Report

## Proposed final title

**From Technology Story to Public Issue: Modeling The Guardian's AI Coverage, 2021–2025**

## Introduction draft

Artificial intelligence has become more than a technical innovation. It is now a public issue connected to labor markets, education, copyright, regulation, elections, business competition, misinformation, and cultural production. News coverage matters because it shapes how readers encounter both the opportunities and risks of AI. The Guardian is a useful source for studying this shift because its AI-related stories appear across multiple sections, including Technology, Business, Opinion, World news, Politics, Culture, and Life and style, rather than only in technology reporting.

This project builds on the midterm analysis of AI-related Guardian coverage from 2021 to 2025. The midterm project constructed a broad search corpus from five AI-related terms and then created a stricter corpus using AI-related keyword tags and headline/trail-text pattern matching. The broad corpus captured the overall AI-related search environment, while the strict corpus served as a higher-precision approximation of core AI coverage. The final project extends that work by improving the motivation, clarifying the search-term strategy, validating the strict corpus through a manual audit, and building predictive and topic models on the cleaner AI-related subset.

The main research question is:

> How did The Guardian's AI-related coverage change between 2021 and 2025, and can article text and metadata predict whether an AI-related article is framed as a technology/business issue or as a broader public issue?

The project focuses on four hypotheses:

1. AI-related Guardian coverage increased substantially after the public diffusion of generative AI tools.
2. AI coverage is not limited to the Technology section; it also appears in news, opinion, business, politics, education, culture, and lifestyle coverage.
3. Textual features such as “ChatGPT,” “OpenAI,” “large language model,” “regulation,” “jobs,” “copyright,” “education,” and “risk” help distinguish technology/business framing from broader public-issue framing.
4. Topic modeling will reveal multiple themes in AI coverage, including business competition, regulation, creative industries, education, labor, and AI risk.

## Search-term justification draft

The search-term strategy is designed to balance recall and precision. Instead of relying on a single term such as “AI,” which can be too broad or ambiguous, the project uses terms from three conceptual groups.

| Term group | Search terms or strict signals | Justification |
|---|---|---|
| General concept terms | `artificial intelligence`; strict text signal for standalone `AI` when it appears with relevant AI context words | Captures general AI coverage while limiting false positives from the short acronym `AI`. |
| Technical and subfield terms | `machine learning`, `deep learning`, `neural network`, `large language model`, `LLM` | Captures articles that discuss AI through technical vocabulary rather than the general phrase “artificial intelligence.” |
| Public-facing generative AI terms | `generative AI`, `ChatGPT`, `OpenAI`, `Google Gemini`, `Google DeepMind`, `Claude AI`, `DALL-E`, `Midjourney` | Captures the post-2022 public-facing generative AI discussion and platform-specific coverage. |

The broad corpus prioritizes recall by collecting articles from a union of AI-related Guardian API searches. The strict corpus prioritizes precision by keeping articles that have explicit AI-related Guardian keyword tags or clear AI signals in the headline and trail text. This broad-versus-strict design allows the analysis to distinguish the larger AI-related search environment from a more conservative set of likely core AI articles.

## Methods draft: data and corpus construction

The data come from the Guardian Content API `/search` endpoint. Articles are collected month by month from January 2021 through December 2025. For each query and month, all available API result pages are requested. Returned articles are then deduplicated by Guardian article ID, so an article that matches multiple AI-related queries appears only once in the broad corpus.

For each article, the project extracts Guardian article ID, publication date, section, headline, trail text, keyword tags, editorial-format tags, byline, URL, and word count. HTML is removed from trail text, publication timestamps are converted to calendar months, and keyword and editorial-format tags are stored for later feature engineering.

The strict corpus is defined using two types of evidence. First, articles are kept if their Guardian keyword tags include AI-related labels such as AI, artificial intelligence, machine learning, deep learning, large language models, ChatGPT, OpenAI, or generative AI. Second, articles are kept if their headline or trail text contains clear AI-related phrases such as “artificial intelligence,” “machine learning,” “deep learning,” “generative AI,” “large language model,” “LLM,” “ChatGPT,” “OpenAI,” “Gemini,” “Claude,” “DALL-E,” or “Midjourney.” Because the standalone acronym “AI” can be ambiguous, the script only treats it as a strict text signal when it appears with additional AI-context words such as model, algorithm, chatbot, generative, automation, regulation, risk, tools, or machine learning.

## Manual audit draft

To evaluate whether the strict corpus improves precision relative to the broad search corpus, I conduct a small manual audit. I randomly sample 100 articles from the strict corpus and 100 articles from the broad-but-not-strict corpus. For each sampled article, I read the headline and trail text and assign one of three labels: `core_ai_article`, `incidental_ai_mention`, or `unclear`. The main audit statistic is the share of sampled articles labeled as `core_ai_article` in each group. If the strict corpus has a substantially higher core-AI share than the broad-but-not-strict group, this supports using the strict corpus for final modeling.

## Target variable and feature engineering draft

The final predictive task is to classify whether an AI-related article is framed as a technology/business story or as a broader public-issue story. The binary outcome is:

```text
tech_business_frame = 1 if section_name is Technology or Business
tech_business_frame = 0 otherwise
```

This target is useful because it directly tests whether AI coverage remains primarily technical/commercial or whether it is distributed across broader public-facing sections. To avoid data leakage, `section_name` itself is not used as a predictor in the final model.

The Day 1 feature-engineering script creates text and metadata features that can be used in Day 2 modeling. These include year, month, post-ChatGPT period, word count, headline length, trail-text length, combined text length, keyword flags for major AI themes, number of Guardian keyword tags, number of editorial-format tags, and editorial-format indicators such as News, Comment, Features, Reviews, Analysis, Explainers, and Interviews. The combined headline and trail text will later be converted into TF-IDF features for logistic regression, Random Forest, and XGBoost models.

## Day 1 result interpretation template

After running the Day 1 script, write one paragraph for each of the first three figures:

1. **Monthly volume:** Compare broad and strict article counts over time. Emphasize that the broad corpus measures the larger AI-related search environment, while the strict corpus is used for cleaner final analysis.
2. **Top sections:** Discuss which sections dominate the strict corpus. If Technology and Business are not the only large sections, use this as evidence that AI is covered as a broader public issue.
3. **Section share over time:** Discuss whether section composition changes over time. Avoid making causal claims; describe the plot as evidence of changing framing or changing editorial attention.

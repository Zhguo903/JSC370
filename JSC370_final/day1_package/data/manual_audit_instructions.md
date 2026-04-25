# Manual Audit Instructions

The purpose of the manual audit is to check whether the rule-based strict corpus is more precise than the broad search corpus.

The script samples two groups:

1. `strict`: articles kept by the final strict AI rules
2. `broad_not_strict`: articles returned by broad search terms but not kept by strict AI rules

For each sampled article, read the headline and trail text. Then fill the `reviewer_label` column with one of the following labels.

## Labels

### `core_ai_article`
Use this label when AI, machine learning, large language models, ChatGPT, OpenAI, automation, AI regulation, AI risk, AI tools, or AI impact is a main topic of the article.

### `incidental_ai_mention`
Use this label when an AI-related term appears, but the article is mainly about another topic.

### `unclear`
Use this label when the headline and trail text do not give enough information to decide.

## Notes

- Do not use the section name alone to decide the label.
- If AI is clearly the main issue, choose `core_ai_article` even if the article is in Opinion, Culture, Education, Business, or Politics instead of Technology.
- If the article only mentions AI as one example among many unrelated issues, choose `incidental_ai_mention`.

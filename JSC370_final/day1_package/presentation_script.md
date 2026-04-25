# 5-Minute Presentation Script

## 0:00–0:40 Motivation

My project studies how *The Guardian's* AI-related coverage changed from 2021 to 2025. The motivation is that AI is not only a technical topic. It is connected to labor, education, copyright, regulation, business competition, politics, misinformation, and culture. News coverage matters because it shapes how the public understands these risks and opportunities.

## 0:40–1:15 Data and corpus construction

I use the Guardian Content API to collect articles month by month from 2021 through 2025. I construct two corpora. The broad corpus is the union of AI-related search terms. The strict corpus keeps only articles with stronger AI evidence in keyword tags, headlines, or trail text. The final expanded search strategy produced 40,232 broad-corpus articles and 3,120 strict-corpus articles.

## 1:15–2:00 Manual audit and descriptive results

Because a search-based corpus can be overinclusive, I manually audited 100 strict-corpus articles and 100 broad-but-not-strict articles. The audit showed that 80% of sampled strict-corpus articles were core AI articles, compared with only 1% of sampled broad-but-not-strict articles. This supports using the strict corpus for modeling. The descriptive figures show that AI coverage increased over time and appears across many sections, not only Technology.

## 2:00–3:15 Classification modeling

The main prediction task is to classify whether a strict-corpus AI article is framed as a Technology/Business story or as a broader public-issue story. I use headline and trail-text TF-IDF features, keyword indicators, time variables, word count, tag counts, editorial-format indicators, and sentiment. I exclude section name from the predictors because the target is derived from section membership. I compare a majority baseline, logistic regression, Random Forest, and XGBoost when available.

## 3:15–4:15 Results and topic modeling

The model-performance plot compares the models using accuracy, precision, recall, F1, and ROC-AUC. The confusion matrix shows where the selected model makes errors. The variable-importance plot shows which text and metadata features are most useful for distinguishing the two frames. I also use LDA topic modeling to identify themes in AI coverage and show how topic prevalence changes over time.

## 4:15–5:00 Conclusion

The main conclusion is that AI coverage in *The Guardian* grew and diversified between 2021 and 2025. The strict corpus and manual audit show that careful corpus construction matters. The classification and topic models suggest that AI coverage is not only a technology or business issue but also a broader public issue involving politics, education, copyright, labor, creativity, and risk.

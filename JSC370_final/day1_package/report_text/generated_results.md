## Generated results summary

The expanded final search strategy produced **40,232** broad-corpus articles and **3,120** strict-corpus articles across **60** months. The strict corpus represented **7.76%** of the broad corpus. Within the strict corpus, **1,457** articles were labeled as Technology/Business frame articles and **1,663** articles were labeled as broader public-issue frame articles.

The manual audit found that 80.0% of sampled strict-corpus articles were core AI articles, compared with 1.0% of sampled broad-but-not-strict articles. This supports using the strict corpus as the main dataset for modeling.

The best-performing model by test-set F1 was **XGBoost**, with accuracy 0.764, F1 0.750, and ROC-AUC 0.847.

The LDA model separated the strict corpus into themes such as AI tools and ChatGPT; Topic 2: chatgpt, images, just; Topic 3: openai, musk, media; Topic 4: intelligence, artificial, artificial intelligence; Topic 5: nvidia, company, openai; Education and work.

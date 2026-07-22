# LLM as Judge
LLM-as-judge uses a language model to grade answers instead of exact string matching. The judge
receives the question, an expected answer, and a candidate answer, then returns a score. It
handles paraphrases and wording differences that would fail a keyword match, which makes it a
practical way to score a retrieval-augmented system on a test set.

# Top-k Retrieval
Top-k retrieval returns the k most similar documents to the query. A small k keeps the prompt
short, cheap, and focused but may miss useful context. A large k improves recall but adds tokens
and noise that can distract the model. The right k is a balance tuned against the document set
and question style; this project defaults to k equal to three.

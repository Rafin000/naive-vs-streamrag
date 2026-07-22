# Tokens and Cost
Language models bill by tokens, where a token is roughly four characters of English text.
Cost has two parts: input (prompt) tokens and output (completion) tokens, usually priced
differently. Larger retrieved context raises the input token count and therefore the cost, so
retrieving fewer, more relevant chunks keeps answers both cheaper and sharper.

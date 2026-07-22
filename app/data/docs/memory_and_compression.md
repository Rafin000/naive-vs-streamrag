# Memory and Compression
An agent's memory is the list of messages resent to the model on each turn so it remembers the
conversation. Because every message costs tokens, memory cannot grow forever. Compression
summarizes the oldest turns into a short note and keeps only the most recent messages verbatim,
which preserves the important facts while staying inside the token budget.

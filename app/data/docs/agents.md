# Agent Harness
An agent harness adds tools, memory, and context management around a language model. Tools
let the model call functions such as a calculator. Memory is the running message list resent
each turn. When memory grows past a token budget, older turns are summarized to compress them.

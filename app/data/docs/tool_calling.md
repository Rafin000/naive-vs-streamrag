# Tool Calling
Tool calling lets a language model invoke a function instead of guessing an answer. The model
is given tool descriptions and, when useful, returns a structured call with arguments. The
application runs the function and returns the result to the model. This project exposes a
calculator tool so arithmetic is computed exactly rather than approximated by the model.

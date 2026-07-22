# Chunking
Chunking splits long documents into smaller passages before embedding them. Chunks that are too
large dilute relevance and waste context tokens, while chunks that are too small lose the
surrounding meaning. A common approach is to split on paragraphs or a fixed token size with a
small overlap so that ideas spanning a boundary are not cut in half.

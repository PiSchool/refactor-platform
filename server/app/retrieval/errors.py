"""Retrieval-specific failures that must fail S2 closed."""


class RetrievalUnavailable(RuntimeError):
    """A mandatory S2 component could not produce a valid result."""


class RetrievalCancelled(RetrievalUnavailable):
    """The operator stopped or skipped a task during retrieval preparation."""
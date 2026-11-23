"""
Fluent builder for PromQL queries.
"""

from __future__ import annotations


class PromQBuilder:
    """Builds PromQL query strings via method chaining."""

    def __init__(self) -> None:
        self._query: str = ""

    @property
    def query(self) -> str:
        return self._query

    def metric(self, metric_name: str, **labels: str) -> PromQBuilder:
        """Start the query with metric_name and regex label matchers."""
        self._query = f"""{metric_name}{{{", ".join([f'{k}=~"{v}"' for k, v in labels.items()])}}}"""
        return self

    def sum_by(self, *labels: str) -> PromQBuilder:
        """Wrap the current query in sum by (...)."""
        self._query = f"sum by ({', '.join(labels)}) ({self._query})"
        return self

    def group_by(self, *labels: str) -> PromQBuilder:
        """Wrap the current query in group by (...)."""
        self._query = f"group by ({', '.join(labels)}) ({self._query})"
        return self

    def op(
        self,
        operator: str,
        other: PromQBuilder,
        on: list[str],
        grouping_side: str,
        grouping_labels: list[str],
    ) -> PromQBuilder:
        """Combine the current query with another using operator and vector-matching modifiers."""
        modifiers = []
        if on:
            modifiers.append(f"on({', '.join(on)})")
        if grouping_side:
            side_func = f"group_{grouping_side}"
            modifiers.append(f"{side_func}({', '.join(grouping_labels)})")
        modifier_str = " ".join(modifiers)
        self._query = f"{self._query} {operator} {modifier_str} ({other.query})"
        return self

    def build(self) -> str:
        """Return the constructed PromQL query string."""
        return self._query

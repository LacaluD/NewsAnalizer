"""Shared data contracts for cross-layer pipeline communication."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PipelineResult:
    """Represent a normalized operation result in the pipeline."""

    success: bool
    text: str | None = None
    tag: str | None = None
    error: str | None = None

    @classmethod
    def ok(cls, text: str, tag: str | None = None) -> PipelineResult:
        """Create a successful result."""
        return cls(success=True, text=text, tag=tag, error=None)

    @classmethod
    def fail(cls, error: str) -> PipelineResult:
        """Create a failed result."""
        return cls(success=False, text=None, tag=None, error=error)

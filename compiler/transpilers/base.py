# Copyright (C) 2026 Tendril Authors
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Base Transpiler Interface.

Defines the abstract contract and serialization hooks for converting
Tendril-IR instances into target diagramming DSLs.
"""

from abc import ABC, abstractmethod
import re
from core.models.ir import TendrilIR


class BaseTranspiler(ABC):
    """Abstract base class for all deterministic diagram transpilers."""

    @property
    @abstractmethod
    def target_name(self) -> str:
        """Name of the target DSL (e.g., 'mermaid', 'd2', 'plantuml')."""
        ...

    @abstractmethod
    def transpile(self, ir: TendrilIR) -> str:
        """Converts validated Tendril-IR into the target DSL string representation.

        Args:
            ir: Strictly-typed, validated TendrilIR instance.

        Returns:
            Deterministic DSL code block ready for linter or renderer.
        """
        ...

    @staticmethod
    def sanitize_label(label: str) -> str:
        """Sanitizes text labels to prevent syntax injection and broken tokens.

        Replaces raw double quotes with escaped quotes and strips trailing newlines.
        """
        escaped = label.replace('"', '\\"').strip()
        # Remove unprintable control characters while keeping whitespace
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", escaped)
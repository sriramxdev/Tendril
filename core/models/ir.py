# Copyright (C) 2026 Tendril Authors
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tendril Intermediate Representation (Tendril-IR) Models.

Defines the strictly-typed graph topology intermediate representation
decoupled from target diagramming DSLs (Mermaid, D2, PlantUML).
"""

from enum import StrEnum
from typing import Annotated, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator


class DiagramType(StrEnum):
    """Supported diagram topologies and layout paradigms."""
    SEQUENCE_FLOW = "sequence_flow"
    STATE_MACHINE = "state_machine"
    SYSTEM_ARCHITECTURE = "system_architecture"
    ENTITY_RELATIONSHIP = "entity_relationship"


class NodeShape(StrEnum):
    """DSL-agnostic visual shape tokens."""
    RECTANGLE = "rectangle"
    ROUNDED = "rounded"
    DATABASE = "database"
    ACTOR = "actor"
    DIAMOND = "diamond"
    CLOUD = "cloud"
    QUEUE = "queue"


class EdgeSemantics(StrEnum):
    """Communication and traversal semantics across nodes."""
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    RETURN_VALUE = "return_value"
    STATE_TRANSITION = "state_transition"
    DATA_STREAM = "data_stream"


class LayoutDirection(StrEnum):
    """Spatial flow orientation."""
    TOP_TO_BOTTOM = "TD"
    BOTTOM_TO_TOP = "BT"
    LEFT_TO_RIGHT = "LR"
    RIGHT_TO_LEFT = "RL"


class IRNode(BaseModel):
    """Canonical node entity within the graph topology."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: Annotated[
        str,
        Field(
            pattern=r"^[a-zA-Z0-9_-]+$",
            description="Unique, slugified identifier containing only alphanumeric characters, underscores, or dashes.",
        ),
    ]
    label: Annotated[str, Field(min_length=1, max_length=100, description="Display label for the node.")]
    shape: NodeShape = NodeShape.ROUNDED
    subgraph_parent: str | None = Field(
        default=None,
        description="ID of the parent subgraph/cluster if nested within one.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary semantic attributes (e.g., protocol, port, technology stack).",
    )


class IREdge(BaseModel):
    """Canonical directed relationship connecting two nodes."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    source: Annotated[str, Field(description="Node ID originating the edge.")]
    target: Annotated[str, Field(description="Node ID terminating the edge.")]
    label: str | None = Field(default=None, max_length=120, description="Edge interaction or transition description.")
    semantics: EdgeSemantics = EdgeSemantics.SYNCHRONOUS
    order: int | None = Field(
        default=None,
        ge=0,
        description="Chronological sequence execution index (mandatory for SEQUENCE_FLOW).",
    )
    guard_condition: str | None = Field(
        default=None,
        max_length=80,
        description="Boolean branch predicate or conditional statement (e.g., [is_valid]).",
    )


class DiagramMetadata(BaseModel):
    """Compilation context and visual styling instructions."""
    model_config = ConfigDict(frozen=True)

    title: Annotated[str, Field(min_length=1, max_length=120)]
    description: str | None = Field(default=None, max_length=500)
    version: str = Field(default="1.0.0")
    direction: LayoutDirection = LayoutDirection.TOP_TO_BOTTOM
    theme: str = Field(default="adaptive_dark", description="Visual palette target.")


class TendrilIR(BaseModel):
    """Root Tendril Intermediate Representation container.
    
    Acts as the single source of truth for all downstream transpilers and linters.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Annotated[str, Field(default="1.0.0", description="Semver of IR specification.")]
    diagram_type: DiagramType
    metadata: DiagramMetadata
    nodes: list[IRNode] = Field(min_length=1, description="Nodes in the topology.")
    edges: list[IREdge] = Field(default_factory=list, description="Direct transitions or relations.")

    @model_validator(mode="after")
    def validate_graph_integrity(self) -> "TendrilIR":
        """Enforces referential integrity, unique keys, and archetype invariants."""
        # 1. Unique Node IDs
        node_ids: set[str] = set()
        for node in self.nodes:
            if node.id in node_ids:
                raise ValueError(f"Duplicate node ID detected: '{node.id}'")
            node_ids.add(node.id)

        # 2. Foreign Key Integrity on Edges
        for idx, edge in enumerate(self.edges):
            if edge.source not in node_ids:
                raise ValueError(
                    f"Edge[{idx}] references non-existent source node: '{edge.source}'"
                )
            if edge.target not in node_ids:
                raise ValueError(
                    f"Edge[{idx}] references non-existent target node: '{edge.target}'"
                )

        # 3. Subgraph Parent Hierarchy Validation
        for node in self.nodes:
            if node.subgraph_parent is not None:
                if node.subgraph_parent not in node_ids:
                    raise ValueError(
                        f"Node '{node.id}' references non-existent subgraph parent: '{node.subgraph_parent}'"
                    )
                if node.subgraph_parent == node.id:
                    raise ValueError(f"Node '{node.id}' cannot be its own subgraph parent.")

        # 4. Sequence Flow Ordering Strictness
        if self.diagram_type == DiagramType.SEQUENCE_FLOW:
            for idx, edge in enumerate(self.edges):
                if edge.order is None:
                    raise ValueError(
                        f"Edge[{idx}] ('{edge.source}' -> '{edge.target}') must specify 'order' for SEQUENCE_FLOW."
                    )

        return self
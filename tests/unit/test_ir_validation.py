# Copyright (C) 2026 Tendril Authors
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest
from pydantic import ValidationError
from core.models.ir import (
    DiagramMetadata,
    DiagramType,
    EdgeSemantics,
    IREdge,
    IRNode,
    NodeShape,
    TendrilIR,
)


def test_valid_tendril_ir_construction() -> None:
    """Ensure a structurally sound IR compiles without validation errors."""
    ir = TendrilIR(
        diagram_type=DiagramType.SYSTEM_ARCHITECTURE,
        metadata=DiagramMetadata(title="Microservice Ingress"),
        nodes=[
            IRNode(id="api_gateway", label="Kong Gateway", shape=NodeShape.RECTANGLE),
            IRNode(id="auth_service", label="Auth Service", shape=NodeShape.ROUNDED),
        ],
        edges=[
            IREdge(
                source="api_gateway",
                target="auth_service",
                label="Verify JWT",
                semantics=EdgeSemantics.SYNCHRONOUS,
            )
        ],
    )
    assert len(ir.nodes) == 2
    assert ir.edges[0].source == "api_gateway"


def test_missing_node_reference_raises_validation_error() -> None:
    """Ensure referential integrity catches non-existent edge targets."""
    with pytest.raises(ValidationError) as exc_info:
        TendrilIR(
            diagram_type=DiagramType.SYSTEM_ARCHITECTURE,
            metadata=DiagramMetadata(title="Invalid Topology"),
            nodes=[IRNode(id="service_a", label="Service A")],
            edges=[
                IREdge(
                    source="service_a",
                    target="ghost_service",  # Missing target
                    label="Ping",
                )
            ],
        )
    assert "references non-existent target node: 'ghost_service'" in str(exc_info.value)


def test_sequence_diagram_requires_edge_order() -> None:
    """Sequence flows must enforce explicit temporal ordering on transitions."""
    with pytest.raises(ValidationError) as exc_info:
        TendrilIR(
            diagram_type=DiagramType.SEQUENCE_FLOW,
            metadata=DiagramMetadata(title="Unordered Flow"),
            nodes=[
                IRNode(id="client", label="Client"),
                IRNode(id="server", label="Server"),
            ],
            edges=[
                IREdge(
                    source="client",
                    target="server",
                    label="GET /data",
                    order=None,  # Forbidden in sequence diagrams
                )
            ],
        )
    assert "must specify 'order' for SEQUENCE_FLOW" in str(exc_info.value)
# backend/learning/mirror_gate.py
from __future__ import annotations


def approve_mirror(candidate: dict) -> bool:
    """
    Reject aggressive configs if sim-paper divergence is high.
    """

    if candidate["confidence_penalty"] < 0.8:
        return False

    return True

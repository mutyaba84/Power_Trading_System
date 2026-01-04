from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

from backend.utils.logger import get_logger
from backend.utils.paths import storage_root
from backend.utils.persistence import append_jsonl, ai_core_read_only

logger = get_logger("KnowledgeGraph")


@dataclass
class KnowledgeGraph:
    """
    Runtime-safe knowledge graph (no pickle).
    - In-memory map
    - Optional append-only JSONL journal
    - Respects AI_CORE_READ_ONLY
    """

    root_dir: Path = field(default_factory=lambda: storage_root() / "ai_core")
    journal_name: str = "knowledge_events.jsonl"

    def __post_init__(self) -> None:
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.journal_path = self.root_dir / self.journal_name
        self.graph: Dict[str, Any] = {}
        logger.info("KnowledgeGraph initialized (runtime-safe).")

    def add(self, key: str, value: Any) -> None:
        self.graph[key] = value
        self._journal("add", {"key": key, "value": value})

    def get(self, key: str, default: Any = None) -> Any:
        return self.graph.get(key, default)

    def snapshot(self) -> Dict[str, Any]:
        return dict(self.graph)

    def observe_trade(self, record: Dict[str, Any]) -> None:
        self._journal("trade", record)

    def _journal(self, event_type: str, payload: Dict[str, Any]) -> None:
        if ai_core_read_only():
            return
        try:
            append_jsonl(self.journal_path, {"event": event_type, "payload": payload, "ts": time.time()})
        except Exception as e:
            logger.warning(f"KnowledgeGraph journal failed (ok): {e}")

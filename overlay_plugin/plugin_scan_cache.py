"""In-memory cache for plugin scan status results."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Mapping, Optional


@dataclass
class PluginScanCache:
    """Stores casefolded plugin-name -> status tokens from the latest scan."""

    statuses: Dict[str, str] = field(default_factory=dict)
    updated_at: Optional[float] = None

    def update(self, statuses: Mapping[str, str]) -> None:
        self.statuses = {
            str(name).strip().casefold(): str(status).strip().lower()
            for name, status in statuses.items()
            if str(name or "").strip()
        }
        self.updated_at = time.time()

    def snapshot(self) -> Dict[str, str]:
        return dict(self.statuses)

    def empty(self) -> bool:
        return not self.statuses

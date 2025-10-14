"""Simplified Hyperledger Fabric facade for demo purposes.

The real Nexus project would integrate with a Fabric network to track the
upload/download totals and uptime rewards of each participant. Building a
full Fabric network is outside the scope of this demo so instead we create a
small in-memory representation with the same shape that a Fabric client
library might expose.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class LedgerRecord:
    username: str
    upload: int = 0
    download: int = 0
    wealth: int = 0


class LedgerClient:
    """Interface describing the operations the backend expects."""

    def ensure_identity(self, username: str) -> str:
        raise NotImplementedError

    def get_balance(self, username: str) -> Optional[Dict[str, int]]:
        raise NotImplementedError

    def reward_for_uptime(self, username: str) -> Optional[Dict[str, int]]:
        raise NotImplementedError


@dataclass
class InMemoryLedger(LedgerClient):
    """Very small in-memory mock that simulates Fabric chaincode calls."""

    records: Dict[str, LedgerRecord] = field(default_factory=dict)

    def ensure_identity(self, username: str) -> str:
        record = self.records.get(username)
        if record is None:
            record = LedgerRecord(username=username)
            self.records[username] = record
        return f"fabric-identity::{username}"

    def get_balance(self, username: str) -> Optional[Dict[str, int]]:
        record = self.records.get(username)
        if record is None:
            return None
        return {
            "upload": record.upload,
            "download": record.download,
            "wealth": record.wealth,
        }

    def reward_for_uptime(self, username: str) -> Optional[Dict[str, int]]:
        record = self.records.get(username)
        if record is None:
            return None
        record.wealth += 10
        record.upload += 5
        return self.get_balance(username)

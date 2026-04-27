from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
import json
import re
import time
from pathlib import Path
from typing import Any

from .config import ChatMemoryConfig


@dataclass(slots=True)
class MemoryEntry:
    created_at: str
    user: str
    assistant: str

    def as_search_text(self) -> str:
        return f"{self.user}\n{self.assistant}".strip()

    def to_dict(self) -> dict[str, str]:
        return {
            "created_at": self.created_at,
            "user": self.user,
            "assistant": self.assistant,
        }


class ChatMemoryStore:
    def __init__(self, config: ChatMemoryConfig) -> None:
        self.config = config
        self.path = config.path

    def restore_recent(self) -> list[dict[str, str]]:
        if not self.config.enabled:
            return []
        entries = self._load_entries()
        recent = entries[-self.config.recent_turns_after_compress :]
        messages: list[dict[str, str]] = []
        for entry in recent:
            messages.append({"role": "user", "content": entry.user})
            messages.append({"role": "assistant", "content": entry.assistant})
        return messages

    def build_context(self, query: str) -> str:
        if not self.config.enabled:
            return ""
        data = self._load_data()
        parts: list[str] = []
        summary = str(data.get("summary") or "").strip()
        if summary:
            parts.append("长期记忆摘要:\n" + summary)

        matches = self.search(query, limit=self.config.retrieval_limit)
        if matches:
            rendered = []
            for index, entry in enumerate(matches, start=1):
                rendered.append(
                    f"{index}. 用户: {entry.user}\n   菲比: {entry.assistant}"
                )
            parts.append("和当前问题可能相关的旧对话:\n" + "\n".join(rendered))

        return "\n\n".join(parts).strip()

    def append_exchange(
        self,
        user_message: str,
        assistant_reply: str,
        summarizer: Callable[[str, list[MemoryEntry]], str],
    ) -> None:
        if not self.config.enabled:
            return
        data = self._load_data()
        entries = self._decode_entries(data.get("entries"))
        entries.append(
            MemoryEntry(
                created_at=datetime.now().isoformat(timespec="seconds"),
                user=user_message.strip(),
                assistant=assistant_reply.strip(),
            )
        )
        data["entries"] = [entry.to_dict() for entry in entries]
        self._write_data(data)

        if self._file_size() > self.config.max_bytes:
            self.compress(summarizer)

    def compress(self, summarizer: Callable[[str, list[MemoryEntry]], str]) -> None:
        data = self._load_data()
        entries = self._decode_entries(data.get("entries"))
        if not entries:
            return

        keep_count = self.config.recent_turns_after_compress
        kept_entries = entries[-keep_count:] if keep_count > 0 else []
        old_entries = entries[:-keep_count] if keep_count > 0 else entries
        if not old_entries:
            old_entries = entries
            kept_entries = []

        existing_summary = str(data.get("summary") or "").strip()
        try:
            summary = summarizer(existing_summary, old_entries).strip()
        except Exception:
            summary = existing_summary

        if not summary:
            summary = self._fallback_summary(old_entries)

        compressed = {
            "version": 1,
            "summary": summary,
            "entries": [entry.to_dict() for entry in kept_entries],
            "compressed_at": datetime.now().isoformat(timespec="seconds"),
        }
        self._write_data(compressed)

    def search(self, query: str, *, limit: int) -> list[MemoryEntry]:
        if limit <= 0:
            return []
        query = query.strip()
        if not query:
            return []

        query_tokens = _tokens(query)
        scored: list[tuple[float, float, MemoryEntry]] = []
        now = time.time()
        entries = self._load_entries()
        for index, entry in enumerate(entries):
            text = entry.as_search_text()
            text_lower = text.lower()
            overlap = sum(1 for token in query_tokens if token in text_lower)
            ratio = SequenceMatcher(None, query.lower(), text_lower[:800]).ratio()
            recency = (index + 1) / max(1, len(entries))
            score = overlap * 2.0 + ratio + recency * 0.15
            if score > 0.2:
                scored.append((score, now + index, entry))

        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return [entry for _, _, entry in scored[:limit]]

    def _load_entries(self) -> list[MemoryEntry]:
        return self._decode_entries(self._load_data().get("entries"))

    def _load_data(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "summary": "", "entries": []}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {"version": 1, "summary": "", "entries": []}
        if not isinstance(data, dict):
            return {"version": 1, "summary": "", "entries": []}
        data.setdefault("version", 1)
        data.setdefault("summary", "")
        data.setdefault("entries", [])
        return data

    def _decode_entries(self, value: object) -> list[MemoryEntry]:
        if not isinstance(value, list):
            return []
        entries: list[MemoryEntry] = []
        for item in value:
            if not isinstance(item, dict):
                continue
            user = str(item.get("user") or "").strip()
            assistant = str(item.get("assistant") or "").strip()
            if not user and not assistant:
                continue
            entries.append(
                MemoryEntry(
                    created_at=str(item.get("created_at") or ""),
                    user=user,
                    assistant=assistant,
                )
            )
        return entries

    def _write_data(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _file_size(self) -> int:
        try:
            return self.path.stat().st_size
        except OSError:
            return 0

    def _fallback_summary(self, entries: list[MemoryEntry]) -> str:
        lines: list[str] = []
        for entry in entries[-20:]:
            text = entry.as_search_text().replace("\n", " ")
            if len(text) > 180:
                text = text[:177] + "..."
            lines.append(f"- {text}")
        return "\n".join(lines)


def _tokens(text: str) -> set[str]:
    lowered = text.lower()
    words = set(re.findall(r"[a-z0-9_]{2,}", lowered))
    cjk = re.findall(r"[\u4e00-\u9fff]", lowered)
    words.update(cjk)
    for size in (2, 3):
        for index in range(0, max(0, len(cjk) - size + 1)):
            words.add("".join(cjk[index : index + size]))
    return words

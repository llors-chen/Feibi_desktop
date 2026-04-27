from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

try:
    from openai import OpenAI
except Exception as exc:  # pragma: no cover - optional runtime dependency guard
    OpenAI = None
    OPENAI_IMPORT_ERROR = exc
else:
    OPENAI_IMPORT_ERROR = None

from .config import ChatConfig


class ChatError(RuntimeError):
    pass


class ChatClient:
    def __init__(self, config: ChatConfig) -> None:
        self.config = config

    def ensure_ready(self) -> None:
        if not self.config.enabled:
            raise ChatError("聊天功能未启用，请先在 pet_config.json 中打开 chat.enabled。")
        if OpenAI is None:
            raise ChatError(
                "缺少 openai 依赖，请先执行 pip install -r requirements.txt。"
            )
        if not self.config.api_key:
            raise ChatError("chat.api_key 不能为空。")
        if not self.config.model:
            raise ChatError("chat.model 不能为空。")

    def request_reply(
        self,
        history: Sequence[dict[str, str]],
        user_message: str,
        *,
        memory_context: str = "",
    ) -> str:
        self.ensure_ready()
        client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url or None,
            timeout=self.config.timeout_seconds,
        )

        completion = client.chat.completions.create(
            model=self.config.model,
            messages=self._build_messages(history, user_message, memory_context),
        )
        return self._extract_text(completion)

    def summarize_memory(
        self,
        existing_summary: str,
        exchanges_text: str,
    ) -> str:
        self.ensure_ready()
        client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url or None,
            timeout=self.config.timeout_seconds,
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "你是桌宠菲比的长期记忆整理器。请把旧对话压缩成简洁、可检索的中文记忆。"
                    "保留用户偏好、设定、长期事实、重要事件、承诺、称呼和情绪线索；"
                    "删除寒暄、重复内容和无意义细节。输出要点列表即可。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"已有记忆摘要:\n{existing_summary or '无'}\n\n"
                    f"需要压缩的旧对话:\n{exchanges_text}\n\n"
                    "请合并为新的长期记忆摘要，尽量控制在 4000 字以内。"
                ),
            },
        ]
        completion = client.chat.completions.create(
            model=self.config.model,
            messages=messages,
        )
        return self._extract_text(completion)

    def _build_messages(
        self,
        history: Sequence[dict[str, str]],
        user_message: str,
        memory_context: str = "",
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        system_prompt = self._resolve_system_prompt()
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if memory_context.strip():
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "以下是菲比长期记忆中与当前对话可能相关的信息。"
                        "它可能不完整或只模糊相关，请结合当前用户输入使用，"
                        "不要逐字复述给用户。\n\n"
                        f"{memory_context.strip()}"
                    ),
                }
            )

        if self.config.max_history > 0:
            messages.extend(history[-self.config.max_history * 2 :])

        messages.append({"role": "user", "content": user_message})
        return messages

    def _resolve_system_prompt(self) -> str:
        parts: list[str] = []
        if self.config.skill_path is not None:
            parts.append(_read_text(self.config.skill_path))
        if self.config.system_prompt:
            parts.append(self.config.system_prompt.strip())
        return "\n\n".join(part for part in parts if part).strip()

    def _extract_text(self, completion: Any) -> str:
        try:
            content = completion.choices[0].message.content
        except Exception as exc:
            raise ChatError(f"聊天接口返回格式异常: {exc}") from exc

        if isinstance(content, str):
            text = content.strip()
            return text or "模型没有返回文本内容。"

        if isinstance(content, list):
            chunks: list[str] = []
            for item in content:
                text = getattr(item, "text", None)
                if isinstance(text, str) and text.strip():
                    chunks.append(text.strip())
                    continue
                if isinstance(item, dict):
                    nested = item.get("text")
                    if isinstance(nested, str) and nested.strip():
                        chunks.append(nested.strip())
            merged = "".join(chunks).strip()
            return merged or "模型没有返回文本内容。"

        return "模型没有返回可显示的文本内容。"


def _read_text(path: Path) -> str:
    last_error: Exception | None = None
    for encoding in ("utf-8", "utf-8-sig", "gbk"):
        try:
            return path.read_text(encoding=encoding).strip()
        except Exception as exc:  # pragma: no cover - small fallback helper
            last_error = exc
    raise ChatError(f"读取 skill 文件失败: {path} ({last_error})")

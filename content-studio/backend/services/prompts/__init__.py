"""Prompt 模板与组装辅助（generator 依赖）。

- `system.md`：默认人设 + 三条死规则 + 参考示例
- `sections.py`：组装段落的 helper（风格优先级、mode、长度、资料库文档、参考素材）
"""
from pathlib import Path

_SYSTEM_PATH = Path(__file__).parent / "system.md"
SYSTEM_PROMPT: str = _SYSTEM_PATH.read_text(encoding="utf-8")

# 平台名称映射（仅用于 prompt 上下文提示，不限制字数和风格）
PLATFORM_LABELS = {
    "douyin": "抖音",
    "xiaohongshu": "小红书",
    "weixin": "微信视频号",
}

__all__ = ["SYSTEM_PROMPT", "PLATFORM_LABELS"]

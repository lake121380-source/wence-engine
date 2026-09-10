"""PromptBuilder: 汇总上下文并输出 system/user prompt 及结构化 debug 信息。"""

from __future__ import annotations

from dataclasses import dataclass

from services.prompts import SYSTEM_PROMPT, PLATFORM_LABELS
from services.prompts.sections import (
    build_length_requirement_block,
    compose_mode_block,
    compose_product_doc_block,
    compose_refs_block,
    compose_style_priority_block,
    compose_user_prompt,
)


@dataclass
class PromptBuildContext:
    topic: str
    platform: str
    target_word_count: int | None
    style_template_id: int | None
    creator_ids: list[int] | None
    product_doc_ids: list[int] | None
    viral_analysis_ids: list[int] | None
    style_context: str
    industry_context: str
    product_context: str
    viewpoint_context: str
    viral_context: str


class PromptBuilder:
    """将生成上下文转换为 prompt 文本。"""

    @staticmethod
    def build(ctx: PromptBuildContext) -> dict:
        has_doc = bool(ctx.product_doc_ids)
        has_viral = bool(ctx.viral_analysis_ids)
        has_style = bool(ctx.style_template_id or ctx.creator_ids)

        platform_label = PLATFORM_LABELS.get(ctx.platform, ctx.platform)
        mode_block = compose_mode_block(has_doc=has_doc, has_viral=has_viral)
        style_priority_block = compose_style_priority_block(has_doc=has_doc, has_style=has_style)
        product_doc_block = compose_product_doc_block(ctx.product_context, ctx.product_doc_ids)
        refs_block = compose_refs_block(
            style_context=ctx.style_context,
            industry_context=ctx.industry_context,
            product_context=ctx.product_context,
            product_doc_ids=ctx.product_doc_ids,
            viewpoint_context=ctx.viewpoint_context,
            viral_context=ctx.viral_context,
        )
        # @资料库 > target_word_count > 350 底线：有 doc 时不再叠加目标字数
        length_requirement_block = ""
        if not has_doc:
            length_requirement_block = build_length_requirement_block(ctx.target_word_count)

        user_prompt = compose_user_prompt(
            platform_label=platform_label,
            topic=ctx.topic,
            style_priority_block=style_priority_block,
            mode_block=mode_block,
            product_doc_block=product_doc_block,
            length_requirement_block=length_requirement_block,
            refs_block=refs_block,
        )

        mode_branch = "plain"
        if has_doc and has_viral:
            mode_branch = "doc+viral"
        elif has_doc:
            mode_branch = "doc_only"
        elif has_viral:
            mode_branch = "viral_only"

        debug = {
            "mode_branch": mode_branch,
            "has_doc": has_doc,
            "has_viral": has_viral,
            "has_style": has_style,
            "platform_label": platform_label,
            "doc_chars_injected": len(ctx.product_context or ""),
            "viral_chars_injected": len(ctx.viral_context or ""),
            "style_chars_injected": len(ctx.style_context or ""),
            "industry_chars_injected": len(ctx.industry_context or ""),
            "viewpoint_chars_injected": len(ctx.viewpoint_context or ""),
            "length_rule_applied": bool(length_requirement_block),
            "product_doc_ids": ctx.product_doc_ids or [],
            "creator_ids": ctx.creator_ids or [],
            "viral_analysis_ids": ctx.viral_analysis_ids or [],
        }

        return {
            "system": SYSTEM_PROMPT,
            "user": user_prompt,
            "debug": debug,
        }

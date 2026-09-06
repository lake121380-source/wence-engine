"""Prompt 片段组装 helper。"""

from typing import List


def build_length_requirement_block(target_word_count: int | None) -> str:
    if not target_word_count:
        return ""
    min_words = max(100, int(target_word_count * 0.9))
    max_words = min(2000, int(target_word_count * 1.1))
    return (
        "## 字数硬性要求\n"
        f"- 目标字数：{target_word_count} 字\n"
        f"- 允许范围：{min_words} - {max_words} 字\n"
        "- 请严格控制篇幅，不要明显少于或多于目标字数"
    )


def compose_mode_block(has_doc: bool = False, has_viral: bool = False) -> str:
    """根据用户引用的素材类型，返回对应的创作指令（只讲怎么写，不讲写多长）。"""
    if has_doc and has_viral:
        return (
            "创作思路：先看下面那几条爆款为什么能爆——爆点在哪、情绪怎么走、结构怎么铺。"
            "然后把资料库里的料（事实、数据、案例、场景）按那个路子重新讲一遍。"
            "爆款是『怎么讲』的参考，资料库是『讲什么』的素材，两边都不要照抄。"
        )
    if has_doc:
        return (
            "创作思路：下面是用户从资料库里圈给你的原文。"
            "你要按它的结构、节奏、信息密度和语气重写一条新的——长度要贴上它，不能写两段就收。"
            "原文里的事实、案例、数据可以用，但句子不要复制；表达要全部换成你自己的。"
            "如果用户明确说了『仿写』，那就更贴着原文的骨架来。"
        )
    if has_viral:
        return (
            "创作思路：参考下面爆款诊断里提炼的爆点逻辑、情绪路径和结构节奏，围绕我的话题写一条新的。"
            "不要复用原文的台词和案例，内核复刻，表层原创。"
        )
    return (
        "创作思路：根据我的话题，找一个最能戳到目标用户的切入点，只打透一个核心点，"
        "让人看完有强烈的「说的就是我」或「我不知道这个」的感觉。"
    )


def compose_style_priority_block(has_doc: bool, has_style: bool) -> str:
    """声明风格优先级，避免默认人设压过用户 @ 的内容。"""
    if not (has_doc or has_style):
        return ""
    lines: List[str] = ["## 风格优先级（从高到低）"]
    n = 1
    if has_doc:
        lines.append(f"{n}. 本消息里 @的资料库原文风格（仿写/参考时，语气、节奏、篇幅都贴合它）")
        n += 1
    if has_style:
        lines.append(f"{n}. 本消息里 @的博主风格模板（按模板的语气和套路写）")
        n += 1
    lines.append(f"{n}. system 里的默认人设（只在以上两者都不生效时使用）")
    lines.append("注意：当有高优先级风格时，不要让默认人设的口吻压过去。")
    return "\n".join(lines)


def compose_product_doc_block(product_context: str, product_doc_ids: list[int] | None) -> str:
    """显式 @ 资料库原文时，单独提升优先级。"""
    if not (product_context and product_doc_ids):
        return ""
    return (
        "## 用户@的原始文案（重点依据，必须认真对待）\n"
        "下面是用户从资料库里圈出来要你参考/仿写的原文。它的篇幅、信息密度、叙事结构就是你输出的目标标准——"
        "你的正文长度和信息量必须和它相当，不能只写一两段就交差。\n\n"
        f"{product_context}"
    )


def compose_refs_block(
    style_context: str,
    industry_context: str,
    product_context: str,
    product_doc_ids: list[int] | None,
    viewpoint_context: str,
    viral_context: str,
) -> str:
    """组装可选参考素材区块。"""
    ref_sections: list[str] = []
    if style_context:
        ref_sections.append(f"### 博主风格参考\n{style_context}")
    if industry_context:
        ref_sections.append(f"### 行业知识\n{industry_context}")
    if product_context and not product_doc_ids:
        ref_sections.append(f"### 资料库（背景参考）\n{product_context}")
    if viewpoint_context:
        ref_sections.append(f"### 运营者观点（请融入文案）\n{viewpoint_context}")
    if viral_context:
        ref_sections.append(f"### 爆款洞察（参考成功要素）\n{viral_context}")
    if not ref_sections:
        return ""
    return "## 参考素材（辅助提升质量，不能偏离我的要求）\n\n" + "\n\n".join(ref_sections)


def compose_user_prompt(
    platform_label: str,
    topic: str,
    style_priority_block: str,
    mode_block: str,
    product_doc_block: str,
    length_requirement_block: str,
    refs_block: str,
) -> str:
    """按既定顺序组装 user prompt。"""
    parts = [
        f"## 创作平台\n{platform_label}",
        "## 我的创作要求（请严格按此执行）\n<user_topic>\n" + topic + "\n</user_topic>",
    ]
    if style_priority_block:
        parts.append(style_priority_block)
    parts.append(mode_block)
    if product_doc_block:
        parts.append(product_doc_block)
    if length_requirement_block:
        parts.append(length_requirement_block)
    if refs_block:
        parts.append(refs_block)
    return "\n\n".join(parts)

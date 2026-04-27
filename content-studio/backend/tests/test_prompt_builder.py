from services.prompt_builder import PromptBuilder, PromptBuildContext


def _ctx(**kwargs) -> PromptBuildContext:
    base = dict(
        topic="测试话题",
        platform="douyin",
        target_word_count=None,
        style_template_id=None,
        creator_ids=None,
        product_doc_ids=None,
        viral_analysis_ids=None,
        style_context="",
        industry_context="",
        product_context="",
        viewpoint_context="",
        viral_context="",
    )
    base.update(kwargs)
    return PromptBuildContext(**base)


def test_plain_mode_no_length_rule_without_target():
    out = PromptBuilder.build(_ctx())
    assert out["debug"]["mode_branch"] == "plain"
    assert out["debug"]["length_rule_applied"] is False
    assert "## 字数硬性要求" not in out["user"]


def test_doc_only_mode_hides_length_rule_even_with_target():
    out = PromptBuilder.build(
        _ctx(
            target_word_count=600,
            product_doc_ids=[1],
            product_context="文档正文",
        )
    )
    assert out["debug"]["mode_branch"] == "doc_only"
    assert out["debug"]["length_rule_applied"] is False
    assert "## 字数硬性要求" not in out["user"]
    assert "## 用户@的原始文案" in out["user"]


def test_viral_only_mode_and_length_rule_with_target():
    out = PromptBuilder.build(_ctx(target_word_count=500, viral_analysis_ids=[9], viral_context="爆款洞察"))
    assert out["debug"]["mode_branch"] == "viral_only"
    assert out["debug"]["length_rule_applied"] is True
    assert "## 字数硬性要求" in out["user"]


def test_style_priority_block_present_when_style_or_doc_exists():
    out_style = PromptBuilder.build(_ctx(style_template_id=3, style_context="风格参考"))
    assert "## 风格优先级（从高到低）" in out_style["user"]

    out_doc = PromptBuilder.build(_ctx(product_doc_ids=[2], product_context="原文", creator_ids=[8]))
    assert "## 风格优先级（从高到低）" in out_doc["user"]

"""
文案生成服务
- 组装 RAG 上下文
- 调用 Claude API
- 解析结构化输出
"""
import json, asyncio, re
from typing import AsyncGenerator

import anthropic
from sqlalchemy.orm import Session
from models import StyleTemplate, Generation
from services.knowledge import knowledge_service
from services.prompt_builder import PromptBuilder, PromptBuildContext
from services.prompts import SYSTEM_PROMPT
from config import settings


class GeneratorService:

    def __init__(self):
        if settings.use_deepseek:
            # 使用DeepSeek兼容Anthropic API的接口
            self.client = anthropic.Anthropic(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url
            )
            self.model_name = settings.deepseek_model
        else:
            # 使用原始Anthropic API
            self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            self.model_name = "claude-sonnet-4-20250514"

    async def generate(
        self,
        db: Session,
        topic: str,
        platform: str = "douyin",
        target_word_count: int | None = None,
        style_template_id: int = None,
        product_doc_ids: list[int] = None,
        creator_ids: list[int] = None,
        viewpoint_ids: list[int] = None,
        viral_analysis_ids: list[int] = None,
        tenant_id: int = None,
        user_id: int = None,
        history: list[dict] = None,
    ) -> dict:
        """
        主生成方法（五源RAG + 对话上下文）
        - history: 之前的对话轮次，用于多轮迭代
        - 只有用户显式引用素材时才加载对应 RAG 源，避免噪音
        """
        rag = self._build_rag_and_prompt(
            db, topic, platform, target_word_count,
            style_template_id, product_doc_ids, creator_ids,
            viewpoint_ids, viral_analysis_ids, tenant_id, history,
        )

        loop = asyncio.get_event_loop()
        message = await loop.run_in_executor(
            None,
            lambda: self.client.messages.create(
                model=self.model_name,
                max_tokens=4096,
                temperature=0.75,
                system=SYSTEM_PROMPT,
                messages=rag["ai_messages"],
            )
        )
        raw_output = message.content[0].text.strip()
        output = self._parse_output(raw_output)

        gen = self._save_generation(
            db, rag, output, raw_output,
            tenant_id=tenant_id, user_id=user_id,
            style_template_id=style_template_id,
            product_doc_ids=product_doc_ids, creator_ids=creator_ids,
            viewpoint_ids=viewpoint_ids, viral_analysis_ids=viral_analysis_ids,
        )

        return {
            "id": gen.id,
            "title": output.get("title", ""),
            "hook": output.get("hook", ""),
            "body": output.get("body", ""),
            "cta": output.get("cta", ""),
            "tags": output.get("tags", []),
            "platform": platform,
            "topic": topic,
        }

    # ── 内部 helpers ──────────────────────────────────────
    @staticmethod
    def _build_messages(history: list[dict] | None, user_prompt: str) -> list[dict]:
        """构建对话消息列表（支持多轮迭代）"""
        ai_messages = []
        if history:
            recent = history[-6:]  # 最多 3 轮
            for msg in recent:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role in ("user", "assistant") and content:
                    ai_messages.append({"role": role, "content": content})
        ai_messages.append({"role": "user", "content": user_prompt})
        return ai_messages

    # ── 共享方法 ──────────────────────────────────────────

    def _build_rag_and_prompt(
        self, db, topic, platform,
        target_word_count, style_template_id,
        product_doc_ids, creator_ids,
        viewpoint_ids, viral_analysis_ids,
        tenant_id, history,
    ):
        """构建五源 RAG 上下文 + 组装 prompt。"""
        has_explicit_refs = bool(creator_ids or product_doc_ids or viewpoint_ids
                                or viral_analysis_ids or style_template_id)

        if style_template_id:
            style_context = self._get_style_context(db, style_template_id, topic, tenant_id=tenant_id)
        elif has_explicit_refs and creator_ids:
            style_context = self._get_style_context(db, None, topic, tenant_id=tenant_id)
        else:
            style_context = ""

        if creator_ids:
            industry_results = knowledge_service.retrieve_industry(topic, n=5, creator_id=creator_ids[0])
            industry_context = self._format_retrieval(industry_results) if industry_results else ""
        elif has_explicit_refs and tenant_id:
            from models import TenantCreator as _TC
            sub_cids = [r.creator_id for r in db.query(_TC.creator_id).filter(_TC.tenant_id == tenant_id).all()]
            if sub_cids:
                industry_results = knowledge_service.retrieve_industry(topic, n=5, creator_id_list=sub_cids)
                industry_context = self._format_retrieval(industry_results) if industry_results else ""
            else:
                industry_context = ""
        else:
            industry_context = ""

        if product_doc_ids:
            product_context = self._get_product_doc_full_context(db, product_doc_ids, tenant_id=tenant_id)
        elif not has_explicit_refs and tenant_id:
            fallback_results = knowledge_service.retrieve_product(topic, n=3, tenant_id=tenant_id)
            product_context = self._format_retrieval(fallback_results) if fallback_results else ""
        else:
            product_context = ""

        if viewpoint_ids:
            viewpoint_context = self._get_viewpoint_context(db, topic, viewpoint_ids, tenant_id=tenant_id)
        else:
            viewpoint_context = ""

        if viral_analysis_ids:
            viral_context = self._get_viral_context(db, viral_analysis_ids, tenant_id=tenant_id)
        else:
            viral_context = ""

        prompt_pack = PromptBuilder.build(
            PromptBuildContext(
                topic=topic, platform=platform,
                target_word_count=target_word_count,
                style_template_id=style_template_id,
                creator_ids=creator_ids, product_doc_ids=product_doc_ids,
                viral_analysis_ids=viral_analysis_ids,
                style_context=style_context, industry_context=industry_context,
                product_context=product_context, viewpoint_context=viewpoint_context,
                viral_context=viral_context,
            )
        )
        user_prompt = prompt_pack["user"]
        prompt = f"[SYSTEM]\n{prompt_pack['system']}\n\n[USER]\n{user_prompt}"
        ai_messages = self._build_messages(history, user_prompt)

        return {
            "has_explicit_refs": has_explicit_refs,
            "prompt_pack": prompt_pack,
            "prompt": prompt,
            "ai_messages": ai_messages,
        }

    def _save_generation(self, db, rag, output, raw_output,
                         tenant_id=None, user_id=None,
                         style_template_id=None, product_doc_ids=None,
                         creator_ids=None, viewpoint_ids=None,
                         viral_analysis_ids=None):
        """保存 Generation 记录。"""
        prompt_pack = rag["prompt_pack"]
        gen = Generation(
            tenant_id=tenant_id, user_id=user_id,
            topic=rag.get("user_prompt", "")[:100],
            platform=rag.get("platform", "douyin"),
            style_template_id=style_template_id,
            product_doc_ids=product_doc_ids or [],
            creator_ids=creator_ids or [],
            viewpoint_ids=viewpoint_ids or [],
            viral_analysis_ids=viral_analysis_ids or [],
            prompt_used=rag["prompt"],
            output_title=output.get("title", ""),
            output_hook=output.get("hook", ""),
            output_body=output.get("body", ""),
            output_cta=output.get("cta", ""),
            output_full=raw_output,
            debug_info=prompt_pack.get("debug", {}),
            mode_branch=prompt_pack.get("debug", {}).get("mode_branch", "plain"),
            temperature_used=0.75,
            doc_chars_injected=prompt_pack.get("debug", {}).get("doc_chars_injected", 0),
            viral_chars_injected=prompt_pack.get("debug", {}).get("viral_chars_injected", 0),
        )
        db.add(gen)
        db.commit()
        db.refresh(gen)
        return gen

    # 标签行判定：整行至少 2 个 token，且每个 token 都是 #+可打印字符（中文/英数/下划线）
    _TAG_TOKEN_RE = re.compile(r'^#[\w\u4e00-\u9fff][\w\u4e00-\u9fff\-]*$')

    @classmethod
    def _is_tag_line(cls, line: str) -> bool:
        stripped = line.strip()
        if not stripped:
            return False
        tokens = stripped.split()
        if len(tokens) < 2:
            return False
        return all(cls._TAG_TOKEN_RE.match(t) for t in tokens)

    @classmethod
    def _parse_output(cls, raw_output: str) -> dict:
        """从 LLM 原始输出中解析纯文本文案 + 标签。
        只从末尾反向扫描连续的 tag 行，碰到第一个非 tag 行立刻停止，
        避免误把正文里独立的 `#1 ...` 或 `#正文` 这类行当作标签吃掉。"""
        text = raw_output.strip()
        lines = text.split('\n')
        # 去末尾空行
        while lines and not lines[-1].strip():
            lines.pop()

        tag_lines: list[str] = []
        while lines and cls._is_tag_line(lines[-1]):
            tag_lines.append(lines.pop())
            while lines and not lines[-1].strip():
                lines.pop()
        # tag_lines 是从下往上 pop 的，恢复原始顺序
        tag_lines.reverse()

        tags: list[str] = []
        for tl in tag_lines:
            for tok in tl.strip().split():
                name = tok.lstrip('#').strip()
                if name:
                    tags.append(name)

        body = '\n'.join(lines).strip()
        return {
            "title": "",
            "hook": "",
            "body": body,
            "cta": "",
            "tags": tags,
        }

    async def generate_stream(
        self,
        db: Session,
        topic: str,
        platform: str = "douyin",
        target_word_count: int | None = None,
        style_template_id: int = None,
        product_doc_ids: list[int] = None,
        creator_ids: list[int] = None,
        viewpoint_ids: list[int] = None,
        viral_analysis_ids: list[int] = None,
        tenant_id: int = None,
        user_id: int = None,
        history: list[dict] = None,
    ) -> AsyncGenerator[str, None]:
        """
        流式生成方法，yield SSE 格式的 text chunk。
        最后 yield 一条 event:done 包含完整解析结果 + generation id。
        """
        # ── 共享 RAG 上下文构建 ──
        rag = self._build_rag_and_prompt(
            db, topic, platform, target_word_count,
            style_template_id, product_doc_ids, creator_ids,
            viewpoint_ids, viral_analysis_ids, tenant_id, history,
        )
        ai_messages = rag["ai_messages"]

        # ── 流式调用 LLM（使用 asyncio.Queue 消除忙等） ──
        loop = asyncio.get_event_loop()
        import threading
        q = asyncio.Queue()

        def _producer():
            try:
                with self.client.messages.stream(
                    model=self.model_name,
                    max_tokens=4096,
                    temperature=0.75,
                    system=SYSTEM_PROMPT,
                    messages=ai_messages,
                ) as stream:
                    for text in stream.text_stream:
                        asyncio.run_coroutine_threadsafe(q.put(("chunk", text)), loop)
                asyncio.run_coroutine_threadsafe(q.put(("done", None)), loop)
            except Exception as e:
                asyncio.run_coroutine_threadsafe(q.put(("error", str(e))), loop)

        thread = threading.Thread(target=_producer, daemon=True)
        thread.start()

        all_chunks = []
        while True:
            kind, data = await q.get()  # 阻塞等待，无忙等
            if kind == "chunk":
                all_chunks.append(data)
                escaped = json.dumps(data, ensure_ascii=False)
                yield f"data: {escaped}\n\n"
            elif kind == "done":
                break
            elif kind == "error":
                yield f"event: error\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                return

        # ── 解析 & 保存 ──
        raw_output = "".join(all_chunks).strip()
        output = self._parse_output(raw_output)

        gen = self._save_generation(
            db, rag, output, raw_output,
            tenant_id=tenant_id, user_id=user_id,
            style_template_id=style_template_id,
            product_doc_ids=product_doc_ids, creator_ids=creator_ids,
            viewpoint_ids=viewpoint_ids, viral_analysis_ids=viral_analysis_ids,
        )

        result = {
            "id": gen.id,
            "title": output.get("title", ""),
            "hook": output.get("hook", ""),
            "body": output.get("body", ""),
            "cta": output.get("cta", ""),
            "tags": output.get("tags", []),
            "platform": platform,
            "topic": topic,
        }
        yield f"event: done\ndata: {json.dumps(result, ensure_ascii=False)}\n\n"

    async def analyze_style(self, db: Session, creator_id: int, tenant_id: int = None) -> dict:
        """
        分析博主风格并生成/更新风格模版
        从已抓取的视频中提取风格特征，优先使用语音转录（script）
        """
        from models import Creator, CreatorVideo
        creator = db.query(Creator).filter(Creator.id == creator_id).first()
        videos = db.query(CreatorVideo).filter(
            CreatorVideo.creator_id == creator_id,
        ).order_by(CreatorVideo.like_count.desc()).limit(30).all()

        if not videos:
            raise ValueError("该博主还没有视频数据，请先抓取内容")

        # 区分爆款 vs 普通视频（按点赞量，取中位值分割）
        likes = sorted([v.like_count or 0 for v in videos], reverse=True)
        median_likes = likes[len(likes) // 2] if likes else 0

        # 构造样本：优先用 script（实际口播内容），其次 description
        hot_samples = []
        normal_samples = []
        for v in videos:
            content = (v.script or "").strip()
            desc = (v.description or "").strip()
            if not content and not desc:
                continue
            # 组装单条样本
            entry = f"标题：{v.title or '(无标题)'}\n点赞：{v.like_count:,}"
            if content:
                entry += f"\n口播文案（视频中说的话）：{content[:500]}"
            if desc and desc != content[:len(desc)]:
                entry += f"\n发布描述：{desc[:100]}"
            if (v.like_count or 0) > median_likes:
                hot_samples.append(entry)
            else:
                normal_samples.append(entry)

        hot_text = "\n\n---\n\n".join(hot_samples[:8])
        normal_text = "\n\n---\n\n".join(normal_samples[:4])

        analysis_prompt = f"""你是一位专业的短视频运营策略师。请深入分析博主「{creator.nickname}」（{creator.platform}，粉丝 {(creator.follower_count or 0):,}）的创作风格。

## 爆款视频样本（点赞>{median_likes:,}的高互动视频）
{hot_text or '暂无'}

## 普通视频样本（对比参考）
{normal_text or '暂无'}

## 分析要求
对比爆款和普通视频的差异，提取这个博主**能复用的风格特征**。请以JSON格式返回：

{{
  "tone_description": "语气风格详细描述（50字以内）：口语化/书面化、情绪基调、人称视角、是否有口头禅",
  "structure_pattern": "内容结构模式（80字以内）：典型的视频流程，从开头到结尾的内容编排规律",
  "hook_patterns": ["爆款常用的开头hook模式1（带具体示例）", "开头模式2", "开头模式3"],
  "cta_patterns": ["结尾引导互动/关注的方式1（带具体示例）", "方式2"],
  "content_formula": "爆款内容公式（60字以内）：这个博主的爆款视频有什么共同的内容框架或叙事套路",
  "vocabulary_style": "用词特征（40字以内）：专业术语使用程度、是否用比喻/类比、金句特点",
  "example_scripts": ["从样本中提炼的最佳文案模板1（200字以内，保留原始风格）", "模板2"]
}}"""

        import json, asyncio
        loop = asyncio.get_event_loop()
        message = await loop.run_in_executor(
            None,
            lambda: self.client.messages.create(
                model=self.model_name,
                max_tokens=2000,
                messages=[{"role": "user", "content": analysis_prompt}]
            )
        )
        raw = message.content[0].text.strip().replace("```json", "").replace("```", "").strip()

        try:
            style_data = json.loads(raw)
        except Exception:
            raise ValueError("风格分析解析失败")

        # 保存或更新风格模版（严格按 creator_id + tenant_id 匹配，避免跨租户覆盖）
        existing = db.query(StyleTemplate).filter(
            StyleTemplate.creator_id == creator_id,
            StyleTemplate.tenant_id == tenant_id,
        ).first()
        if existing:
            for k, v in style_data.items():
                setattr(existing, k, v)
            tmpl = existing
        else:
            tmpl = StyleTemplate(
                creator_id=creator_id,
                name=f"{creator.nickname} 风格",
                platform=creator.platform,
                tenant_id=tenant_id,
                **style_data
            )
            db.add(tmpl)

        db.commit()
        db.refresh(tmpl)

        # 索引到向量库
        knowledge_service.index_style_template(db, tmpl.id)

        return {
            "template_id": tmpl.id,
            "name": tmpl.name,
            **style_data
        }

    def _get_style_context(self, db: Session, template_id: int, topic: str, tenant_id: int = None) -> str:
        if not template_id:
            # 从向量库检索最相关的风格（按租户隔离）
            results = knowledge_service.retrieve_style(topic, n=1, tenant_id=tenant_id)
            if results:
                return results[0]["text"]
            return "通用短视频风格：开门见山，节奏紧凑，口语化表达"

        tmpl = db.query(StyleTemplate).filter(StyleTemplate.id == template_id).first()
        if not tmpl:
            return "通用短视频风格"

        parts = [f"语气风格：{tmpl.tone_description or ''}"]
        if tmpl.structure_pattern:
            parts.append(f"内容结构套路：{tmpl.structure_pattern}")
        if tmpl.content_formula:
            parts.append(f"爆款内容公式：{tmpl.content_formula}")
        if tmpl.vocabulary_style:
            parts.append(f"用词特征：{tmpl.vocabulary_style}")
        if tmpl.hook_patterns:
            # 注入所有开头模式，不只是第一条
            hooks = "\n".join([f"  · {h}" for h in tmpl.hook_patterns])
            parts.append(f"开头套路（可任选）：\n{hooks}")
        if tmpl.cta_patterns:
            ctas = "\n".join([f"  · {c}" for c in tmpl.cta_patterns])
            parts.append(f"结尾互动引导：\n{ctas}")
        if tmpl.example_scripts:
            # 注入全部示例文案（不截断），这是模仿风格最重要的输入
            scripts_text = "\n\n---\n\n".join([s[:600] for s in tmpl.example_scripts])
            parts.append(f"该博主高互动文案原文（严格模仿这些文案的语气、断句、节奏和词汇习惯）：\n\n{scripts_text}")
        return "\n\n".join(parts)

    def _get_viewpoint_context(self, db: Session, topic: str, viewpoint_ids: list[int] = None, tenant_id: int = None) -> str:
        """获取运营者观点上下文（第4源）"""
        from models import OperatorViewpoint
        lines = []
        if viewpoint_ids:
            vps = db.query(OperatorViewpoint).filter(
                OperatorViewpoint.id.in_(viewpoint_ids),
                OperatorViewpoint.is_active == True,
                OperatorViewpoint.tenant_id == tenant_id,
            ).all()
            for vp in vps:
                lines.append(f"【{vp.category}】{vp.title}：{vp.content[:200]}")
        else:
            results = knowledge_service.retrieve_viewpoints(topic, n=3, tenant_id=tenant_id)
            for r in results:
                lines.append(r["text"][:200])
        return "\n\n".join(lines) if lines else "暂无运营者观点，请在观点库中添加您的独立立场"

    def _get_viral_context(self, db: Session, viral_analysis_ids: list[int] = None, tenant_id: int = None) -> str:
        """获取爆款分析洞察（第5源）"""
        if not viral_analysis_ids:
            return "暂无参考爆款，如需增强效果请在选题库分析爆款后选择参考"
        from models import VideoAnalysis
        _f = [VideoAnalysis.id.in_(viral_analysis_ids)]
        if tenant_id:
            _f.append(VideoAnalysis.tenant_id == tenant_id)
        analyses = db.query(VideoAnalysis).filter(*_f).all()
        lines = []
        for a in analyses:
            title = (a.raw_data or {}).get("title", f"视频#{a.video_id or a.topic_id}")
            original_script = (a.raw_data or {}).get("script") or (a.raw_data or {}).get("transcript") or ""
            block = [f"参考爆款「{title[:80]}」："]
            if original_script:
                block.append(f"- 原视频口播文案：{original_script[:1500]}")
            if a.resonance_analysis:
                block.append(f"- 共鸣点（为什么点赞）：{a.resonance_analysis[:800]}")
            if a.discussion_analysis:
                block.append(f"- 讨论钩子（为什么评论）：{a.discussion_analysis[:800]}")
            if a.value_analysis:
                block.append(f"- 收藏价值：{a.value_analysis[:600]}")
            if a.why_viral_summary:
                block.append(f"- 爆款综合诊断：{a.why_viral_summary[:1200]}")
            lines.append("\n".join(block))
        return "\n\n".join(lines) if lines else "暂无爆款分析数据"

    @staticmethod
    def _truncate_by_boundary(text: str, limit: int) -> str:
        """在 limit 内优先按段落/句号/换行切断，保留完整句子。"""
        if len(text) <= limit:
            return text
        head = text[:limit]
        # 优先级：段落 > 中文标点 > 换行 > 英文句号
        for sep in ("\n\n", "。", "！", "？", "\n", ". ", "; "):
            idx = head.rfind(sep)
            if idx >= limit * 0.6:  # 防止切得太短
                return head[: idx + len(sep)].rstrip()
        return head

    def _get_product_doc_full_context(self, db: Session, doc_ids: list[int], tenant_id: int = None) -> str:
        """用户显式 @ 文档时，直接读文档全文，不走 RAG。
        多个文档合并，每个文档最多 3000 字，整体上限 10000 字；
        截断时先按段落/句号边界优先，避免破句。"""
        if not doc_ids:
            return ""
        from models import Document
        q = db.query(Document).filter(Document.id.in_(doc_ids))
        if tenant_id:
            q = q.filter(Document.tenant_id == tenant_id)
        docs = q.all()
        if not docs:
            return ""
        blocks = []
        total = 0
        per_doc_limit = 3000
        overall_limit = 10000
        for d in docs:
            text = (d.content or "").strip()
            if not text:
                continue
            remaining = overall_limit - total
            if remaining <= 0:
                break
            chunk_limit = min(per_doc_limit, remaining)
            snippet = self._truncate_by_boundary(text, chunk_limit)
            if not snippet:
                continue
            blocks.append(f"【{d.name}】\n{snippet}")
            total += len(snippet)
        return "\n\n".join(blocks)

    def _format_retrieval(self, results: list[dict]) -> str:
        return "\n\n".join([
            f"[{r['metadata'].get('creator_name', '') or r['metadata'].get('doc_name', '')}]\n{self._truncate_by_boundary(r['text'], 600)}"
            for r in results
        ])

    async def analyze_combined_style(
        self,
        db: Session,
        creator_ids: list[int],
        template_name: str,
        platform: str = "douyin",
        tenant_id: int = None,
    ) -> dict:
        """
        多博主联合风格分析
        提取多个博主的共同风格特征并生成融合风格模板
        """
        import json, asyncio
        from models import Creator, CreatorVideo

        if not creator_ids:
            raise ValueError("请至少选择一个博主")

        creators_info = []
        all_samples = []

        for cid in creator_ids:
            creator = db.query(Creator).filter(Creator.id == cid).first()
            if not creator:
                continue
            videos = db.query(CreatorVideo).filter(
                CreatorVideo.creator_id == cid,
                CreatorVideo.like_count > 500
            ).order_by(CreatorVideo.like_count.desc()).limit(5).all()

            samples = [
                f"标题：{v.title}\n文案：{v.description}"
                for v in videos if v.description
            ][:3]

            if samples:
                creators_info.append(creator.nickname)
                all_samples.append(f"===== 博主：{creator.nickname} ({creator.platform}) =====\n" + "\n\n".join(samples))

        if not all_samples:
            raise ValueError("选中的博主没有足够的视频数据，请先抓取内容")

        combined_samples = "\n\n".join(all_samples)
        num_creators = len(creators_info)
        creators_str = "、".join(creators_info)

        analysis_prompt = f"""分析以下来自 {num_creators} 位博主（{creators_str}）的短视频文案，提炼他们的共同风格特征，生成一套融合风格模板。

视频样本：
{combined_samples}

请综合分析这些博主的共同表达方式、语气、结构和技巧，以JSON格式返回融合风格模板：
{{
  "tone_description": "融合语气风格描述（30字以内，体现共同特点）",
  "structure_pattern": "内容结构描述（50字以内，综合多位博主的结构套路）",
  "hook_patterns": ["融合开头模式1", "融合开头模式2", "融合开头模式3"],
  "cta_patterns": ["融合结尾召唤1", "融合结尾召唤2"],
  "example_scripts": ["融合风格示例文案1"]
}}"""

        import json, asyncio

        loop = asyncio.get_event_loop()
        message = await loop.run_in_executor(
            None,
            lambda: self.client.messages.create(
                model=self.model_name,
                max_tokens=1200,
                messages=[{"role": "user", "content": analysis_prompt}]
            )
        )
        raw = message.content[0].text.strip().replace("```json", "").replace("```", "").strip()

        try:
            style_data = json.loads(raw)
        except Exception:
            raise ValueError("联合风格分析解析失败，请重试")

        # 创建融合风格模板（creator_id=None 表示多博主融合，按租户隔离）
        tmpl = StyleTemplate(
            creator_id=None,
            name=template_name,
            platform=platform,
            tenant_id=tenant_id,
            **style_data
        )
        db.add(tmpl)
        db.commit()
        db.refresh(tmpl)

        # 索引到向量库
        knowledge_service.index_style_template(db, tmpl.id)

        return {
            "template_id": tmpl.id,
            "name": tmpl.name,
            "platform": tmpl.platform,
            "source_creators": creators_info,
            **style_data,
        }


generator_service = GeneratorService()

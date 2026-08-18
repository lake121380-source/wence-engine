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
from config import settings


# ── system prompt：角色定义 + 平台规则 + 质量约束（不含用户输入） ──
SYSTEM_PROMPT = """你是一个真人短视频博主，不是AI助手。你写的每一句话都要像是自己真的经历过、真的想说的。

## 核心原则
1. **说人话**：想象你正在对着镜头跟一个朋友聊天，不要写"文案腔"
2. **一个核心点**：一条视频只讲透一件事，不要面面俱到
3. **有态度**：要有鲜明的观点和立场，不要两边讨好
4. **制造缺口**：开头制造信息缺口（好奇、共鸣、冲突），让人想听下去

## 绝对禁止
- AI味表达："在这个XXX的时代""不得不说""值得一提的是""让我们一起"
- 废话开头："你有没有想过""今天给大家分享""大家好，我是XXX"
- 堆砌感叹号（全文最多1个）
- 编造数据、虚假案例
- 说教语气："你应该""你必须""你一定要"
- 万能总结："所以说""总而言之""希望对你有帮助"

## 写作技巧
- 开头直接抛出一个让人"等一下，什么？"的信息点
- 用具体细节代替抽象概括（不说"很便宜"，说"9块9"）
- 每段只承载一个信息点，段落之间有逻辑递进
- 结尾要么留一个开放问题，要么给一句能记住的金句，不要硬塞行动号召
- 短句和长句交替使用，制造呼吸感

## 输出要求
直接输出可以拿去用的完整文案，从第一个字就是正文内容。
不要加"标题：""开头：""正文："等任何标签。
不要用 markdown 格式。
文案最后另起一行，用 # 号列出 3-5 个标签（如 #标签1 #标签2）。"""

# ── 平台专属风格指令 ──
PLATFORM_RULES = {
    "douyin": """【抖音】口播节奏，前3秒定生死
- 纯口语，像跟朋友面对面聊，允许语气词（"真的""就是说""你猜怎么着"）
- 短句为主，每句不超过15字，关键处用停顿或反问制造悬念
- 结构：钩子(3秒抓注意力)→展开(冲突/故事/干货)→收尾(金句或开放问题)
- 字数：150-300字（30-60秒口播）
- 引导评论比引导关注有效10倍""",

    "xiaohongshu": """【小红书】真实分享感，像在写给闺蜜的私信
- 第一人称真实体验视角，可以暴露不完美（"踩了3个月的坑"）
- 标题要有具体数字或对比反差（"月薪3千到3万｜我只改了这一点"）
- 正文用短段落，每段2-3句，段间空一行，emoji点缀但不堆砌
- 字数：200-500字（小红书用户习惯读长内容）
- 收藏引导（"先码后看"）比关注引导更自然""",

    "weixin": """【视频号】有深度有价值，像一个见多识广的朋友在分享见解
- 可以比抖音稍正式，但仍然是聊天而非演讲
- 允许适度铺垫，但开头仍然需要一个有力的观点或反常识信息
- 结构：观点/现象切入→案例拆解→深层分析→一句话总结
- 字数：200-400字
- 引导转发（"转给需要的朋友"）比点赞更适合视频号的社交裂变属性""",
}


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
        style_template_id: int = None,
        product_doc_ids: list[int] = None,
        creator_ids: list[int] = None,
        viewpoint_ids: list[int] = None,
        viral_analysis_ids: list[int] = None,
        tenant_id: int = None,
        history: list[dict] = None,
    ) -> dict:
        """
        主生成方法（五源RAG + 对话上下文）
        - history: 之前的对话轮次，用于多轮迭代
        - 只有用户显式引用素材时才加载对应 RAG 源，避免噪音
        """
        # ── 判断用户是否显式引用了素材（有引用才检索，没引用不自动塞） ──
        has_explicit_refs = bool(creator_ids or product_doc_ids or viewpoint_ids
                                or viral_analysis_ids or style_template_id)

        # 1. 获取风格上下文
        if style_template_id:
            style_context = self._get_style_context(db, style_template_id, topic, tenant_id=tenant_id)
        elif has_explicit_refs and creator_ids:
            # 有引用博主但没指定风格模板，尝试自动匹配
            style_context = self._get_style_context(db, None, topic, tenant_id=tenant_id)
        else:
            style_context = ""

        # 2. RAG：行业知识检索（仅在引用了博主时才检索）
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

        # 3. RAG：产品资料检索（仅在引用了文档时才检索）
        if product_doc_ids:
            product_results = knowledge_service.retrieve_product(topic, n=5, tenant_id=tenant_id)
            product_context = self._format_retrieval(product_results) if product_results else ""
        else:
            product_context = ""

        # 4. RAG：运营者观点检索（仅在引用了观点时才检索）
        if viewpoint_ids:
            viewpoint_context = self._get_viewpoint_context(db, topic, viewpoint_ids, tenant_id=tenant_id)
        else:
            viewpoint_context = ""

        # 5. 爆款分析注入（仅在引用了爆款时才检索）
        if viral_analysis_ids:
            viral_context = self._get_viral_context(db, viral_analysis_ids, tenant_id=tenant_id)
        else:
            viral_context = ""

        # 6. 组装 Prompt（system + user 分层）
        platform_rules = PLATFORM_RULES.get(platform, PLATFORM_RULES["douyin"])

        # 过滤掉空的参考素材段落，避免出现"暂无"噪音
        ref_sections = []
        if style_context:
            ref_sections.append(f"### 博主风格参考\n{style_context}")
        if industry_context:
            ref_sections.append(f"### 行业知识\n{industry_context}")
        if product_context:
            ref_sections.append(f"### 产品资料\n{product_context}")
        if viewpoint_context:
            ref_sections.append(f"### 运营者观点（请融入文案）\n{viewpoint_context}")
        if viral_context:
            ref_sections.append(f"### 爆款洞察（参考成功要素）\n{viral_context}")

        if ref_sections:
            refs_block = "## 参考素材（辅助提升质量，不能偏离我的要求）\n\n" + "\n\n".join(ref_sections)
        else:
            refs_block = ""

        user_prompt = f"""## 我的创作要求（请严格按此执行）
{topic}

## 目标平台特征
{platform_rules}

{refs_block}"""

        # 保存完整 prompt 用于审计
        prompt = f"[SYSTEM]\n{SYSTEM_PROMPT}\n\n[USER]\n{user_prompt}"

        # 7. 构建对话消息列表（支持多轮迭代）
        ai_messages = self._build_messages(history, user_prompt)

        loop = asyncio.get_event_loop()
        message = await loop.run_in_executor(
            None,
            lambda: self.client.messages.create(
                model=self.model_name,
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                messages=ai_messages,
            )
        )
        raw_output = message.content[0].text.strip()

        # 8. 解析 JSON
        output = self._parse_output(raw_output)

        # 9. 保存记录（补全 creator_ids / viewpoint_ids / viral_analysis_ids）
        gen = Generation(
            topic=topic,
            platform=platform,
            style_template_id=style_template_id,
            product_doc_ids=product_doc_ids or [],
            creator_ids=creator_ids or [],
            viewpoint_ids=viewpoint_ids or [],
            viral_analysis_ids=viral_analysis_ids or [],
            prompt_used=prompt,
            output_title=output.get("title", ""),
            output_hook=output.get("hook", ""),
            output_body=output.get("body", ""),
            output_cta=output.get("cta", ""),
            output_full=raw_output,
        )
        db.add(gen)
        db.commit()
        db.refresh(gen)

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

    @staticmethod
    def _parse_output(raw_output: str) -> dict:
        """从 LLM 原始输出中解析纯文本文案 + 标签"""
        text = raw_output.strip()
        tags = []
        # 提取末尾的 #标签
        lines = text.split('\n')
        content_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and all(part.startswith('#') for part in stripped.split() if part):
                # 这行全是 #标签
                tags.extend([t.lstrip('#').strip() for t in stripped.split() if t.startswith('#') and len(t) > 1])
            else:
                content_lines.append(line)
        # 去掉末尾空行
        while content_lines and not content_lines[-1].strip():
            content_lines.pop()
        body = '\n'.join(content_lines).strip()
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
        style_template_id: int = None,
        product_doc_ids: list[int] = None,
        creator_ids: list[int] = None,
        viewpoint_ids: list[int] = None,
        viral_analysis_ids: list[int] = None,
        tenant_id: int = None,
        history: list[dict] = None,
    ) -> AsyncGenerator[str, None]:
        """
        流式生成方法，yield SSE 格式的 text chunk。
        最后 yield 一条 event:done 包含完整解析结果 + generation id。
        """
        # ── 复用 generate 里的 RAG 上下文构建逻辑 ──
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
            product_results = knowledge_service.retrieve_product(topic, n=5, tenant_id=tenant_id)
            product_context = self._format_retrieval(product_results) if product_results else ""
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

        platform_rules = PLATFORM_RULES.get(platform, PLATFORM_RULES["douyin"])
        ref_sections = []
        if style_context:
            ref_sections.append(f"### 博主风格参考\n{style_context}")
        if industry_context:
            ref_sections.append(f"### 行业知识\n{industry_context}")
        if product_context:
            ref_sections.append(f"### 产品资料\n{product_context}")
        if viewpoint_context:
            ref_sections.append(f"### 运营者观点（请融入文案）\n{viewpoint_context}")
        if viral_context:
            ref_sections.append(f"### 爆款洞察（参考成功要素）\n{viral_context}")

        refs_block = ("## 参考素材（辅助提升质量，不能偏离我的要求）\n\n" + "\n\n".join(ref_sections)) if ref_sections else ""

        user_prompt = f"""## 我的创作要求（请严格按此执行）
{topic}

## 目标平台特征
{platform_rules}

{refs_block}"""

        prompt = f"[SYSTEM]\n{SYSTEM_PROMPT}\n\n[USER]\n{user_prompt}"
        ai_messages = self._build_messages(history, user_prompt)

        # ── 流式调用 LLM ──
        raw_chunks = []

        def _stream_sync():
            """在线程中同步流式读取"""
            collected = []
            with self.client.messages.stream(
                model=self.model_name,
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                messages=ai_messages,
            ) as stream:
                for text in stream.text_stream:
                    collected.append(text)
                    yield text
            return collected

        loop = asyncio.get_event_loop()
        import queue, threading
        q: queue.Queue = queue.Queue()

        def _run():
            try:
                collected = []
                with self.client.messages.stream(
                    model=self.model_name,
                    max_tokens=2000,
                    system=SYSTEM_PROMPT,
                    messages=ai_messages,
                ) as stream:
                    for text in stream.text_stream:
                        collected.append(text)
                        q.put(("chunk", text))
                q.put(("done", collected))
            except Exception as e:
                q.put(("error", str(e)))

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        all_chunks = []
        while True:
            # non-blocking poll with short sleep
            try:
                kind, data = await loop.run_in_executor(None, lambda: q.get(timeout=0.1))
            except Exception:
                continue
            if kind == "chunk":
                all_chunks.append(data)
                # SSE: data line
                escaped = json.dumps(data, ensure_ascii=False)
                yield f"data: {escaped}\n\n"
            elif kind == "done":
                all_chunks = data
                break
            elif kind == "error":
                yield f"event: error\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                return

        # ── 解析 & 保存 ──
        raw_output = "".join(all_chunks).strip()
        output = self._parse_output(raw_output)

        gen = Generation(
            topic=topic,
            platform=platform,
            style_template_id=style_template_id,
            product_doc_ids=product_doc_ids or [],
            creator_ids=creator_ids or [],
            viewpoint_ids=viewpoint_ids or [],
            viral_analysis_ids=viral_analysis_ids or [],
            prompt_used=prompt,
            output_title=output.get("title", ""),
            output_hook=output.get("hook", ""),
            output_body=output.get("body", ""),
            output_cta=output.get("cta", ""),
            output_full=raw_output,
        )
        db.add(gen)
        db.commit()
        db.refresh(gen)

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
        ).order_by(CreatorVideo.like_count.desc()).limit(20).all()

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
        await knowledge_service.index_style_template(db, tmpl.id)

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

        parts = [f"风格：{tmpl.tone_description or ''}"]
        if tmpl.structure_pattern:
            parts.append(f"结构：{tmpl.structure_pattern}")
        if tmpl.content_formula:
            parts.append(f"爆款公式：{tmpl.content_formula}")
        if tmpl.vocabulary_style:
            parts.append(f"用词特征：{tmpl.vocabulary_style}")
        if tmpl.hook_patterns:
            parts.append(f"开头示例：{tmpl.hook_patterns[0]}")
        if tmpl.cta_patterns:
            parts.append(f"结尾示例：{tmpl.cta_patterns[0]}")
        if tmpl.example_scripts:
            parts.append(f"参考文案：{tmpl.example_scripts[0][:200]}")
        return "\n".join(parts)

    def _get_viewpoint_context(self, db: Session, topic: str, viewpoint_ids: list[int] = None, tenant_id: int = None) -> str:
        """获取运营者观点上下文（第4源）"""
        from models import OperatorViewpoint
        lines = []
        if viewpoint_ids:
            vps = db.query(OperatorViewpoint).filter(
                OperatorViewpoint.id.in_(viewpoint_ids),
                OperatorViewpoint.is_active == True,
                OperatorViewpoint.tenant_id == tenant_id,
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
            lines.append(
                f"参考爆款「{title[:30]}」：\n"
                f"- 共鸣点：{(a.resonance_analysis or '')[:80]}\n"
                f"- 讨论钩子：{(a.discussion_analysis or '')[:80]}\n"
                f"- 爆款总结：{(a.why_viral_summary or '')[:100]}"
            )
        return "\n\n".join(lines) if lines else "暂无爆款分析数据"

    def _format_retrieval(self, results: list[dict]) -> str:
        return "\n\n".join([
            f"[{r['metadata'].get('creator_name', '') or r['metadata'].get('doc_name', '')}]\n{r['text'][:300]}"
            for r in results
        ])

    def _platform_label(self, platform: str) -> str:
        labels = {
            "douyin": "抖音（15-60秒竖屏短视频）",
            "xiaohongshu": "小红书（图文/短视频笔记）",
            "weixin": "视频号（短视频）",
            "weixin": "微信视频号",
        }
        return labels.get(platform, platform)

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
        await knowledge_service.index_style_template(db, tmpl.id)

        return {
            "template_id": tmpl.id,
            "name": tmpl.name,
            "platform": tmpl.platform,
            "source_creators": creators_info,
            **style_data,
        }


generator_service = GeneratorService()

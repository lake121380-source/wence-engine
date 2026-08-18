"""
知识库服务
- 博主视频内容向量化
- 产品资料解析 + 向量化
- RAG 检索接口
"""
import os
import hashlib
from pathlib import Path
from sqlalchemy.orm import Session
import chromadb
from chromadb.utils import embedding_functions
from models import Creator, CreatorVideo, Document, StyleTemplate
from config import settings


class KnowledgeService:
    def __init__(self):
        # 懒加载：避免服务启动时卡在 ChromaDB Rust 初始化
        self._initialized = False
        self.client = None
        self.ef = None
        self.industry_col = None
        self.product_col = None
        self.style_col = None
        self.viewpoint_col = None

    def _ensure_initialized(self):
        if self._initialized:
            return
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        self.industry_col = self.client.get_or_create_collection(
            name="industry_knowledge",
            embedding_function=self.ef,
            metadata={"description": "行业博主观点与内容"}
        )
        self.product_col = self.client.get_or_create_collection(
            name="product_knowledge",
            embedding_function=self.ef,
            metadata={"description": "产品资料文档"}
        )
        self.style_col = self.client.get_or_create_collection(
            name="style_knowledge",
            embedding_function=self.ef,
            metadata={"description": "博主风格样本"}
        )
        self.viewpoint_col = self.client.get_or_create_collection(
            name="operator_viewpoints",
            embedding_function=self.ef,
            metadata={"description": "运营者观点库"}
        )
        self._initialized = True

    # ─── 博主视频索引 ─────────────────────────────────────────
    async def index_creator_videos(self, db: Session, creator_id: int):
        """将博主未索引的视频入向量库"""
        self._ensure_initialized()
        creator = db.query(Creator).filter(Creator.id == creator_id).first()
        videos = db.query(CreatorVideo).filter(
            CreatorVideo.creator_id == creator_id,
            CreatorVideo.indexed == False,
            CreatorVideo.description != None,
            CreatorVideo.description != ""
        ).all()

        if not videos:
            return 0

        docs, metas, ids = [], [], []
        for v in videos:
            text = f"{v.title}\n{v.description}"
            if v.tags:
                text += f"\n标签：{' '.join(v.tags)}"
            doc_id = f"video_{v.id}"
            docs.append(text)
            metas.append({
                "creator_id": str(creator_id),
                "creator_name": creator.nickname or "",
                "platform": v.platform or "",
                "video_id": v.video_id or "",
                "like_count": v.like_count or 0,
                "play_count": v.play_count or 0,
                "type": "industry_video",
                # 共享博主模型下不再用 creator.tenant_id 做隔离，改由 creator_id 过滤
            })
            ids.append(doc_id)

        # 批量 upsert
        batch_size = 50
        for i in range(0, len(docs), batch_size):
            self.industry_col.upsert(
                documents=docs[i:i+batch_size],
                metadatas=metas[i:i+batch_size],
                ids=ids[i:i+batch_size]
            )

        # 标记已索引
        for v in videos:
            v.indexed = True
        db.commit()
        return len(videos)

    # ─── 产品文档处理 ─────────────────────────────────────────
    async def process_document(self, db: Session, doc_id: int):
        """解析文档文本并入向量库"""
        self._ensure_initialized()
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc or not doc.file_path:
            return

        text = self._extract_text(doc.file_path, doc.file_type)
        doc.content = text
        chunks = self._chunk_text(text)
        doc.chunk_count = len(chunks)

        chunk_docs, chunk_metas, chunk_ids = [], [], []
        for i, chunk in enumerate(chunks):
            chunk_docs.append(chunk)
            chunk_metas.append({
                "doc_id": str(doc_id),
                "doc_name": doc.name,
                "chunk_index": i,
                "type": "product_doc",
                "tenant_id": str(doc.tenant_id or 0),
            })
            chunk_ids.append(f"doc_{doc_id}_chunk_{i}")

        if chunk_docs:
            self.product_col.upsert(
                documents=chunk_docs,
                metadatas=chunk_metas,
                ids=chunk_ids
            )

        doc.indexed = True
        db.commit()
        return len(chunks)

    async def process_text(self, db: Session, doc_id: int, text: str):
        """直接将文本内容入向量库（来自博主视频文案、爆款选题等）"""
        self._ensure_initialized()
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc or not text.strip():
            return 0

        doc.content = text
        chunks = self._chunk_text(text)
        doc.chunk_count = len(chunks)

        chunk_docs, chunk_metas, chunk_ids = [], [], []
        for i, chunk in enumerate(chunks):
            chunk_docs.append(chunk)
            chunk_metas.append({
                "doc_id": str(doc_id),
                "doc_name": doc.name,
                "chunk_index": i,
                "type": "product_doc",
                "tenant_id": str(doc.tenant_id or 0),
            })
            chunk_ids.append(f"doc_{doc_id}_chunk_{i}")

        if chunk_docs:
            self.product_col.upsert(
                documents=chunk_docs,
                metadatas=chunk_metas,
                ids=chunk_ids
            )

        doc.indexed = True
        db.commit()
        return len(chunks)

    # ─── 风格模版索引 ─────────────────────────────────────────
    async def index_style_template(self, db: Session, template_id: int):
        """将风格模版入向量库"""
        self._ensure_initialized()
        tmpl = db.query(StyleTemplate).filter(StyleTemplate.id == template_id).first()
        if not tmpl:
            return

        text_parts = [f"风格名：{tmpl.name}"]
        if tmpl.tone_description:
            text_parts.append(f"语气：{tmpl.tone_description}")
        if tmpl.structure_pattern:
            text_parts.append(f"结构：{tmpl.structure_pattern}")
        if tmpl.hook_patterns:
            text_parts.append(f"开头钩子示例：{'；'.join(tmpl.hook_patterns[:3])}")
        if tmpl.example_scripts:
            text_parts.append(f"文案示例：{tmpl.example_scripts[0][:200]}")

        self.style_col.upsert(
            documents=["\n".join(text_parts)],
            metadatas=[{"template_id": str(template_id), "name": tmpl.name, "platform": tmpl.platform or "", "tenant_id": str(tmpl.tenant_id or 0)}],
            ids=[f"style_{template_id}"]
        )

    # ─── RAG 检索 ─────────────────────────────────────────────
    def retrieve_industry(self, query: str, n: int = 5, creator_id: int = None, tenant_id: int = None, creator_id_list: list = None) -> list[dict]:
        """
        检索行业博主视频内容。
        - creator_id: 指定单个博主
        - creator_id_list: 指定多个博主（当前租户订阅的所有博主）
        - tenant_id: 旧参数，保留兼容，共享博主模型下通常不用
        """
        self._ensure_initialized()
        count = self.industry_col.count()
        if count == 0:
            return []
        where = {"type": "industry_video"}
        if creator_id:
            where["creator_id"] = str(creator_id)
        elif creator_id_list:
            # 按订阅博主列表过滤（共享博主模型下替代 tenant_id 过滤）
            if not creator_id_list:
                return []
            where = {"$and": [{"type": "industry_video"}, {"creator_id": {"$in": [str(c) for c in creator_id_list]}}]}
        elif tenant_id:
            where["tenant_id"] = str(tenant_id)
        else:
            return []  # 没有任何过滤条件时拒绝返回，防止跨租户泄漏
        try:
            results = self.industry_col.query(
                query_texts=[query],
                n_results=min(n, count),
                where=where,
            )
            return self._format_results(results)
        except Exception:
            return []

    def retrieve_product(self, query: str, n: int = 5, tenant_id: int = None) -> list[dict]:
        self._ensure_initialized()
        try:
            count = self.product_col.count()
            if count == 0:
                return []
            if not tenant_id:
                return []  # 必须指定租户，防止跨租户泄漏
            where = {"tenant_id": str(tenant_id)}
            results = self.product_col.query(
                query_texts=[query],
                n_results=min(n, count),
                where=where,
            )
            return self._format_results(results)
        except Exception:
            return []

    def retrieve_style(self, query: str, n: int = 3, tenant_id: int = None) -> list[dict]:
        self._ensure_initialized()
        try:
            count = self.style_col.count()
            if count == 0:
                return []
            if not tenant_id:
                return []  # 必须指定租户，防止跨租户泄漏
            where = {"tenant_id": str(tenant_id)}
            results = self.style_col.query(
                query_texts=[query],
                n_results=min(n, count),
                where=where,
            )
            return self._format_results(results)
        except Exception:
            return []

    # ─── 运营者观点 ──────────────────────────────────────────
    def index_viewpoint(self, viewpoint_id: int, title: str, content: str, category: str, tags: str, tenant_id: int = 0):
        """将运营者观点入向量库"""
        self._ensure_initialized()
        text = f"【{category}】{title}\n{content}"
        self.viewpoint_col.upsert(
            documents=[text],
            metadatas=[{
                "viewpoint_id": str(viewpoint_id),
                "title": title,
                "category": category,
                "tags": tags or "",
                "tenant_id": str(tenant_id or 0),
            }],
            ids=[f"viewpoint_{viewpoint_id}"]
        )

    def delete_viewpoint(self, viewpoint_id: int):
        """从向量库删除观点"""
        self._ensure_initialized()
        try:
            self.viewpoint_col.delete(ids=[f"viewpoint_{viewpoint_id}"])
        except Exception:
            pass

    def retrieve_viewpoints(self, query: str, n: int = 5, tenant_id: int = None) -> list[dict]:
        """检索相关运营者观点"""
        self._ensure_initialized()
        try:
            count = self.viewpoint_col.count()
            if count == 0:
                return []
            if not tenant_id:
                return []  # 必须指定租户，防止跨租户泄漏
            where = {"tenant_id": str(tenant_id)}
            results = self.viewpoint_col.query(
                query_texts=[query],
                n_results=min(n, count),
                where=where,
            )
            return self._format_results(results)
        except Exception:
            return []

    def get_stats(self) -> dict:
        self._ensure_initialized()
        return {
            "industry_docs": self.industry_col.count(),
            "product_docs": self.product_col.count(),
            "style_docs": self.style_col.count(),
            "viewpoint_docs": self.viewpoint_col.count(),
        }

    # ─── 私有方法 ─────────────────────────────────────────────
    def _extract_text(self, file_path: str, file_type: str) -> str:
        try:
            if file_type == "pdf":
                import fitz
                doc = fitz.open(file_path)
                return "\n".join(page.get_text() for page in doc)
            elif file_type in ("docx", "doc"):
                from docx import Document as DocxDoc
                doc = DocxDoc(file_path)
                return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            elif file_type == "txt":
                return Path(file_path).read_text(encoding="utf-8", errors="ignore")
            else:
                return Path(file_path).read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"[Knowledge] extract_text error: {e}")
            return ""

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        if not text:
            return []
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - overlap
        return chunks

    def _format_results(self, results: dict) -> list[dict]:
        out = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        for doc, meta, dist in zip(docs, metas, distances):
            out.append({"text": doc, "metadata": meta, "score": round(1 - dist, 4)})
        return out


knowledge_service = KnowledgeService()

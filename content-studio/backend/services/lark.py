"""
飞书多维表格（Bitable）集成服务
- 自动获取 tenant_access_token
- 创建 / 查找多维表格 App 和数据表
- 批量写入选题数据
"""
import httpx
import time
from config import settings

FEISHU_BASE = "https://open.feishu.cn/open-apis"

# 选题表字段定义（飞书字段类型：1=文本 2=数字 3=单选 11=复选 15=URL 17=关联 999=自动编号）
TOPIC_TABLE_FIELDS = [
    {"field_name": "选题标题", "type": 1},           # 文本
    {"field_name": "关键词",   "type": 1},
    {"field_name": "平台",     "type": 3,            # 单选
     "property": {"options": [
         {"name": "抖音"}, {"name": "小红书"}, {"name": "B站"}
     ]}},
    {"field_name": "点赞数",   "type": 2},           # 数字
    {"field_name": "评论数",   "type": 2},
    {"field_name": "播放量",   "type": 2},
    {"field_name": "原视频作者", "type": 1},
    {"field_name": "视频标签", "type": 1},
    {"field_name": "视频链接", "type": 15},          # URL
    {"field_name": "封面图片", "type": 1},
    {"field_name": "状态",     "type": 3,            # 单选
     "property": {"options": [
         {"name": "待评审"}, {"name": "已采纳"}, {"name": "已使用"}, {"name": "已忽略"}
     ]}},
    {"field_name": "抓取时间", "type": 5},           # 日期时间
]


class LarkBitableService:
    def __init__(self):
        self._token: str | None = None
        self._token_expires: float = 0

    # ─── Auth ──────────────────────────────────────────────
    async def _get_token(self) -> str:
        """获取 tenant_access_token，有缓存（有效期 2 小时）"""
        if self._token and time.time() < self._token_expires - 60:
            return self._token

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{FEISHU_BASE}/auth/v3/tenant_access_token/internal",
                json={"app_id": settings.lark_app_id, "app_secret": settings.lark_app_secret},
            )
            resp.raise_for_status()
            data = resp.json()

        if data.get("code") != 0:
            raise RuntimeError(f"飞书获取 Token 失败: {data.get('msg')}")

        self._token = data["tenant_access_token"]
        self._token_expires = time.time() + data.get("expire", 7200)
        return self._token

    def _headers(self, token: str) -> dict:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    # ─── App 管理 ───────────────────────────────────────────
    async def create_bitable_app(self, name: str, folder_token: str = "") -> dict:
        """创建多维表格 App，返回 {app_token, url}"""
        token = await self._get_token()
        payload = {"name": name}
        if folder_token:
            payload["folder_token"] = folder_token

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{FEISHU_BASE}/bitable/v1/apps",
                headers=self._headers(token),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        if data.get("code") != 0:
            raise RuntimeError(f"创建多维表格失败: {data.get('msg')}")
        return data["data"]["app"]

    # ─── 表管理 ─────────────────────────────────────────────
    async def create_table(self, app_token: str, table_name: str, fields: list[dict] | None = None) -> str:
        """在 App 里创建数据表，返回 table_id"""
        token = await self._get_token()
        payload: dict = {"table": {"name": table_name}}
        if fields:
            payload["table"]["fields"] = fields

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{FEISHU_BASE}/bitable/v1/apps/{app_token}/tables",
                headers=self._headers(token),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        if data.get("code") != 0:
            raise RuntimeError(f"创建数据表失败: {data.get('msg')}")
        return data["data"]["table_id"]

    async def list_tables(self, app_token: str) -> list[dict]:
        """列出 App 中所有数据表"""
        token = await self._get_token()
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{FEISHU_BASE}/bitable/v1/apps/{app_token}/tables",
                headers=self._headers(token),
            )
            resp.raise_for_status()
            data = resp.json()
        return data.get("data", {}).get("items", [])

    async def ensure_topic_table(self, app_token: str, table_name: str = "爆款选题库") -> str:
        """确保选题表存在，若不存在则创建；返回 table_id"""
        tables = await self.list_tables(app_token)
        for t in tables:
            if t.get("name") == table_name:
                return t["table_id"]
        return await self.create_table(app_token, table_name, TOPIC_TABLE_FIELDS)

    # ─── 记录写入 ────────────────────────────────────────────
    async def batch_create_records(self, app_token: str, table_id: str, records: list[dict]) -> int:
        """
        批量新建记录（每批最多 500 条）
        records: [{"fields": {...}}, ...]
        返回写入成功条数
        """
        token = await self._get_token()
        total = 0
        batch_size = 500
        for i in range(0, len(records), batch_size):
            batch = records[i: i + batch_size]
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{FEISHU_BASE}/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create",
                    headers=self._headers(token),
                    json={"records": batch},
                )
                resp.raise_for_status()
                data = resp.json()
            if data.get("code") != 0:
                raise RuntimeError(f"批量写入记录失败: {data.get('msg')}")
            total += len(data.get("data", {}).get("records", []))
        return total

    async def sync_topics_to_feishu(
        self, topics: list[dict], app_token: str, table_name: str = "爆款选题库",
        table_id: str = None,
    ) -> dict:
        """
        将选题列表同步到飞书多维表格
        - 若传入 table_id：直接写入该已有数据表
        - 若未传入 table_id：通过 table_name 查找或自动创建
        topics: 来自 topic_hunter 的标准结构
        返回 {table_id, written, url}
        """
        if table_id:
            # 写入已有表格，直接用传入的 table_id
            resolved_table_id = table_id
        else:
            resolved_table_id = await self.ensure_topic_table(app_token, table_name)

        records = []
        for t in topics:
            video_url = _build_video_url(t.get("platform", ""), t.get("video_id", ""))
            records.append({"fields": {
                "选题标题":    t.get("title", ""),
                "关键词":      t.get("keyword", ""),
                "平台":        _platform_zh(t.get("platform", "")),
                "点赞数":      t.get("like_count", 0),
                "评论数":      t.get("comment_count", 0),
                "播放量":      t.get("play_count", 0),
                "原视频作者":  t.get("author", ""),
                "视频标签":    ", ".join(t.get("tags", [])),
                "视频链接":    {"link": video_url, "text": "查看原视频"} if video_url else {},
                "封面图片":    t.get("cover_url", ""),
                "状态":        "待评审",
                "抓取时间":    int(time.time() * 1000),  # 毫秒时间戳
            }})

        written = await self.batch_create_records(app_token, resolved_table_id, records)
        url = f"https://feishu.cn/base/{app_token}?table={resolved_table_id}"
        return {"table_id": resolved_table_id, "written": written, "url": url}

    async def list_table_fields(self, app_token: str, table_id: str) -> list[dict]:
        """获取指定数据表的所有字段列表"""
        token = await self._get_token()
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{FEISHU_BASE}/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
                headers=self._headers(token),
            )
            resp.raise_for_status()
            data = resp.json()
        return data.get("data", {}).get("items", [])

    async def read_table_records(
        self,
        app_token: str,
        table_id: str,
        keyword_field: str = "关键词",
        max_records: int = 200,
    ) -> list[str]:
        """
        读取飞书数据表中的关键词列，返回去重后的关键词列表
        用于从飞书表格拉取关键词自动触发爬取
        """
        token = await self._get_token()
        keywords = []
        page_token = None

        while len(keywords) < max_records:
            params: dict = {"page_size": 100}
            if page_token:
                params["page_token"] = page_token

            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(
                    f"{FEISHU_BASE}/bitable/v1/apps/{app_token}/tables/{table_id}/records",
                    headers=self._headers(token),
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()

            if data.get("code") != 0:
                raise RuntimeError(f"读取飞书记录失败: {data.get('msg')}")

            items = data.get("data", {}).get("items", [])
            for item in items:
                fields = item.get("fields", {})
                kw_val = fields.get(keyword_field, "")
                # 字段值可能是字符串或列表
                if isinstance(kw_val, list):
                    for seg in kw_val:
                        if isinstance(seg, dict):
                            kw_val = seg.get("text", "")
                        elif isinstance(seg, str):
                            kw_val = seg
                        break
                if kw_val and isinstance(kw_val, str) and kw_val.strip():
                    keywords.append(kw_val.strip())

            has_more = data.get("data", {}).get("has_more", False)
            page_token = data.get("data", {}).get("page_token")
            if not has_more or not page_token:
                break

        # 去重保留顺序
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        return unique_keywords


# ─── 工具函数 ─────────────────────────────────────────────────
def _platform_zh(platform: str) -> str:
    return {"douyin": "抖音", "xiaohongshu": "小红书", "weixin": "视频号"}.get(platform, platform)


def _build_video_url(platform: str, video_id: str) -> str:
    if not video_id:
        return ""
    if platform == "douyin":
        return f"https://www.douyin.com/video/{video_id}"
    if platform == "xiaohongshu":
        return f"https://www.xiaohongshu.com/explore/{video_id}"
    if platform == "weixin":
        return f"https://channels.weixin.qq.com/platform/post/detail?id={video_id}"
    return ""


lark_service = LarkBitableService()

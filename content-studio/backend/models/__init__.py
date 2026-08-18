from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Creator(Base):
    """博主档案"""
    __tablename__ = "creators"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    platform = Column(String(20), nullable=False)        # douyin / xiaohongshu / weixin
    platform_id = Column(String(100), nullable=False)    # 平台唯一ID (sec_user_id / uid etc.)
    unique_id = Column(String(100))                      # 抖音号 / 小红书号
    nickname = Column(String(200))
    avatar_url = Column(String(500))
    follower_count = Column(Integer, default=0)
    video_count = Column(Integer, default=0)
    bio = Column(Text)
    tags = Column(JSON, default=list)                    # 行业标签
    is_active = Column(Boolean, default=True)
    last_crawled_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    videos = relationship("CreatorVideo", back_populates="creator", cascade="all, delete-orphan")
    style_templates = relationship("StyleTemplate", back_populates="creator")
    tenant_subscriptions = relationship("TenantCreator", back_populates="creator", cascade="all, delete-orphan")


class TenantCreator(Base):
    """租户-博主订阅关系（多租户共享博主数据的关联表）"""
    __tablename__ = "tenant_creators"
    __table_args__ = (UniqueConstraint("tenant_id", "creator_id", name="uq_tenant_creator"),)

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False, index=True)
    added_at = Column(DateTime, default=datetime.utcnow)

    creator = relationship("Creator", back_populates="tenant_subscriptions")


class CreatorVideo(Base):
    """博主视频内容"""
    __tablename__ = "creator_videos"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False)
    platform = Column(String(20))
    video_id = Column(String(100), unique=True)
    title = Column(Text)
    description = Column(Text)
    cover_url = Column(String(500))
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    play_count = Column(Integer, default=0)
    duration = Column(Integer)                           # 秒
    tags = Column(JSON, default=list)
    published_at = Column(DateTime)
    raw_data = Column(JSON)                              # 原始 API 数据
    indexed = Column(Boolean, default=False)             # 是否已入向量库
    created_at = Column(DateTime, default=datetime.utcnow)

    collect_count = Column(Integer, default=0)          # 收藏数（抖音/B站）
    like_play_ratio = Column(Float, nullable=True)       # 点赞/播放 互动比
    comment_play_ratio = Column(Float, nullable=True)    # 评论/播放 互动比
    collect_play_ratio = Column(Float, nullable=True)    # 收藏/播放 互动比
    script = Column(Text)                                # 视频语音转录文案
    top_comments = Column(JSON, default=list)            # 热门评论 [{nickname, content, likes}]
    video_url = Column(String(500))                      # 原始视频/播放链接

    creator = relationship("Creator", back_populates="videos")


class CreatorIntelCard(Base):
    """博主情报卡（四维度AI分析），按租户隔离"""
    __tablename__ = "creator_intel_cards"
    __table_args__ = (UniqueConstraint("tenant_id", "creator_id", name="uq_tenant_intel_card"),)

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    positioning = Column(Text)                           # 账号定位分析
    video_style = Column(Text)                           # 视频风格特征
    common_topics = Column(JSON, default=list)           # 常用话题列表
    comment_pain_points = Column(JSON, default=list)     # 评论区痛点挖掘
    summary = Column(Text)                               # 综合情报摘要
    raw_analysis = Column(Text)                          # AI原始分析JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = relationship("Creator", backref="intel_cards")


class OperatorViewpoint(Base):
    """运营者观点库"""
    __tablename__ = "operator_viewpoints"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String(200), nullable=False)          # 观点标题
    category = Column(String(50), default="行业立场")    # 行业立场 / 价值观 / 差异化角度
    content = Column(Text, nullable=False)               # 观点详细内容
    tags = Column(String(500), default="")               # 标签，逗号分隔
    is_active = Column(Boolean, default=True)
    indexed = Column(Boolean, default=False)             # 是否已入向量库
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VideoAnalysis(Base):
    """视频爆款分析（三互动比 + AI诊断），按租户隔离"""
    __tablename__ = "video_analyses"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    video_id = Column(Integer, ForeignKey("creator_videos.id"), nullable=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    like_play_ratio = Column(Float, default=0.0)
    comment_play_ratio = Column(Float, default=0.0)
    collect_play_ratio = Column(Float, default=0.0)
    resonance_analysis = Column(Text)                    # 点赞/播放 → 观点共鸣/金句分析
    discussion_analysis = Column(Text)                   # 评论/播放 → 争议点/讨论钩子
    value_analysis = Column(Text)                        # 收藏/播放 → 干货/知识价值分析
    why_viral_summary = Column(Text)                     # "为什么爆"综合图谱
    raw_data = Column(JSON)                              # 原始输入数据快照
    created_at = Column(DateTime, default=datetime.utcnow)

    video = relationship("CreatorVideo", backref="analysis", uselist=False, foreign_keys=[video_id])
    topic = relationship("Topic", backref="analysis", uselist=False, foreign_keys=[topic_id])


class Document(Base):
    """产品资料文档"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    name = Column(String(200), nullable=False)
    file_type = Column(String(20))                       # pdf / docx / txt / image / text
    file_path = Column(String(500))
    content = Column(Text)                               # 提取的文本
    chunk_count = Column(Integer, default=0)             # 向量库分块数
    indexed = Column(Boolean, default=False)
    tags = Column(JSON, default=list)
    folder_name = Column(String(100), nullable=True)     # 文件夹分类
    source_type = Column(String(20), nullable=True)      # creator_video / topic / upload
    source_ref = Column(String(200), nullable=True)      # 来源引用（视频ID等）
    created_at = Column(DateTime, default=datetime.utcnow)


class StyleTemplate(Base):
    """博主风格模版"""
    __tablename__ = "style_templates"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=True)
    name = Column(String(200), nullable=False)
    platform = Column(String(20))
    hook_patterns = Column(JSON, default=list)           # 开头钩子模式列表
    structure_pattern = Column(Text)                     # 整体结构描述
    tone_description = Column(Text)                      # 语气风格描述
    example_scripts = Column(JSON, default=list)         # 示例文案片段
    cta_patterns = Column(JSON, default=list)            # 结尾CTA模式
    content_formula = Column(Text)                       # 爆款内容公式
    vocabulary_style = Column(Text)                      # 用词特征
    avg_duration = Column(Integer)                       # 平均时长（秒）
    content_type = Column(String(50), nullable=True)     # 内容类型：产品种草/知识分享/观点输出/故事叙述/认知觉醒
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = relationship("Creator", back_populates="style_templates")


class Generation(Base):
    """文案生成记录"""
    __tablename__ = "generations"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    topic = Column(Text, nullable=False)                 # 选题
    platform = Column(String(20))
    style_template_id = Column(Integer, ForeignKey("style_templates.id"), nullable=True)
    product_doc_ids = Column(JSON, default=list)         # 关联的产品资料ID列表
    creator_ids = Column(JSON, default=list)             # 关联的博主ID列表
    viewpoint_ids = Column(JSON, default=list)           # 关联的观点ID列表
    viral_analysis_ids = Column(JSON, default=list)      # 关联的爆款分析ID列表
    prompt_used = Column(Text)                           # 实际使用的 prompt
    output_title = Column(Text)
    output_hook = Column(Text)
    output_body = Column(Text)
    output_cta = Column(Text)
    output_full = Column(Text)
    rating = Column(Integer)                             # 用户评分 1-5
    created_at = Column(DateTime, default=datetime.utcnow)


class Topic(Base):
    """爆款选题（来自关键词搜索或手动添加）"""
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    keyword = Column(String(200))                        # 搜索关键词
    platform = Column(String(20))                        # douyin / xiaohongshu / weixin
    video_id = Column(String(100))                       # 平台视频 ID
    title = Column(Text)                                 # 视频标题 / 选题
    description = Column(Text)
    author = Column(String(200))
    author_id = Column(String(100))
    cover_url = Column(String(500))
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    play_count = Column(Integer, default=0)
    collect_count = Column(Integer, default=0)           # 收藏数
    tags = Column(JSON, default=list)
    status = Column(String(20), default="待评审")        # 待评审 / 已采纳 / 已使用 / 已忽略
    feishu_synced = Column(Boolean, default=False)       # 是否已同步飞书
    feishu_app_token = Column(String(200))
    feishu_table_id = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

    # ── 新增：作者信息 ──
    author_unique_id = Column(String(100))               # 抖音号等
    author_avatar = Column(String(500))                  # 作者头像
    author_follower_count = Column(Integer, default=0)   # 作者粉丝数
    author_bio = Column(Text)                            # 作者简介
    author_url = Column(String(500))                     # 作者主页链接

    # ── 新增：视频详情 ──
    video_url = Column(String(500))                      # 原始视频链接
    script = Column(Text)                                # 视频文案内容
    top_comments = Column(JSON, default=list)            # 热门评论 [{nickname, content, likes}]
    video_create_time = Column(Integer, default=0)       # 视频发布时间戳
    duration = Column(Integer, default=0)                # 视频时长(秒)

    # ── 新增：互动比 ──
    like_play_ratio = Column(Float, default=0.0)         # 点赞/播放
    comment_play_ratio = Column(Float, default=0.0)      # 评论/播放
    collect_play_ratio = Column(Float, default=0.0)      # 收藏/播放


# ═══════════════════════════════════════════════
#  SaaS 多租户 & 认证模型
# ═══════════════════════════════════════════════

class Tenant(Base):
    """企业/租户"""
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="tenant")


class User(Base):
    """用户（通过微信公众号授权登录）"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    wechat_openid = Column(String(100), unique=True, nullable=True, index=True)
    wechat_unionid = Column(String(100), nullable=True, index=True)
    email = Column(String(200), unique=True, nullable=True, index=True)
    password_hash = Column(String(200), nullable=True)
    oauth_provider = Column(String(20), nullable=True)   # google / github
    oauth_id = Column(String(200), nullable=True)        # 第三方 OAuth 唯一 ID
    nickname = Column(String(200), default="")
    avatar = Column(String(500), default="")
    role = Column(String(20), default="member")          # admin / member
    is_active = Column(Boolean, default=True)
    session_version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    tenant = relationship("Tenant", back_populates="users")
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    orders = relationship("PaymentOrder", back_populates="user")

    @property
    def subscription_expire_at(self):
        if self.subscription:
            return self.subscription.expire_at
        return None

    @property
    def is_subscription_active(self):
        if not self.subscription:
            return False
        from datetime import timezone
        now = datetime.utcnow()
        return self.subscription.expire_at > now

    @property
    def is_trial(self):
        if not self.subscription:
            return False
        return self.subscription.plan == "trial"


class Subscription(Base):
    """用户订阅记录"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    plan = Column(String(20), nullable=False)            # trial / monthly
    started_at = Column(DateTime, default=datetime.utcnow)
    expire_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="subscription")


class PaymentOrder(Base):
    """支付订单"""
    __tablename__ = "payment_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount_fen = Column(Integer, nullable=False)         # 单位：分
    method = Column(String(20), nullable=False)          # wechat / alipay
    plan = Column(String(20), default="monthly")         # 购买的套餐
    status = Column(String(20), default="pending")       # pending / paid / closed / refunded
    pay_url = Column(Text, nullable=True)                # 支付链接 / 二维码 URL
    qr_code_url = Column(Text, nullable=True)            # 微信支付二维码图片
    transaction_id = Column(String(100), nullable=True)  # 第三方支付流水号
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="orders")


class DocumentFolder(Base):
    """产品资料文件夹（持久化空文件夹）"""
    __tablename__ = "document_folders"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class WechatScene(Base):
    """微信公众号带参场景二维码（用于 PC 端扫码登录）"""
    __tablename__ = "wechat_scenes"

    id = Column(Integer, primary_key=True, index=True)
    scene_id = Column(String(64), unique=True, nullable=False, index=True)
    ticket = Column(Text, nullable=True)                 # 微信返回的 ticket
    qr_url = Column(Text, nullable=True)                 # 二维码图片 URL
    status = Column(String(20), default="pending")       # pending / authorized / expired
    openid = Column(String(100), nullable=True)          # 扫码用户的 openid
    token = Column(Text, nullable=True)                  # 生成的 JWT（扫码成功后存入）
    expire_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ═══════════════════════════════════════════════
#  平台管理员模型
# ═══════════════════════════════════════════════

class AdminUser(Base):
    """平台超级管理员（独立于租户体系，使用账号密码登录）"""
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    nickname = Column(String(200), default="管理员")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

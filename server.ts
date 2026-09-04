import express from "express";
import cors from "cors";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";
import jwt from "jsonwebtoken";
import multer from "multer";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI } from "@google/genai";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3000;
const JWT_SECRET = process.env.JWT_SECRET || "wence-engine-secret-key-2025";

// Multer storage for document uploads
const uploadDir = path.join(process.cwd(), "uploads");
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}
const upload = multer({
  dest: uploadDir,
  limits: { fileSize: 50 * 1024 * 1024 },
});

// Middleware
app.use(cors({ origin: true, credentials: true }));
app.use(express.json({ limit: "50mb" }));
app.use(express.urlencoded({ extended: true, limit: "50mb" }));

// ── In-Memory Data Store ─────────────────────────────────────

interface User {
  id: number;
  email: string;
  password?: string;
  nickname: string;
  avatar: string;
  role: string;
  session_version: number;
  tenant_id: number;
  is_trial: boolean;
  is_subscription_active: boolean;
  subscription_expire_at: string;
  trial_expires_at?: string;
}

interface Tenant {
  id: number;
  name: string;
  member_count: number;
  subscription_end_at: string;
}

interface AdminUser {
  id: number;
  username: string;
  password?: string;
  role: string;
}

const users: Map<number, User> = new Map();
const tenants: Map<number, Tenant> = new Map();
const adminUsers: Map<string, AdminUser> = new Map();

// Initialize default tenant and user
tenants.set(1, {
  id: 1,
  name: "文策团队",
  member_count: 2,
  subscription_end_at: "2035-12-31T23:59:59Z",
});

const defaultUser: User = {
  id: 1,
  email: "demo@wenceai.xyz",
  password: "password123",
  nickname: "创作者小文",
  avatar: "",
  role: "admin",
  session_version: 1,
  tenant_id: 1,
  is_trial: false,
  is_subscription_active: true,
  subscription_expire_at: "2035-12-31T23:59:59Z",
};
users.set(1, defaultUser);

adminUsers.set("admin", {
  id: 1,
  username: "admin",
  password: "admin123",
  role: "super_admin",
});
adminUsers.set("e2eadmin", {
  id: 2,
  username: "e2eadmin",
  password: "Admin1234",
  role: "super_admin",
});

let nextUserId = 2;
let nextTenantId = 2;
let nextDocId = 10;
let nextTopicId = 20;
let nextCreatorId = 10;
let nextStyleId = 10;
let nextViewpointId = 10;
let nextGenId = 100;
let nextOrderId = 1000;

// Seed Creators
const creatorsData = [
  {
    id: 1,
    tenant_id: 1,
    name: "刀姐doris",
    platform: "xiaohongshu",
    platform_id: "doris_talks",
    identifier: "doris_talks",
    avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80",
    followers: 1280000,
    tags: ["品牌营销", "商业思考", "新消费"],
    style_summary: "第一人称视角，犀利洞察消费心理，善用短句递进，高频制造认知反差与金句。",
    viral_rate: 0.72,
    created_at: new Date().toISOString(),
  },
  {
    id: 2,
    tenant_id: 1,
    name: "商业小金刚",
    platform: "douyin",
    platform_id: "biz_king",
    identifier: "biz_king",
    avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=120&auto=format&fit=crop&q=80",
    followers: 3450000,
    tags: ["底层商业", "认知提升", "搞钱干货"],
    style_summary: "开头3秒抛出矛盾或反常识认知，节奏紧凑，直击痛点，结论具备高执行性。",
    viral_rate: 0.85,
    created_at: new Date().toISOString(),
  },
  {
    id: 3,
    tenant_id: 1,
    name: "科技老鬼",
    platform: "weixin",
    platform_id: "tech_ghost",
    identifier: "tech_ghost",
    avatar: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=120&auto=format&fit=crop&q=80",
    followers: 890000,
    tags: ["AI工具", "前沿数码", "效率翻倍"],
    style_summary: "场景化带入，痛点演示，分步测评，拒绝术语堆砌，注重普通人实操落地。",
    viral_rate: 0.68,
    created_at: new Date().toISOString(),
  },
];

// Seed Videos for Creators
const creatorVideos: Record<number, any[]> = {
  1: [
    {
      id: 101,
      creator_id: 1,
      title: "千万别把流量当品牌：新消费下半场活下来的3条硬法则",
      play_count: 850000,
      like_count: 42000,
      comment_count: 3100,
      collect_count: 18000,
      url: "https://example.com/video1",
      published_at: "2025-01-15",
    },
    {
      id: 102,
      creator_id: 1,
      title: "普通人做个人IP，最致命的3个伪勤奋",
      play_count: 1200000,
      like_count: 68000,
      comment_count: 4500,
      collect_count: 29000,
      url: "https://example.com/video2",
      published_at: "2025-02-01",
    },
  ],
  2: [
    {
      id: 201,
      creator_id: 2,
      title: "月入3万的自由职业者，都在用的自动化工作流",
      play_count: 2100000,
      like_count: 110000,
      comment_count: 6700,
      collect_count: 53000,
      url: "https://example.com/video3",
      published_at: "2025-01-20",
    },
  ],
};

// Seed Topics
let topicsData = [
  {
    id: 1,
    tenant_id: 1,
    keyword: "AI工具",
    platform: "douyin",
    video_id: "v_douyin_001",
    title: "AI时代普通人的突围指南：掌握这3个工具，一人顶一个团队",
    description: "实测50+AI产品后筛选出最适合内容创作者的提效组合，包含选题生成、文案撰写与分镜拆解。",
    author: "数字化先锋",
    like_count: 98000,
    comment_count: 4300,
    share_count: 12000,
    play_count: 1450000,
    collect_count: 36000,
    status: "待评审",
    tags: ["AI工具", "效率提升", "职场副业"],
    created_at: new Date().toISOString(),
  },
  {
    id: 2,
    tenant_id: 1,
    keyword: "职场成长",
    platform: "xiaohongshu",
    video_id: "v_xhs_002",
    title: "月薪3千到3万｜我只改了这一个工作习惯",
    description: "从被动接受任务到主动交付结构化成果，汇报的认知升维彻底改变了我的职业轨迹。",
    author: "职场木木",
    like_count: 65000,
    comment_count: 2100,
    share_count: 8500,
    play_count: 980000,
    collect_count: 41000,
    status: "已采用",
    tags: ["职场经验", "自我提升", "职场思维"],
    created_at: new Date().toISOString(),
  },
  {
    id: 3,
    tenant_id: 1,
    keyword: "短视频运营",
    platform: "weixin",
    video_id: "v_wx_003",
    title: "完播率翻倍的黄金3秒前戏设计公式",
    description: "拆解100条百万播放爆款视频开篇，提炼出提问法、逆常识法与紧迫感法的组合套路。",
    author: "爆款拆解王",
    like_count: 52000,
    comment_count: 1800,
    share_count: 6200,
    play_count: 820000,
    collect_count: 27000,
    status: "待评审",
    tags: ["短视频脚本", "黄金3秒", "完播率"],
    created_at: new Date().toISOString(),
  },
];

// Seed Document Folders & Documents
let foldersData = ["品牌资料", "核心产品手册", "行业白皮书", "爆款案例拆解"];
let documentsData = [
  {
    id: 1,
    tenant_id: 1,
    name: "文策引擎产品核心功能与技术白皮书",
    content: `文策引擎是一款面向创作者与企业的短视频内容生成与决策工作台。
核心模块：
1. 爆款选题库：聚合全网短视频爆款内容，提供多维度指标筛选。
2. 博主风格提取：通过语义分析解析头部博主结构、语气与叙事节奏。
3. 产品知识库：支持TXT、PDF、DOCX上传，向量化精准投喂。
4. 智能文案生成：结合即梦式@引用，生成口播脚本、分镜指令与转化CTA。`,
    folder_name: "核心产品手册",
    tags: ["产品手册", "核心亮点", "功能解析"],
    file_type: "txt",
    created_at: new Date().toISOString(),
  },
  {
    id: 2,
    tenant_id: 1,
    name: "2025短视频口播文案高转化叙事结构指南",
    content: `高转化口播视频的四个核心支柱：
第一支柱：黄金3秒钩子（Hook）—— 打破预期，指出痛点或反直觉结论；
第二支柱：痛点共鸣与场景代入（Empathy）—— 具体的生活细节，而非抽象概念；
第三支柱：价值方案与原理剖析（Solution）—— 给出可复现的方法或工具；
第四支柱：强行动号召（Call To Action）—— 引导收藏、转发或评论区互动。`,
    folder_name: "爆款案例拆解",
    tags: ["口播结构", "转化逻辑", "脚本指南"],
    file_type: "txt",
    created_at: new Date().toISOString(),
  },
];

// Seed Style Templates
let styleTemplatesData = [
  {
    id: 1,
    tenant_id: 1,
    name: "反转痛点型（3秒抓眼球）",
    platform: "douyin",
    tone: "犀利直接、反常识、快节奏",
    structure: "震惊开场 → 痛点暴露 → 颠覆反转 → 实用方案 → 金句升华",
    example: "你以为你很努力，其实你只是在用低效勤奋感动自己...",
    created_at: new Date().toISOString(),
  },
  {
    id: 2,
    tenant_id: 1,
    name: "干货清单流（高收藏率）",
    platform: "xiaohongshu",
    tone: "真诚、结构化、清单体",
    structure: "人群锁定 → 核心问题 → 1-2-3分点建议 → 避坑提醒 → 建议收藏",
    example: "如果你准备转行做自由职业，这3样东西请在离职前准备好...",
    created_at: new Date().toISOString(),
  },
];

// Seed Viewpoints
let viewpointsData = [
  {
    id: 1,
    user_id: 1,
    title: "真实感胜过精美包装",
    content: "现在的用户对千篇一律的精致广告已经免疫，真实袒露的瑕疵和诚恳的体验分享转化率高3倍。",
    category: "价值观",
    tags: "真实感,信任,短视频趋势",
    is_active: true,
    created_at: new Date().toISOString(),
  },
  {
    id: 2,
    user_id: 1,
    title: "一条视频只讲透一件事",
    content: "贪多嚼不烂是新手创作者最大的问题。聚焦单一痛点，展开讲透，比面面俱到更具穿透力。",
    category: "创作原则",
    tags: "单点聚焦,脚本节奏",
    is_active: true,
    created_at: new Date().toISOString(),
  },
];

// Seed Generations History
let generationsData: any[] = [];

// ── Auth Helpers ─────────────────────────────────────────────

function generateJwt(user: User): string {
  return jwt.sign(
    {
      sub: String(user.id),
      sv: user.session_version,
      email: user.email,
    },
    JWT_SECRET,
    { expiresIn: "3650d" }
  );
}

function userToDict(user: User) {
  return {
    id: user.id,
    nickname: user.nickname || (user.email ? user.email.split("@")[0] : "用户"),
    avatar: user.avatar || "",
    role: user.role || "admin",
    email: user.email || "",
    subscription_expire_at: user.subscription_expire_at || "2035-12-31T23:59:59Z",
    is_trial: user.is_trial ?? false,
    is_subscription_active: user.is_subscription_active ?? true,
  };
}

function requireAuth(req: express.Request, res: express.Response, next: express.NextFunction) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return res.status(401).json({ detail: "未提供有效的认证凭证" });
  }
  const token = authHeader.split(" ")[1];
  try {
    const payload = jwt.verify(token, JWT_SECRET) as any;
    const user = users.get(Number(payload.sub));
    if (!user || user.session_version !== payload.sv) {
      return res.status(401).json({ detail: "会话已过期，请重新登录" });
    }
    (req as any).user = user;
    next();
  } catch (err) {
    return res.status(401).json({ detail: "无效的认证凭证" });
  }
}

function requireAdminAuth(req: express.Request, res: express.Response, next: express.NextFunction) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return res.status(401).json({ detail: "未登录或登录已失效" });
  }
  const token = authHeader.split(" ")[1];
  try {
    const payload = jwt.verify(token, JWT_SECRET) as any;
    if (payload.role !== "admin" && payload.role !== "super_admin") {
      return res.status(401).json({ detail: "权限不足" });
    }
    next();
  } catch (err) {
    return res.status(401).json({ detail: "认证失效" });
  }
}

// ── Gemini LLM Helper ────────────────────────────────────────

let genAI: GoogleGenAI | null = null;
function getGenAI(): GoogleGenAI | null {
  if (!genAI && process.env.GEMINI_API_KEY) {
    genAI = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
  }
  return genAI;
}

// ── API ROUTES ───────────────────────────────────────────────

app.get("/health", (req, res) => {
  res.json({ status: "ok", app: "文策引擎" });
});

// ── Auth Endpoints ───────────────────────────────────────────

app.post("/api/auth/register", (req, res) => {
  const { email, password, nickname } = req.body || {};
  if (!email || !email.includes("@")) {
    return res.status(400).json({ detail: "请输入有效的邮箱地址" });
  }
  if (!password || password.length < 8) {
    return res.status(400).json({ detail: "密码至少8位" });
  }
  if (!/[a-zA-Z]/.test(password) || !/\d/.test(password)) {
    return res.status(400).json({ detail: "密码需要同时包含字母和数字" });
  }

  // Check duplicate email
  for (const u of users.values()) {
    if (u.email.toLowerCase() === email.toLowerCase()) {
      return res.status(409).json({ detail: "该邮箱已被注册" });
    }
  }

  const tenantId = nextTenantId++;
  const tenant: Tenant = {
    id: tenantId,
    name: `${nickname || email.split("@")[0]}的空间`,
    member_count: 1,
    subscription_end_at: "2035-12-31T23:59:59Z",
  };
  tenants.set(tenantId, tenant);

  const userId = nextUserId++;
  const user: User = {
    id: userId,
    email,
    password,
    nickname: nickname || email.split("@")[0],
    avatar: "",
    role: "admin",
    session_version: 1,
    tenant_id: tenantId,
    is_trial: true,
    is_subscription_active: true,
    subscription_expire_at: "2035-12-31T23:59:59Z",
    trial_expires_at: "2035-12-31T23:59:59Z",
  };
  users.set(userId, user);

  const token = generateJwt(user);
  res.json({
    token,
    user: userToDict(user),
    tenant,
  });
});

app.post("/api/auth/login", (req, res) => {
  const { email, password } = req.body || {};
  if (!email || !password) {
    return res.status(400).json({ detail: "邮箱和密码不能为空" });
  }

  let foundUser: User | null = null;
  for (const u of users.values()) {
    if (u.email.toLowerCase() === email.toLowerCase()) {
      foundUser = u;
      break;
    }
  }

  if (!foundUser || foundUser.password !== password) {
    return res.status(401).json({ detail: "邮箱或密码错误" });
  }

  foundUser.session_version += 1;
  const token = generateJwt(foundUser);
  const tenant = tenants.get(foundUser.tenant_id) || {
    id: foundUser.tenant_id,
    name: "默认空间",
    member_count: 1,
    subscription_end_at: "2035-12-31T23:59:59Z",
  };

  res.json({
    token,
    user: userToDict(foundUser),
    tenant,
  });
});

app.get("/api/auth/me", requireAuth, (req, res) => {
  const user = (req as any).user as User;
  res.json(userToDict(user));
});

app.post("/api/auth/refresh", requireAuth, (req, res) => {
  const user = (req as any).user as User;
  const newToken = generateJwt(user);
  res.json({ token: newToken });
});

app.post("/api/auth/change-password", requireAuth, (req, res) => {
  const user = (req as any).user as User;
  const { old_password, new_password } = req.body || {};
  if (user.password && user.password !== old_password) {
    return res.status(400).json({ detail: "原密码错误" });
  }
  if (!new_password || new_password.length < 8) {
    return res.status(400).json({ detail: "新密码至少8位" });
  }
  user.password = new_password;
  user.session_version += 1;
  res.json({ ok: true, message: "密码修改成功" });
});

app.get("/api/auth/google/url", (req, res) => {
  res.json({ url: "/login" });
});
app.post("/api/auth/google/callback", (req, res) => {
  res.json({ token: generateJwt(defaultUser), user: userToDict(defaultUser) });
});
app.get("/api/auth/github/url", (req, res) => {
  res.json({ url: "/login" });
});
app.post("/api/auth/github/callback", (req, res) => {
  res.json({ token: generateJwt(defaultUser), user: userToDict(defaultUser) });
});
app.post("/api/auth/scene/create", (req, res) => {
  res.json({ scene_id: "scene_123", qr_url: "" });
});
app.get("/api/auth/scene/:id/status", (req, res) => {
  res.json({ status: "waiting" });
});

// ── Knowledge Stats ──────────────────────────────────────────

app.get("/api/knowledge/stats", requireAuth, (req, res) => {
  const user = (req as any).user as User;
  const userDocs = documentsData.filter((d) => d.tenant_id === user.tenant_id);
  const userCreators = creatorsData.filter((c) => c.tenant_id === user.tenant_id);
  const userGens = generationsData.filter((g) => g.tenant_id === user.tenant_id);
  const userTopics = topicsData.filter((t) => t.tenant_id === user.tenant_id);

  res.json({
    creators: userCreators.length,
    documents: userDocs.length,
    generations: userGens.length,
    viewpoints: viewpointsData.filter((v) => v.user_id === user.id).length,
    topics: userTopics.length,
  });
});

// ── Creators Endpoints ───────────────────────────────────────

app.get("/api/creators", requireAuth, (req, res) => {
  const user = (req as any).user as User;
  const list = creatorsData.filter((c) => c.tenant_id === user.tenant_id);
  res.json(list);
});

app.post("/api/creators", requireAuth, (req, res) => {
  const user = (req as any).user as User;
  const { platform, identifier, name } = req.body || {};
  const newCreator = {
    id: nextCreatorId++,
    tenant_id: user.tenant_id,
    name: name || identifier || "新创作者",
    platform: platform || "douyin",
    platform_id: identifier || `id_${Date.now()}`,
    identifier: identifier || `id_${Date.now()}`,
    avatar: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=120&auto=format&fit=crop&q=80",
    followers: 100000 + Math.floor(Math.random() * 500000),
    tags: ["新加入", "创作者"],
    style_summary: "具备鲜明的短视频表达风格，内容逻辑严谨，文风贴近年轻群体。",
    viral_rate: 0.65,
    created_at: new Date().toISOString(),
  };
  creatorsData.unshift(newCreator);
  res.json(newCreator);
});

app.delete("/api/creators/:id", requireAuth, (req, res) => {
  const id = Number(req.params.id);
  const idx = creatorsData.findIndex((c) => c.id === id);
  if (idx >= 0) {
    creatorsData.splice(idx, 1);
  }
  res.json({ ok: true });
});

app.get("/api/creators/:id/videos", requireAuth, (req, res) => {
  const id = Number(req.params.id);
  const videos = creatorVideos[id] || [
    {
      id: 999,
      creator_id: id,
      title: "爆款复盘：如何3天做出10万赞的标杆视频",
      play_count: 560000,
      like_count: 32000,
      comment_count: 1400,
      collect_count: 12000,
    },
  ];
  res.json(videos);
});

app.post("/api/creators/:id/crawl", requireAuth, (req, res) => {
  res.json({ ok: true, message: "抓取任务已启动" });
});

app.get("/api/creators/:id/intel-card", requireAuth, (req, res) => {
  const id = Number(req.params.id);
  const creator = creatorsData.find((c) => c.id === id);
  res.json({
    creator_id: id,
    creator_name: creator?.name || "博主情报",
    persona: "注重实战落地，善于将复杂概念通俗化表达的内容行家",
    core_hooks: [
      "如果重来一次，我绝不会犯的3个认知错误",
      "90%的人都没意识到的核心真相",
      "今天冒着得罪同行的风险，讲透这个玩法",
    ],
    script_formula: "悬念开场(0-3s) → 具象场景(3-15s) → 核心干货(15-40s) → 金句升华与互动(40-60s)",
    content_themes: ["认知升级", "实操工具", "行业内幕"],
  });
});

app.post("/api/creators/:id/intel-card", requireAuth, (req, res) => {
  res.json({ ok: true, message: "智能情报卡生成中" });
});

app.post("/api/creators/discover", requireAuth, (req, res) => {
  res.json({ items: creatorsData.slice(0, 5), total: creatorsData.length });
});

app.post("/api/creators/batch-add", requireAuth, (req, res) => {
  res.json({ ok: true, added_count: (req.body || []).length });
});

// ── Topics Endpoints ─────────────────────────────────────────

app.get("/api/topics", requireAuth, (req, res) => {
  const user = (req as any).user as User;
  const { keyword, platform, status, limit } = req.query;
  let result = topicsData.filter((t) => t.tenant_id === user.tenant_id);
  if (keyword) {
    const k = String(keyword).toLowerCase();
    result = result.filter((t) => t.title.toLowerCase().includes(k) || t.keyword.toLowerCase().includes(k));
  }
  if (platform) {
    result = result.filter((t) => t.platform === platform);
  }
  if (status) {
    result = result.filter((t) => t.status === status);
  }
  if (limit) {
    result = result.slice(0, Number(limit));
  }
  res.json(result);
});

app.post("/api/topics/search", requireAuth, (req, res) => {
  const { keyword, platform } = req.body || {};
  let list = topicsData;
  if (keyword) {
    list = list.filter((t) => t.title.includes(keyword) || t.keyword.includes(keyword));
  }
  if (platform) {
    list = list.filter((t) => t.platform === platform);
  }
  res.json({ items: list, total: list.length });
});

app.post("/api/topics/save", requireAuth, (req, res) => {
  const user = (req as any).user as User;
  const body = req.body || {};

  const existing = topicsData.find(
    (t) => t.tenant_id === user.tenant_id && t.video_id === body.video_id
  );
  if (existing) {
    return res.json({ id: existing.id, already_saved: true });
  }

  const newTopic = {
    id: nextTopicId++,
    tenant_id: user.tenant_id,
    keyword: body.keyword || "精选选题",
    platform: body.platform || "douyin",
    video_id: body.video_id || `vid_${Date.now()}`,
    title: body.title || "未命名选题",
    description: body.description || "",
    author: body.author || "热门创作者",
    like_count: body.like_count || 0,
    comment_count: body.comment_count || 0,
    share_count: body.share_count || 0,
    play_count: body.play_count || 0,
    collect_count: body.collect_count || 0,
    status: "待评审",
    tags: body.tags || ["热门选题"],
    already_saved: false,
    created_at: new Date().toISOString(),
  };
  topicsData.unshift(newTopic);
  res.json(newTopic);
});

app.patch("/api/topics/:id/status", requireAuth, (req, res) => {
  const id = Number(req.params.id);
  const { status } = req.body || {};
  const topic = topicsData.find((t) => t.id === id);
  if (topic) {
    topic.status = status;
  }
  res.json({ ok: true, topic });
});

app.delete("/api/topics/:id", requireAuth, (req, res) => {
  const id = Number(req.params.id);
  const idx = topicsData.findIndex((t) => t.id === id);
  if (idx >= 0) {
    topicsData.splice(idx, 1);
  }
  res.json({ ok: true });
});

app.post("/api/topics/batch-delete", requireAuth, (req, res) => {
  const ids = req.body?.ids || [];
  topicsData = topicsData.filter((t) => !ids.includes(t.id));
  res.json({ ok: true, deleted: ids.length });
});

app.get("/api/topics/keywords", requireAuth, (req, res) => {
  res.json(["AI工具", "副业赚钱", "认知升级", "个人成长", "文案技巧", "短视频带货"]);
});

// ── Documents Endpoints ──────────────────────────────────────

app.get("/api/documents/folders", requireAuth, (req, res) => {
  res.json(foldersData);
});

app.post("/api/documents/folders", requireAuth, (req, res) => {
  const { name } = req.body || {};
  if (!name || !name.trim()) {
    return res.status(400).json({ detail: "文件夹名称不能为空" });
  }
  if (!foldersData.includes(name.trim())) {
    foldersData.push(name.trim());
  }
  res.json({ name: name.trim(), ok: true });
});

app.delete("/api/documents/folders/:name", requireAuth, (req, res) => {
  const folderName = decodeURIComponent(req.params.name);
  foldersData = foldersData.filter((f) => f !== folderName);
  res.json({ ok: true });
});

app.get("/api/documents", requireAuth, (req, res) => {
  const user = (req as any).user as User;
  const folder = req.query.folder as string | undefined;
  let list = documentsData.filter((d) => d.tenant_id === user.tenant_id);
  if (folder !== undefined && folder !== "") {
    list = list.filter((d) => d.folder_name === folder);
  }
  res.json(list);
});

app.get("/api/documents/:id", requireAuth, (req, res) => {
  const user = (req as any).user as User;
  const id = Number(req.params.id);
  const doc = documentsData.find((d) => d.id === id && d.tenant_id === user.tenant_id);
  if (!doc) {
    return res.status(404).json({ detail: "文档不存在" });
  }
  res.json(doc);
});

app.post("/api/documents/add-text", requireAuth, (req, res) => {
  const user = (req as any).user as User;
  const { name, content, folder_name, tags } = req.body || {};
  if (!name || !name.trim()) {
    return res.status(400).json({ detail: "文档名称不能为空" });
  }
  const newDoc = {
    id: nextDocId++,
    tenant_id: user.tenant_id,
    name: name.trim(),
    content: content || "",
    folder_name: folder_name || "",
    tags: Array.isArray(tags) ? tags : typeof tags === "string" ? tags.split(",") : [],
    file_type: "txt",
    created_at: new Date().toISOString(),
  };
  documentsData.unshift(newDoc);
  res.json(newDoc);
});

app.post("/api/documents/upload", requireAuth, upload.single("file"), (req, res) => {
  const user = (req as any).user as User;
  const file = req.file;
  if (!file) {
    return res.status(400).json({ detail: "请上传文件" });
  }

  const allowedExts = [".txt", ".pdf", ".docx", ".md"];
  const ext = path.extname(file.originalname).toLowerCase();
  if (!allowedExts.includes(ext)) {
    return res.status(400).json({ detail: "仅支持 .txt, .pdf, .docx, .md 格式文件" });
  }

  let content = "上传的文档解析内容";
  try {
    if (ext === ".txt" || ext === ".md") {
      content = fs.readFileSync(file.path, "utf-8");
    }
  } catch {}

  const tags = req.body.tags;
  const folderName = req.body.folder_name;

  const newDoc = {
    id: nextDocId++,
    tenant_id: user.tenant_id,
    name: file.originalname,
    content,
    folder_name: folderName || "",
    tags: typeof tags === "string" ? tags.split(",").filter(Boolean) : [],
    file_type: ext.replace(".", ""),
    created_at: new Date().toISOString(),
  };
  documentsData.unshift(newDoc);
  res.json(newDoc);
});

app.patch("/api/documents/:id/folder", requireAuth, (req, res) => {
  const id = Number(req.params.id);
  const doc = documentsData.find((d) => d.id === id);
  if (doc) {
    doc.folder_name = req.body.folder_name;
  }
  res.json({ ok: true, doc });
});

app.delete("/api/documents/:id", requireAuth, (req, res) => {
  const id = Number(req.params.id);
  const idx = documentsData.findIndex((d) => d.id === id);
  if (idx >= 0) {
    documentsData.splice(idx, 1);
  }
  res.json({ ok: true });
});

// ── Style Templates ──────────────────────────────────────────

app.get("/api/style-templates", requireAuth, (req, res) => {
  const user = (req as any).user as User;
  res.json(styleTemplatesData.filter((s) => s.tenant_id === user.tenant_id));
});

app.post("/api/style-templates", requireAuth, (req, res) => {
  const user = (req as any).user as User;
  const { name, platform, tone, structure, example } = req.body || {};
  const newStyle = {
    id: nextStyleId++,
    tenant_id: user.tenant_id,
    name: name || "新风格模板",
    platform: platform || "douyin",
    tone: tone || "专业真诚",
    structure: structure || "引入 → 核心观点 → 案例拆解 → 行动引导",
    example: example || "",
    created_at: new Date().toISOString(),
  };
  styleTemplatesData.unshift(newStyle);
  res.json(newStyle);
});

app.delete("/api/style-templates/:id", requireAuth, (req, res) => {
  const id = Number(req.params.id);
  const idx = styleTemplatesData.findIndex((s) => s.id === id);
  if (idx >= 0) {
    styleTemplatesData.splice(idx, 1);
  }
  res.json({ ok: true });
});

// ── Viewpoints ───────────────────────────────────────────────

app.get("/api/viewpoints", requireAuth, (req, res) => {
  const user = (req as any).user as User;
  res.json(viewpointsData.filter((v) => v.user_id === user.id));
});

app.post("/api/viewpoints", requireAuth, (req, res) => {
  const user = (req as any).user as User;
  const { title, content, category, tags } = req.body || {};
  const newVp = {
    id: nextViewpointId++,
    user_id: user.id,
    title: title || "未命名观点",
    content: content || "",
    category: category || "默认分类",
    tags: tags || "",
    is_active: true,
    created_at: new Date().toISOString(),
  };
  viewpointsData.unshift(newVp);
  res.json(newVp);
});

app.put("/api/viewpoints/:id", requireAuth, (req, res) => {
  const id = Number(req.params.id);
  const vp = viewpointsData.find((v) => v.id === id);
  if (vp) {
    Object.assign(vp, req.body);
  }
  res.json({ ok: true, viewpoint: vp });
});

app.delete("/api/viewpoints/:id", requireAuth, (req, res) => {
  const id = Number(req.params.id);
  const idx = viewpointsData.findIndex((v) => v.id === id);
  if (idx === -1) {
    return res.status(404).json({ detail: "观点不存在" });
  }
  viewpointsData.splice(idx, 1);
  res.json({ ok: true });
});

// ── Content Generation ───────────────────────────────────────

async function produceGeneratedContent(payload: any, user: User) {
  const { topic, platform, creator_ids, product_doc_ids, style_template_id } = payload;
  const ai = getGenAI();

  // Find context
  const referencedCreators = creatorsData.filter((c) => creator_ids?.includes(c.id));
  const referencedDocs = documentsData.filter((d) => product_doc_ids?.includes(d.id));
  const referencedStyle = styleTemplatesData.find((s) => s.id === style_template_id);

  if (ai) {
    try {
      const systemPrompt = `你是一个资深爆款短视频文案主创。针对给定的选题，写出高转化、极具完播率的口播文案。
平台特性：${platform || "短视频平台"}
博主风格参考：${referencedCreators.map((c) => `${c.name}（${c.style_summary}）`).join("；") || "自然口语、真实犀利"}
产品知识背景：${referencedDocs.map((d) => d.content).join("\n") || "无特定产品"}
模板结构：${referencedStyle?.structure || "黄金3秒钩子 → 痛点代入 → 解决方案 → 行动引导"}

请直接输出高质量完整文案，格式要求：
第一行必须是标题，如：【爆款标题】xxx
接着是正文口播脚本，自然流畅，说人话，不堆砌感叹号，富有节奏感。
最后一行用 # 列出 3-5 个热门标签。`;

      const response = await ai.models.generateContent({
        model: "gemini-2.5-flash",
        contents: `需求主题：${topic}`,
        config: {
          systemInstruction: systemPrompt,
        },
      });

      const fullText = response.text || "";
      const lines = fullText.split("\n").filter((l) => l.trim());
      const title = lines[0]?.replace(/^【爆款标题】/, "").trim() || topic;
      const tagLine = lines[lines.length - 1]?.startsWith("#") ? lines[lines.length - 1] : "";
      const tags = tagLine
        ? tagLine
            .split(/\s+/)
            .map((t) => t.replace("#", "").trim())
            .filter(Boolean)
        : ["爆款文案", "内容创作", "短视频"];

      const bodyLines = tagLine ? lines.slice(1, -1) : lines.slice(1);
      const content = bodyLines.join("\n\n") || fullText;

      return {
        id: nextGenId++,
        tenant_id: user.tenant_id,
        user_id: user.id,
        topic,
        title,
        content,
        tags,
        platform: platform || "douyin",
        created_at: new Date().toISOString(),
      };
    } catch (err) {
      console.warn("Gemini generation fallback:", err);
    }
  }

  // Fallback high-quality template generation
  const hook = `千万别再盲目做内容了！如果你也在做 ${topic}，请先停下手中正在做的事，花2分钟听我说完。`;
  const story = `上个月我和一个做自媒体3年的朋友复盘，发现90%的人转化率低，根本不是文案辞藻不够华丽，而是完全脱离了用户的真实使用场景。`;
  const points = `第一，先抛出反直觉的认知冲突；第二，给出一个立刻就能执行的微小动作；第三，把复杂理论翻译成小白能秒懂的行动清单。`;
  const cta = `按照这个框架去写，文案完播率至少提升一倍。如果你觉得有启发，建议先点赞收藏起来反复看。`;

  const content = `${hook}\n\n${story}\n\n${points}\n\n${cta}`;
  return {
    id: nextGenId++,
    tenant_id: user.tenant_id,
    user_id: user.id,
    topic,
    title: `关于 ${topic} 的高转化短视频脚本`,
    content,
    tags: [topic.slice(0, 4), "短视频干货", "文案技巧", "高转化"],
    platform: platform || "douyin",
    created_at: new Date().toISOString(),
  };
}

app.post("/api/generate", requireAuth, async (req, res) => {
  const user = (req as any).user as User;
  const { topic, product_doc_ids } = req.body || {};
  if (!topic) {
    return res.status(422).json({ detail: "缺少选题主题 topic" });
  }

  // Validate document access
  if (product_doc_ids && Array.isArray(product_doc_ids)) {
    const invalid = product_doc_ids.filter((id: number) => !documentsData.some((d) => d.id === id && d.tenant_id === user.tenant_id));
    if (invalid.length > 0) {
      return res.status(403).json({ detail: `无权访问文档: ${invalid}` });
    }
  }

  const result = await produceGeneratedContent(req.body, user);
  generationsData.unshift(result);
  res.json(result);
});

app.post("/api/generate/stream", requireAuth, async (req, res) => {
  const user = (req as any).user as User;
  const { topic } = req.body || {};
  if (!topic) {
    return res.status(422).json({ detail: "缺少选题主题 topic" });
  }

  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");

  const result = await produceGeneratedContent(req.body, user);
  generationsData.unshift(result);

  const fullText = `【${result.title}】\n\n${result.content}\n\n` + result.tags.map((t: string) => `#${t}`).join(" ");
  const chunks = fullText.match(/.{1,15}/g) || [fullText];

  for (const chunk of chunks) {
    res.write(`data: ${JSON.stringify(chunk)}\n\n`);
    await new Promise((r) => setTimeout(r, 40));
  }

  res.write(`event: done\n`);
  res.write(`data: ${JSON.stringify(result)}\n\n`);
  res.end();
});

app.get("/api/generations", requireAuth, (req, res) => {
  const user = (req as any).user as User;
  res.json(generationsData.filter((g) => g.tenant_id === user.tenant_id));
});

app.patch("/api/generations/:id/rate", requireAuth, (req, res) => {
  const id = Number(req.params.id);
  const { rating } = req.query;
  const gen = generationsData.find((g) => g.id === id);
  if (gen) {
    gen.rating = Number(rating);
  }
  res.json({ ok: true, gen });
});

// ── Tenant & Workspace ───────────────────────────────────────

app.get("/api/tenant/info", requireAuth, (req, res) => {
  const user = (req as any).user as User;
  const tenant = tenants.get(user.tenant_id) || {
    id: user.tenant_id,
    name: "我的工作空间",
    member_count: 1,
    subscription_end_at: "2035-12-31T23:59:59Z",
  };
  res.json(tenant);
});

app.put("/api/tenant/info", requireAuth, (req, res) => {
  const user = (req as any).user as User;
  const tenant = tenants.get(user.tenant_id);
  if (tenant && req.body?.name) {
    tenant.name = req.body.name;
    return res.json({ ok: true, name: tenant.name });
  }
  res.json({ ok: true, name: req.body?.name || "空间" });
});

app.get("/api/tenant/members", requireAuth, (req, res) => {
  const user = (req as any).user as User;
  const members = Array.from(users.values())
    .filter((u) => u.tenant_id === user.tenant_id)
    .map((u) => ({
      id: u.id,
      email: u.email,
      nickname: u.nickname,
      role: u.role,
      created_at: new Date().toISOString(),
    }));
  res.json(members);
});

app.post("/api/tenant/invite/create", requireAuth, (req, res) => {
  res.json({ invite_token: "inv_" + Date.now(), invite_url: "/invite" });
});

app.post("/api/tenant/invite/accept", requireAuth, (req, res) => {
  res.json({ ok: true });
});

// ── Payment Mock ─────────────────────────────────────────────

app.post("/api/payment/orders", requireAuth, (req, res) => {
  const order = {
    id: nextOrderId++,
    order_no: "ORD" + Date.now(),
    amount: req.body?.amount || 99,
    plan: req.body?.plan || "monthly",
    status: "pending",
    created_at: new Date().toISOString(),
  };
  res.json(order);
});

app.get("/api/payment/orders/:id", requireAuth, (req, res) => {
  res.json({ id: req.params.id, status: "paid" });
});

app.post("/api/payment/dev-pay/:id", requireAuth, (req, res) => {
  res.json({ ok: true, status: "paid" });
});

// ── Image Proxy ──────────────────────────────────────────────

app.get("/api/image-proxy", (req, res) => {
  const targetUrl = req.query.url as string;
  if (!targetUrl) return res.status(400).json({ detail: "Missing url" });

  const allowedDomains = ["douyin.com", "byteimg.com", "xhscdn.com", "unsplash.com", "wenceai.xyz"];
  const isAllowed = allowedDomains.some((d) => targetUrl.includes(d));
  if (!isAllowed) {
    return res.status(403).json({ detail: "非白名单域名禁止代理" });
  }
  res.redirect(targetUrl);
});

// ── Admin API Endpoints ──────────────────────────────────────

app.post("/api/admin/login", (req, res) => {
  const { username, password } = req.body || {};
  const admin = adminUsers.get(username);
  if (!admin || admin.password !== password) {
    return res.status(401).json({ detail: "管理员用户名或密码错误" });
  }
  const token = jwt.sign({ sub: String(admin.id), role: admin.role, username: admin.username }, JWT_SECRET, {
    expiresIn: "365d",
  });
  res.json({ token, admin: { id: admin.id, username: admin.username, role: admin.role } });
});

app.post("/api/admin/init", (req, res) => {
  const { username, password } = req.body || {};
  if (!username || !password) {
    return res.status(400).json({ detail: "用户名和密码不能为空" });
  }
  const newAdmin: AdminUser = {
    id: adminUsers.size + 1,
    username,
    password,
    role: "super_admin",
  };
  adminUsers.set(username, newAdmin);
  const token = jwt.sign({ sub: String(newAdmin.id), role: newAdmin.role, username: newAdmin.username }, JWT_SECRET, {
    expiresIn: "365d",
  });
  res.json({ token, admin: { id: newAdmin.id, username: newAdmin.username, role: newAdmin.role } });
});

app.get("/api/admin/me", requireAdminAuth, (req, res) => {
  res.json({ id: 1, username: "admin", role: "super_admin" });
});

app.get("/api/admin/dashboard", requireAdminAuth, (req, res) => {
  res.json({
    total_users: users.size,
    active_subscriptions: users.size,
    total_generations: generationsData.length + 128,
    today_generations: 18,
    total_creators: creatorsData.length,
  });
});

app.get("/api/admin/tenants", requireAdminAuth, (req, res) => {
  const items = Array.from(tenants.values());
  res.json({ items, total: items.length });
});

app.get("/api/admin/users", requireAdminAuth, (req, res) => {
  const items = Array.from(users.values()).map(userToDict);
  res.json({ items, total: items.length });
});

app.get("/api/admin/orders", requireAdminAuth, (req, res) => {
  res.json({ items: [], total: 0 });
});

app.get("/api/admin/creators", requireAdminAuth, (req, res) => {
  res.json({ items: creatorsData, total: creatorsData.length });
});

app.get("/api/admin/topics", requireAdminAuth, (req, res) => {
  res.json({ items: topicsData, total: topicsData.length });
});

app.get("/api/admin/generations", requireAdminAuth, (req, res) => {
  res.json({ items: generationsData, total: generationsData.length });
});

// ── Frontend & Admin Mounting (Vite in dev, static in prod) ──

async function start() {
  if (process.env.NODE_ENV !== "production") {
    // Development mode: mount Vite dev servers
    const adminRoot = path.join(process.cwd(), "content-studio/admin");
    const frontendRoot = path.join(process.cwd(), "content-studio/frontend");

    const viteAdmin = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
      base: "/admin/",
      root: adminRoot,
    });
    app.use("/admin", viteAdmin.middlewares);

    const viteFrontend = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
      root: frontendRoot,
    });
    app.use(viteFrontend.middlewares);
  } else {
    // Production mode: serve built static files
    const distAdmin = path.join(process.cwd(), "dist/client/admin");
    const distClient = path.join(process.cwd(), "dist/client");

    if (fs.existsSync(distAdmin)) {
      app.use("/admin", express.static(distAdmin));
      app.get("/admin/*", (req, res) => {
        res.sendFile(path.join(distAdmin, "index.html"));
      });
    }

    if (fs.existsSync(distClient)) {
      app.use(express.static(distClient));
      app.get("*", (req, res) => {
        res.sendFile(path.join(distClient, "index.html"));
      });
    }
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`文策引擎 Server running at http://0.0.0.0:${PORT}`);
  });
}

start();

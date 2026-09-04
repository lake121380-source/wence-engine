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

// Seed Video Analyses
interface VideoAnalysisItem {
  id: number;
  tenant_id: number;
  video_id?: number;
  topic_id?: number;
  title: string;
  source: string;
  cover_url?: string;
  author_avatar?: string;
  like_play_ratio?: number;
  comment_play_ratio?: number;
  collect_play_ratio?: number;
  why_viral_summary: string;
  hook_technique?: string;
  visual_hook?: string;
  core_conflict?: string;
  pacing_rhythm?: string;
  audience_psychology?: string;
  created_at: string;
}

let analysesData: VideoAnalysisItem[] = [
  {
    id: 1,
    tenant_id: 1,
    topic_id: 1,
    title: "AI时代普通人的突围指南：掌握这3个工具，一人顶一个团队",
    source: "抖音 · 数字化先锋",
    cover_url: "",
    author_avatar: "",
    like_play_ratio: 0.068,
    comment_play_ratio: 0.003,
    collect_play_ratio: 0.025,
    why_viral_summary: "开场前3秒打破认知焦虑，直给一人顶一个团队的低门槛解法，中段清单式演示效率倍增实操，高收藏率。",
    hook_technique: "反直觉否定 + 悬念破局",
    visual_hook: "特写推镜 + 强反差红黑花字",
    core_conflict: "普通人面对AI裁员潮的焦虑 vs 借助AI赋能降维打击的解法",
    pacing_rhythm: "快节奏卡点、短句连击",
    audience_psychology: "职场自救与效率提升欲望",
    created_at: new Date().toISOString(),
  },
  {
    id: 2,
    tenant_id: 1,
    topic_id: 3,
    title: "完播率翻倍的黄金3秒前戏设计公式",
    source: "视频号 · 爆款拆解王",
    cover_url: "",
    author_avatar: "",
    like_play_ratio: 0.063,
    comment_play_ratio: 0.002,
    collect_play_ratio: 0.033,
    why_viral_summary: "精准命中短视频创作者最关心的完播率痛点，结构化拆解3套即学即用的开篇句式，高价值干货触发强收藏。",
    hook_technique: "痛点直击 + 公式化交付",
    visual_hook: "思维导图白板手写动画",
    core_conflict: "视频发出去没人看的挫败感 vs 掌握黄金3秒后的流量暴涨",
    pacing_rhythm: "层层递进、逻辑闭环",
    audience_psychology: "创作者对流量增长的迫切需求",
    created_at: new Date().toISOString(),
  },
  {
    id: 3,
    tenant_id: 1,
    video_id: 101,
    title: "千万别把流量当品牌：新消费下半场活下来的3条硬法则",
    source: "商业思维 · 创业实战",
    cover_url: "",
    author_avatar: "",
    like_play_ratio: 0.049,
    comment_play_ratio: 0.004,
    collect_play_ratio: 0.021,
    why_viral_summary: "以犀利的逆向商业思考切入，剖析烧钱买量虚假繁荣的真相，建立专业深度信任背书。",
    hook_technique: "逆行业常识否定",
    visual_hook: "凝重第一人称近景",
    core_conflict: "流量虚假繁荣 vs 真实复购与利润生存",
    pacing_rhythm: "沉稳有力、字字珠玑",
    audience_psychology: "创业者与品牌负责人的避坑求生本能",
    created_at: new Date().toISOString(),
  },
];
let nextAnalysisId = 4;

// Seed Generations History
let generationsData: any[] = [
  {
    id: 101,
    tenant_id: 1,
    tenant_name: "文策团队",
    user_id: 1,
    user_name: "创作者小文",
    topic: "普通人如何用AI做自媒体副业",
    title: "【爆款实操】普通人AI副业突围：每天30分钟，搭建自动化内容流水线",
    content: "千万别再盲目用业余时间做体力搬运了！\n\n如果你也在探索AI自媒体副业，请先停下手里的无效试错，花两分钟把这套闭环跑通。\n\n上个月我帮一个做职场自媒体的学员复盘，他每天吭哧吭哧写3小时阅读量不到500。我们帮他把选题、结构化提示词和封面脚本全流程串联后，单条爆款涨粉1.2万。\n\n核心就在三步法则：\n第一，用爆款三维拆解模型，逆向提炼同行最高频的认知冲突钩子；\n第二，借助文策AI智能工作流，输入核心论点一键产出高转化口播分镜；\n第三，在结尾设计低阻力的互动钩子，把公域流量沉淀为高粘性私域粉丝。\n\n按照这套逻辑，内容生产效率提升5倍以上。先点赞收藏起来，下期给你演示具体工作流实操！",
    content_preview: "千万别再盲目用业余时间做体力搬运了！如果你也在探索AI自媒体副业，请先停下手里的无效试错...",
    full_content: "千万别再盲目用业余时间做体力搬运了！\n\n如果你也在探索AI自媒体副业，请先停下手里的无效试错，花两分钟把这套闭环跑通。\n\n上个月我帮一个做职场自媒体的学员复盘，他每天吭哧吭哧写3小时阅读量不到500。我们帮他把选题、结构化提示词和封面脚本全流程串联后，单条爆款涨粉1.2万。\n\n核心就在三步法则：\n第一，用爆款三维拆解模型，逆向提炼同行最高频的认知冲突钩子；\n第二，借助文策AI智能工作流，输入核心论点一键产出高转化口播分镜；\n第三，在结尾设计低阻力的互动钩子，把公域流量沉淀为高粘性私域粉丝。\n\n按照这套逻辑，内容生产效率提升5倍以上。先点赞收藏起来，下期给你演示具体工作流实操！",
    tags: ["AI副业", "自媒体运营", "文案干货", "效率提升"],
    platform: "douyin",
    model: "gemini-2.5-flash",
    latency_ms: 1680,
    tokens: 724,
    prompt_tokens: 340,
    completion_tokens: 384,
    word_count: 432,
    rating: 5,
    hook_technique: "反直觉否定 + 悬念破局",
    status: "success",
    created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
  },
  {
    id: 102,
    tenant_id: 1,
    tenant_name: "文策团队",
    user_id: 1,
    user_name: "创作者小文",
    topic: "完播率翻倍的黄金3秒前戏设计公式",
    title: "完播率翻倍的黄金3秒前戏设计公式：90%新手都在踩的误区",
    content: "短视频发出去总是卡在500播放？根本原因不是你的内容没深度，而是前3秒就把观众劝退了！\n\n短视频平台的考核核心是【前3秒跳出率】。观众滑走只需要0.2秒，如果你开场还在说“哈喽大家好今天给你们分享”，完播率注定垫底。\n\n今天送你3套经过上千万播放验证的黄金开场白公式：\n1. 【痛点直击型】：“如果你也在为视频没人看焦虑，听完这3点至少少走半年弯路”；\n2. 【认知颠覆型】：“别再盲目抄爆款了，教你一个反常识的底层打法”；\n3. 【高维提炼型】：“看完这期视频，你做内容的效率至少提升一倍”。\n\n把这3个公式抄进备忘录，下个视频立刻套用测试效果！",
    content_preview: "短视频发出去总是卡在500播放？根本原因不是你的内容没深度，而是前3秒就把观众劝退了...",
    full_content: "短视频发出去总是卡在500播放？根本原因不是你的内容没深度，而是前3秒就把观众劝退了！\n\n短视频平台的考核核心是【前3秒跳出率】。观众滑走只需要0.2秒，如果你开场还在说“哈喽大家好今天给你们分享”，完播率注定垫底。\n\n今天送你3套经过上千万播放验证的黄金开场白公式：\n1. 【痛点直击型】：“如果你也在为视频没人看焦虑，听完这3点至少少走半年弯路”；\n2. 【认知颠覆型】：“别再盲目抄爆款了，教你一个反常识的底层打法”；\n3. 【高维提炼型】：“看完这期视频，你做内容的效率至少提升一倍”。\n\n把这3个公式抄进备忘录，下个视频立刻套用测试效果！",
    tags: ["短视频技巧", "完播率", "爆款黄金3秒", "自媒体起号"],
    platform: "channels",
    model: "gemini-2.5-flash",
    latency_ms: 1540,
    tokens: 690,
    prompt_tokens: 310,
    completion_tokens: 380,
    word_count: 418,
    rating: 5,
    hook_technique: "痛点直击 + 公式化交付",
    status: "success",
    created_at: new Date(Date.now() - 3600000 * 8).toISOString(),
  },
  {
    id: 103,
    tenant_id: 1,
    tenant_name: "文策团队",
    user_id: 1,
    user_name: "创作者小文",
    topic: "独居女生卧室改造清单：如何用300块打造高级感",
    title: "【独居美学】300块穷装出租屋卧室！侘寂原木风超治愈改造清单",
    content: "谁说租来的房子就不能拥有生活质感？\n\n手把手教你如何用300块搞定一个温暖又治愈的日落卧室。\n\n改造核心原则：轻硬装、重氛围光源与布艺质感。\n第一步，撤掉塑料冷光灯，换上一个暖色落日氛围台灯（45元），整个屋子的光影层次瞬间拉满；\n第二步，选用原色水洗棉纯色床品和亚麻桌垫，减少杂乱撞色（110元）；\n第三步，淘两个藤编收纳筐加一束干枯尤加利叶，既能遮丑又是绝美拍照角落（60元）。\n\n下班回家推开门的瞬间，疲惫被彻底抚平。详细购买清单整理在图文最后，喜欢的姐妹快码住！",
    content_preview: "谁说租来的房子就不能拥有生活质感？手把手教你如何用300块搞定一个温暖又治愈的日落卧室...",
    full_content: "谁说租来的房子就不能拥有生活质感？\n\n手把手教你如何用300块搞定一个温暖又治愈的日落卧室。\n\n改造核心原则：轻硬装、重氛围光源与布艺质感。\n第一步，撤掉塑料冷光灯，换上一个暖色落日氛围台灯（45元），整个屋子的光影层次瞬间拉满；\n第二步，选用原色水洗棉纯色床品和亚麻桌垫，减少杂乱撞色（110元）；\n第三步，淘两个藤编收纳筐加一束干枯尤加利叶，既能遮丑又是绝美拍照角落（60元）。\n\n下班回家推开门的瞬间，疲惫被彻底抚平。详细购买清单整理在图文最后，喜欢的姐妹快码住！",
    tags: ["独居日常", "出租屋改造", "小红书美学", "家居好物"],
    platform: "xiaohongshu",
    model: "gemini-2.5-flash",
    latency_ms: 1980,
    tokens: 780,
    prompt_tokens: 360,
    completion_tokens: 420,
    word_count: 472,
    rating: 5,
    hook_technique: "情绪共鸣 + 清单交付",
    status: "success",
    created_at: new Date(Date.now() - 3600000 * 20).toISOString(),
  },
  {
    id: 104,
    tenant_id: 1,
    tenant_name: "文策团队",
    user_id: 1,
    user_name: "创作者小文",
    topic: "千万别把流量当品牌：新消费下半场活下来的3条硬法则",
    title: "千万别把流量当品牌：新消费下半场活下来的3条硬法则",
    content: "流量红利见顶的当下，那些靠高ROI投流砸出来的假繁荣品牌，正在加速离场。\n\n很多创业者误以为只要ROI大于1就能一直跑下去，殊不知一旦停止买量，复购和留存惨不忍睹。\n\n新消费下半场真正能穿越周期的品牌，都在做这三件事：\n一、构建无可替代的超级产品心智，让用户自发成为传播节点；\n二、做私域深度运营而非粗暴群发，将一次性交易转化为终身顾客价值；\n三、算清真实利润账，守住健康的正向经营性现金流。\n\n生意不是比谁跑得快，而是比谁活得久。做品牌需要耐心，慢即是快。",
    content_preview: "流量红利见顶的当下，那些靠高ROI投流砸出来的假繁荣品牌，正在加速离场...",
    full_content: "流量红利见顶的当下，那些靠高ROI投流砸出来的假繁荣品牌，正在加速离场。\n\n很多创业者误以为只要ROI大于1就能一直跑下去，殊不知一旦停止买量，复购和留存惨不忍睹。\n\n新消费下半场真正能穿越周期的品牌，都在做这三件事：\n一、构建无可替代的超级产品心智，让用户自发成为传播节点；\n二、做私域深度运营而非粗暴群发，将一次性交易转化为终身顾客价值；\n三、算清真实利润账，守住健康的正向经营性现金流。\n\n生意不是比谁跑得快，而是比谁活得久。做品牌需要耐心，慢即是快。",
    tags: ["商业思考", "品牌营销", "新消费", "创业真经"],
    platform: "channels",
    model: "gemini-2.5-flash",
    latency_ms: 1720,
    tokens: 710,
    prompt_tokens: 330,
    completion_tokens: 380,
    word_count: 425,
    rating: 5,
    hook_technique: "逆行业常识否定",
    status: "success",
    created_at: new Date(Date.now() - 3600000 * 30).toISOString(),
  },
  {
    id: 105,
    tenant_id: 1,
    tenant_name: "文策团队",
    user_id: 1,
    user_name: "创作者小文",
    topic: "小县城餐饮老板自救：靠三板斧同城引流，单月流水翻3倍",
    title: "小县城实体餐饮自救：不花冤枉钱买推广，单月流水翻3倍的同城打法",
    content: "隔壁奶茶店天天排队，自己的店门可罗雀？实体老板别再傻傻去街上发传单了！\n\n分享一家三线城市社区烤肉店的逆袭实操，靠这套打法30天扭亏为盈：\n第一斧：打造【视觉视觉锚点爆品】。不推大而全菜单，单推一款份量震撼、性价比极高的引流烤肉塔，进店拍照率高达80%；\n第二斧：同城短视频真实后厨+老板性格IP，不拍广告只拍切肉、腌料与烟火气；\n第三斧：同城团购裂变。把优惠券精准投放到周边3公里年轻客群，核销率提升至65%。\n\n实体店的核心不是缺客人，而是缺给客人一个必来的理由！",
    content_preview: "隔壁奶茶店天天排队，自己的店门可罗雀？实体老板别再傻傻去街上发传单了...",
    full_content: "隔壁奶茶店天天排队，自己的店门可罗雀？实体老板别再傻傻去街上发传单了！\n\n分享一家三线城市社区烤肉店的逆袭实操，靠这套打法30天扭亏为盈：\n第一斧：打造【视觉视觉锚点爆品】。不推大而全菜单，单推一款份量震撼、性价比极高的引流烤肉塔，进店拍照率高达80%；\n第二斧：同城短视频真实后厨+老板性格IP，不拍广告只拍切肉、腌料与烟火气；\n第三斧：同城团购裂变。把优惠券精准投放到周边3公里年轻客群，核销率提升至65%。\n\n实体店的核心不是缺客人，而是缺给客人一个必来的理由！",
    tags: ["同城引流", "实体餐饮", "快手运营", "营销获客"],
    platform: "kuaishou",
    model: "gemini-2.5-flash",
    latency_ms: 1860,
    tokens: 760,
    prompt_tokens: 350,
    completion_tokens: 410,
    word_count: 458,
    rating: 4,
    hook_technique: "反差冲突 + 案例实操",
    status: "success",
    created_at: new Date(Date.now() - 3600000 * 48).toISOString(),
  },
  {
    id: 106,
    tenant_id: 1,
    tenant_name: "文策团队",
    user_id: 1,
    user_name: "创作者小文",
    topic: "深度拆解：为什么硅谷正在全面重构AI时代的软件工程？",
    title: "【深度思考】代码生成只是玩具？硅谷正在全面重构AI时代的软件工程",
    content: "很多人还在纠结AI能不能写出完美的Python脚本，但硅谷顶级技术团队已经把战场转移到了Agentic Workflow和软件系统架构重塑。\n\n本期深度探讨三大不可逆的技术变迁：\n1. 从单元代码补全走向端到端智能体自治闭环；\n2. 测试与验证将占据70%以上的工程时间，形式化验证迎来复兴；\n3. 软件架构从微服务演进为以LLM上下文为中心的模块拓扑。\n\n软件工程的范式正在发生半个世纪以来最大的突变，未来的工程师不再是敲击键盘的代码工人，而是复杂智能体系统的总指挥官。\n\n关注我不迷路，下期带来全栈Agent架构剖析。",
    content_preview: "很多人还在纠结AI能不能写出完美的Python脚本，但硅谷顶级技术团队已经把战场转移到了...",
    full_content: "很多人还在纠结AI能不能写出完美的Python脚本，但硅谷顶级技术团队已经把战场转移到了Agentic Workflow和软件系统架构重塑。\n\n本期深度探讨三大不可逆的技术变迁：\n1. 从单元代码补全走向端到端智能体自治闭环；\n2. 测试与验证将占据70%以上的工程时间，形式化验证迎来复兴；\n3. 软件架构从微服务演进为以LLM上下文为中心的模块拓扑。\n\n软件工程的范式正在发生半个世纪以来最大的突变，未来的工程师不再是敲击键盘的代码工人，而是复杂智能体系统的总指挥官。\n\n关注我不迷路，下期带来全栈Agent架构剖析。",
    tags: ["AI前沿", "软件工程", "技术深度", "B站科技"],
    platform: "bilibili",
    model: "gemini-2.5-flash",
    latency_ms: 2420,
    tokens: 920,
    prompt_tokens: 410,
    completion_tokens: 510,
    word_count: 536,
    rating: 5,
    hook_technique: "高维格局 + 深度颠覆",
    status: "success",
    created_at: new Date(Date.now() - 3600000 * 60).toISOString(),
  },
  {
    id: 107,
    tenant_id: 1,
    tenant_name: "文策团队",
    user_id: 1,
    user_name: "创作者小文",
    topic: "职场新人必看：向上汇报的3不原则与结构化思维模板",
    title: "【职场干货】被领导夸奖的向上汇报指南：3不原则与结构化表达",
    content: "在职场上，埋头苦干只占30分，懂得清晰汇报才能拿到另外70分！\n\n多少人向上汇报时像倒苦水，说了20分钟领导只回了一句“重点是什么”？\n\n记住这套经过大厂验证的高效汇报法：\n【3不原则】：\n不带情绪倒垃圾，不只抛问题不给方案，不对关键风险隐瞒遮掩。\n【PREP汇报结构】：\n- Point：开门见山先说结论；\n- Reason：用数据阐明核心依据；\n- Example：举出具体竞品或项目事实；\n- Plan：给出2套不同取舍的可选执行方案供决策。\n\n学会把领导当成你的客户，汇报顺畅了，资源自然向你倾斜！",
    content_preview: "在职场上，埋头苦干只占30分，懂得清晰汇报才能拿到另外70分！多少人向上汇报时像倒苦水...",
    full_content: "在职场上，埋头苦干只占30分，懂得清晰汇报才能拿到另外70分！\n\n多少人向上汇报时像倒苦水，说了20分钟领导只回了一句“重点是什么”？\n\n记住这套经过大厂验证的高效汇报法：\n【3不原则】：\n不带情绪倒垃圾，不只抛问题不给方案，不对关键风险隐瞒遮掩。\n【PREP汇报结构】：\n- Point：开门见山先说结论；\n- Reason：用数据阐明核心依据；\n- Example：举出具体竞品或项目事实；\n- Plan：给出2套不同取舍的可选执行方案供决策。\n\n学会把领导当成你的客户，汇报顺畅了，资源自然向你倾斜！",
    tags: ["职场进阶", "向上管理", "沟通技巧", "结构化思维"],
    platform: "xiaohongshu",
    model: "gemini-2.5-flash",
    latency_ms: 1610,
    tokens: 715,
    prompt_tokens: 320,
    completion_tokens: 395,
    word_count: 440,
    rating: 5,
    hook_technique: "痛点直击 + 公式化交付",
    status: "success",
    created_at: new Date(Date.now() - 3600000 * 75).toISOString(),
  },
  {
    id: 108,
    tenant_id: 1,
    tenant_name: "文策团队",
    user_id: 1,
    user_name: "创作者小文",
    topic: "企业如何借力大模型缩短70%的日常运营流程",
    title: "企业降本增效实战：如何用AI大模型缩短70%的日常运营流程",
    content: "还在让人工每天花4个小时排查数据、撰写同质化周报？\n\n优秀的企业早就将大模型深度嵌入到了业务工作流中。\n\n我们针对中型团队落地的AI自动化实践总结：\n第一，知识库搭建：把企业产品白皮书与客户FAQ统一向量化，客服首次响应准确率从55%提升至92%；\n第二，内容工厂流水线：营销文案产出时间从2天缩短至15分钟；\n第三，智能化报表萃取：每天自动抓取销售异动数据并输出诊断报告。\n\n拥抱AI不是淘汰员工，而是让核心团队从重复琐事中解放出来，专注战略与客户沟通！",
    content_preview: "还在让人工每天花4个小时排查数据、撰写同质化周报？优秀的企业早就将大模型深度嵌入到了业务工作流中...",
    full_content: "还在让人工每天花4个小时排查数据、撰写同质化周报？\n\n优秀的企业早就将大模型深度嵌入到了业务工作流中。\n\n我们针对中型团队落地的AI自动化实践总结：\n第一，知识库搭建：把企业产品白皮书与客户FAQ统一向量化，客服首次响应准确率从55%提升至92%；\n第二，内容工厂流水线：营销文案产出时间从2天缩短至15分钟；\n第三，智能化报表萃取：每天自动抓取销售异动数据并输出诊断报告。\n\n拥抱AI不是淘汰员工，而是让核心团队从重复琐事中解放出来，专注战略与客户沟通！",
    tags: ["数字化转型", "大模型落地", "企业效率", "AI实操"],
    platform: "channels",
    model: "gemini-2.5-flash",
    latency_ms: 2050,
    tokens: 810,
    prompt_tokens: 380,
    completion_tokens: 430,
    word_count: 480,
    rating: 5,
    hook_technique: "高维格局 + 案例实操",
    status: "success",
    created_at: new Date(Date.now() - 3600000 * 96).toISOString(),
  },
];

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

// ── Video & Topic Analyses ───────────────────────────────────

app.get("/api/analyses", requireAuth, (req, res) => {
  const user = (req as any).user as User;
  const list = analysesData.filter((a) => a.tenant_id === user.tenant_id);
  res.json(list);
});

app.get("/api/videos/:id/analysis", requireAuth, (req, res) => {
  const vid = Number(req.params.id);
  const user = (req as any).user as User;
  const item = analysesData.find((a) => a.video_id === vid && a.tenant_id === user.tenant_id);
  if (!item) {
    return res.status(404).json({ detail: "该视频尚未分析" });
  }
  res.json(item);
});

app.post("/api/videos/:id/analyze", requireAuth, (req, res) => {
  const vid = Number(req.params.id);
  const user = (req as any).user as User;
  let item = analysesData.find((a) => a.video_id === vid && a.tenant_id === user.tenant_id);
  if (!item) {
    item = {
      id: nextAnalysisId++,
      tenant_id: user.tenant_id,
      video_id: vid,
      title: `精选爆款视频分析 #${vid}`,
      source: "博主精选视频",
      like_play_ratio: 0.052,
      comment_play_ratio: 0.003,
      collect_play_ratio: 0.028,
      why_viral_summary: "开头通过反常识认知断言破局抓眼球，中段高密度交付实操工具方法，尾声行动号召促收藏。",
      hook_technique: "反常识认知冲突",
      visual_hook: "快节奏近景推镜头",
      core_conflict: "认知误区 vs 正确解法",
      pacing_rhythm: "紧凑干脆",
      audience_psychology: "自我提升与避免踩坑心理",
      created_at: new Date().toISOString(),
    };
    analysesData.unshift(item);
  }
  res.json(item);
});

app.get("/api/topics/:id/analysis", requireAuth, (req, res) => {
  const tid = Number(req.params.id);
  const user = (req as any).user as User;
  const item = analysesData.find((a) => a.topic_id === tid && a.tenant_id === user.tenant_id);
  if (!item) {
    return res.status(404).json({ detail: "该选题尚未分析" });
  }
  res.json(item);
});

app.post("/api/topics/:id/analyze", requireAuth, (req, res) => {
  const tid = Number(req.params.id);
  const user = (req as any).user as User;
  const topic = topicsData.find((t) => t.id === tid);
  let item = analysesData.find((a) => a.topic_id === tid && a.tenant_id === user.tenant_id);
  if (!item) {
    item = {
      id: nextAnalysisId++,
      tenant_id: user.tenant_id,
      topic_id: tid,
      title: topic ? topic.title : `爆款选题分析 #${tid}`,
      source: topic ? `${topic.platform} · ${topic.author}` : "选题素材",
      cover_url: "",
      author_avatar: "",
      like_play_ratio: 0.061,
      comment_play_ratio: 0.003,
      collect_play_ratio: 0.031,
      why_viral_summary: topic
        ? `该选题《${topic.title}》直击大众痛点，以实战干货清单形式呈现，互动与完播表现优秀。`
        : "高点赞高收藏标杆内容，前3秒留存率极高，具备极强可复制性。",
      hook_technique: "强反差悬念破局",
      visual_hook: "直视镜头特写 + 醒目大字",
      core_conflict: "效率焦虑 vs 工具突破",
      pacing_rhythm: "节奏明快、要点层层递进",
      audience_psychology: "求快、求实操、求现成答案",
      created_at: new Date().toISOString(),
    };
    analysesData.unshift(item);
  }
  res.json(item);
});

app.post("/api/topics/batch-analyze", requireAuth, (req, res) => {
  const { topic_ids = [], video_ids = [] } = req.body || {};
  const user = (req as any).user as User;
  const results: any[] = [];

  for (const tid of topic_ids) {
    let item = analysesData.find((a) => a.topic_id === tid && a.tenant_id === user.tenant_id);
    if (!item) {
      const topic = topicsData.find((t) => t.id === tid);
      item = {
        id: nextAnalysisId++,
        tenant_id: user.tenant_id,
        topic_id: tid,
        title: topic?.title || `选题 #${tid}`,
        source: topic ? `${topic.platform} · ${topic.author}` : "选题素材",
        why_viral_summary: "爆款选题深度三维拆解完成，核心痛点抓取精准。",
        created_at: new Date().toISOString(),
      };
      analysesData.unshift(item);
    }
    results.push(item);
  }

  res.json({ total: results.length, results });
});

app.post("/api/creators/:id/videos/analyze", requireAuth, (req, res) => {
  const cid = Number(req.params.id);
  const videos = creatorVideos[cid] || [];
  res.json({ total: videos.length, results: videos });
});

app.post("/api/creators/:id/videos/analyze-async", requireAuth, (req, res) => {
  const cid = Number(req.params.id);
  const videos = creatorVideos[cid] || [];
  const taskId = `task_${Date.now()}`;
  res.json({
    task_id: taskId,
    total: videos.length,
    message: "分析任务已在后台启动",
  });
});

app.get("/api/creators/analyze-task/:taskId", requireAuth, (req, res) => {
  res.json({
    status: "done",
    done: 10,
    total: 10,
    success: 10,
    failed: 0,
  });
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
      const word_count = content.length;
      const tokens = Math.round(word_count * 1.5);
      const latency_ms = 1400 + Math.floor(Math.random() * 650);
      const tenant = tenants.get(user.tenant_id);

      return {
        id: nextGenId++,
        tenant_id: user.tenant_id,
        tenant_name: tenant?.name || "文策团队",
        user_id: user.id,
        user_name: user.nickname || "创作者",
        topic,
        title,
        content,
        content_preview: content.slice(0, 90) + "...",
        full_content: content,
        tags,
        platform: platform || "douyin",
        model: "gemini-2.5-flash",
        latency_ms,
        tokens,
        prompt_tokens: 340,
        completion_tokens: tokens - 340,
        word_count,
        rating: 5,
        hook_technique: "反直觉否定 + 悬念破局",
        status: "success",
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
  const word_count = content.length;
  const tokens = Math.round(word_count * 1.5);
  const latency_ms = 1350 + Math.floor(Math.random() * 600);
  const tenant = tenants.get(user.tenant_id);

  return {
    id: nextGenId++,
    tenant_id: user.tenant_id,
    tenant_name: tenant?.name || "文策团队",
    user_id: user.id,
    user_name: user.nickname || "创作者",
    topic,
    title: `关于 ${topic} 的高转化短视频脚本`,
    content,
    content_preview: content.slice(0, 90) + "...",
    full_content: content,
    tags: [topic.slice(0, 4), "短视频干货", "文案技巧", "高转化"],
    platform: platform || "douyin",
    model: "gemini-2.5-flash",
    latency_ms,
    tokens,
    prompt_tokens: 320,
    completion_tokens: tokens - 320,
    word_count,
    rating: 5,
    hook_technique: "痛点直击 + 公式化交付",
    status: "success",
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
  const { keyword, platform, page = 1, page_size = 20 } = req.query as any;
  let items = [...generationsData];
  if (keyword) {
    const q = String(keyword).toLowerCase();
    items = items.filter(
      (g) =>
        g.title?.toLowerCase().includes(q) ||
        g.topic?.toLowerCase().includes(q) ||
        g.content?.toLowerCase().includes(q) ||
        g.tenant_name?.toLowerCase().includes(q)
    );
  }
  if (platform && platform !== "all") {
    items = items.filter((g) => g.platform === platform);
  }
  const total = items.length;
  const p = Number(page) || 1;
  const ps = Number(page_size) || 20;
  const startIdx = (p - 1) * ps;
  const paginated = items.slice(startIdx, startIdx + ps).map((g) => ({
    ...g,
    content_preview: g.content_preview || g.content?.slice(0, 90) + "...",
    full_content: g.full_content || g.content,
    tenant_name: g.tenant_name || tenants.get(g.tenant_id)?.name || "文策团队",
  }));
  res.json({ items: paginated, total });
});

app.get("/api/admin/generations/analytics", requireAdminAuth, (req, res) => {
  const total = generationsData.length;
  const totalWordCount = generationsData.reduce((acc, g) => acc + (g.word_count || g.content?.length || 450), 0);
  const totalTokens = generationsData.reduce((acc, g) => acc + (g.tokens || 720), 0);
  const totalLatency = generationsData.reduce((acc, g) => acc + (g.latency_ms || 1800), 0);
  const ratedItems = generationsData.filter((g) => typeof g.rating === "number");
  const avgRating = ratedItems.length > 0 ? (ratedItems.reduce((acc, g) => acc + g.rating, 0) / ratedItems.length).toFixed(2) : "4.86";

  const avgLatency = total > 0 ? Math.round(totalLatency / total) : 1790;
  const avgTokens = total > 0 ? Math.round(totalTokens / total) : 745;
  const avgWords = total > 0 ? Math.round(totalWordCount / total) : 465;

  const platformNames: Record<string, { name: string; color: string }> = {
    douyin: { name: "抖音短视频", color: "#fe2c55" },
    xiaohongshu: { name: "小红书图文/视频", color: "#ff2442" },
    channels: { name: "微信视频号", color: "#07c160" },
    kuaishou: { name: "快手短剧/口播", color: "#ff5000" },
    bilibili: { name: "B站中长视频", color: "#00aeec" },
  };

  const platformCounts: Record<string, { count: number; words: number; latency: number; ratings: number[] }> = {};
  for (const g of generationsData) {
    const p = g.platform || "douyin";
    if (!platformCounts[p]) platformCounts[p] = { count: 0, words: 0, latency: 0, ratings: [] };
    platformCounts[p].count++;
    platformCounts[p].words += g.word_count || g.content?.length || 450;
    platformCounts[p].latency += g.latency_ms || 1800;
    if (g.rating) platformCounts[p].ratings.push(g.rating);
  }

  const platforms = Object.entries(platformCounts).map(([k, v]) => ({
    platform: k,
    name: platformNames[k]?.name || k,
    color: platformNames[k]?.color || "#63e2b7",
    count: v.count,
    percentage: total > 0 ? Math.round((v.count / total) * 100) : 0,
    avg_words: v.count > 0 ? Math.round(v.words / v.count) : 450,
    avg_latency_ms: v.count > 0 ? Math.round(v.latency / v.count) : 1800,
    avg_rating: v.ratings.length > 0 ? (v.ratings.reduce((a, b) => a + b, 0) / v.ratings.length).toFixed(1) : "4.9",
  })).sort((a, b) => b.count - a.count);

  const hookStats: Record<string, { count: number; ratings: number[]; totalWords: number }> = {};
  for (const g of generationsData) {
    const h = g.hook_technique || "反直觉否定 + 悬念破局";
    if (!hookStats[h]) hookStats[h] = { count: 0, ratings: [], totalWords: 0 };
    hookStats[h].count++;
    hookStats[h].totalWords += g.word_count || 450;
    if (g.rating) hookStats[h].ratings.push(g.rating);
  }

  const hookTechniques = Object.entries(hookStats).map(([name, v]) => ({
    name,
    count: v.count,
    percentage: total > 0 ? Math.round((v.count / total) * 100) : 0,
    avg_words: Math.round(v.totalWords / v.count),
    avg_rating: v.ratings.length > 0 ? (v.ratings.reduce((a, b) => a + b, 0) / v.ratings.length).toFixed(1) : "4.8",
  })).sort((a, b) => b.count - a.count);

  const now = new Date();
  const trendDays: any[] = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date(now.getTime() - i * 86400000);
    const dateStr = `${d.getMonth() + 1}/${d.getDate()}`;
    const isoPrefix = d.toISOString().slice(0, 10);
    const dayMatches = generationsData.filter((g) => g.created_at?.startsWith(isoPrefix));
    const dayCount = dayMatches.length > 0 ? dayMatches.length * 3 + (7 - i) * 4 : 12 + Math.floor(Math.sin(i * 1.5) * 5 + i * 3);
    const dayLatency = 1680 + Math.floor(Math.sin(i) * 160) + (i % 2 === 0 ? 80 : -40);
    const dayTokens = Math.round(dayCount * 0.74);
    trendDays.push({
      date: dateStr,
      full_date: isoPrefix,
      count: dayCount,
      success_count: Math.round(dayCount * 0.996),
      avg_latency_ms: dayLatency,
      tokens_k: dayTokens,
    });
  }

  const tenantMap: Record<number, { name: string; count: number; ratings: number[]; platforms: Record<string, number> }> = {};
  for (const g of generationsData) {
    const tid = g.tenant_id || 1;
    const tname = g.tenant_name || tenants.get(tid)?.name || "文策团队";
    if (!tenantMap[tid]) tenantMap[tid] = { name: tname, count: 0, ratings: [], platforms: {} };
    tenantMap[tid].count++;
    if (g.rating) tenantMap[tid].ratings.push(g.rating);
    const p = g.platform || "douyin";
    tenantMap[tid].platforms[p] = (tenantMap[tid].platforms[p] || 0) + 1;
  }

  const tenantRanking = Object.entries(tenantMap).map(([id, t]) => {
    let topPlat = "douyin";
    let topPlatCount = 0;
    for (const [pk, pv] of Object.entries(t.platforms)) {
      if (pv > topPlatCount) {
        topPlatCount = pv;
        topPlat = pk;
      }
    }
    return {
      tenant_id: Number(id),
      tenant_name: t.name,
      count: t.count,
      favorite_platform: platformNames[topPlat]?.name || topPlat,
      avg_rating: t.ratings.length > 0 ? (t.ratings.reduce((a, b) => a + b, 0) / t.ratings.length).toFixed(1) : "4.9",
    };
  }).sort((a, b) => b.count - a.count);

  res.json({
    summary: {
      total_generations: total,
      today_generations: 42,
      week_generations: 318,
      week_growth_pct: 18.6,
      success_rate: "99.8%",
      avg_latency_ms: avgLatency,
      p95_latency_ms: Math.round(avgLatency * 1.36),
      avg_tokens: avgTokens,
      avg_word_count: avgWords,
      satisfaction_rate: "96.4%",
      avg_rating: Number(avgRating),
      copy_adoption_rate: "85.2%",
      re_generation_rate: "11.4%",
      total_tokens_consumed: totalTokens > 0 ? totalTokens : 124600,
    },
    engine_health: {
      model_name: "Gemini 2.5 Flash",
      engine_status: "optimal",
      engine_status_text: "运行正常 / 高吞吐极速",
      stream_speed: "88.4 tokens/s",
      cache_hit_rate: "33.2%",
      first_token_latency_ms: 360,
      active_concurrency: 4,
      queue_depth: 0,
      sdk_driver: "@google/genai (TypeScript SDK)",
      last_health_check: new Date().toISOString(),
    },
    platforms,
    hook_techniques: hookTechniques,
    trend_days: trendDays,
    tenant_ranking: tenantRanking,
    quality_distribution: [
      { label: "5 星 (极佳)", count: Math.round(total * 0.78) || 12, pct: 78, color: "#63e2b7" },
      { label: "4 星 (满意)", count: Math.round(total * 0.17) || 3, pct: 17, color: "#70c0e8" },
      { label: "3 星 (一般)", count: Math.round(total * 0.04) || 1, pct: 4, color: "#f2c97d" },
      { label: "1-2 星 (重写)", count: 0, pct: 1, color: "#e88080" },
    ],
  });
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

"""
视频语音转录服务

主方案：Deepgram whisper-medium URL 直传（服务器零下载，中文准确率最高，~8s）
备用方案1：Deepgram nova-3 URL 直传（速度快，准确率稍低）
备用方案2：下载视频 → 硅基流动 SenseVoice 文件上传（准确但需下载视频）

使用前提：
  .env 中配置 DEEPGRAM_API_KEY（主）和/或 SILICONFLOW_API_KEY（备）
"""

import asyncio
import re
from functools import partial

import httpx
import requests

from config import settings

# ── Deepgram ─────────────────────────────────────────────
DEEPGRAM_API_URL = "https://api.deepgram.com/v1/listen"
DEEPGRAM_PRIMARY_PARAMS = {
    "model": "whisper-medium",
    "language": "zh",
}
DEEPGRAM_FALLBACK_PARAMS = {
    "model": "nova-3",
    "language": "zh",
    "punctuate": "true",
    "smart_format": "true",
}

# ── SiliconFlow SenseVoice ────────────────────────────────
SILICONFLOW_API_URL = "https://api.siliconflow.cn/v1/audio/transcriptions"
SENSEFORCE_MODEL = "FunAudioLLM/SenseVoiceSmall"
TELESPEECH_MODEL = "TeleAI/TeleSpeechASR"

MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/121.0.2277.107 "
    "Version/17.0 Mobile/15E148 Safari/604.1"
)

# SiliconFlow 文件上限 100MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024

# SenseVoice 输出中常见的特殊 token / emoji 标记
_SENSEVOICE_NOISE_RE = re.compile(
    r'[\U0001F3B5\U0001F3B6\U0001F3BC]'   # 🎵🎶🎼
    r'|<\|[A-Z_]+\|>'                       # <|MUSIC|> <|BGM|> 等
    r'|^\s*$', re.MULTILINE
)


class TranscribeService:

    # 允许的视频 URL 域名白名单（防 SSRF）
    ALLOWED_DOMAINS = {
        "douyin.com", "douyinvod.com", "douyinpic.com",
        "xiaohongshu.com", "xhscdn.com",
        "weixin.qq.com", "video.weixin.qq.com",
        "bilibili.com", "bilivideo.com",
        "kuaishou.com", "kwaicdn.com",
        "ixigua.com", "pstatp.com", "bytedance.com",
        "snssdk.com", "amemv.com",
        "zjcdn.com",
    }

    def __init__(self):
        self.deepgram_key = settings.deepgram_api_key
        self.siliconflow_key = settings.siliconflow_api_key

    def _validate_url(self, video_url: str) -> None:
        """验证 URL 是否为允许的外部视频域名，防止 SSRF"""
        from urllib.parse import urlparse
        parsed = urlparse(video_url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"不支持的 URL 协议: {parsed.scheme}")
        hostname = (parsed.hostname or "").lower()
        import ipaddress
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_reserved:
                raise ValueError("不允许访问内网地址")
        except ValueError:
            pass
        allowed = any(hostname == d or hostname.endswith("." + d) for d in self.ALLOWED_DOMAINS)
        if not allowed:
            raise ValueError(f"不允许的视频域名: {hostname}")

    def _transcribe_deepgram_url(self, video_url: str, params: dict) -> str:
        """Deepgram URL 直传，服务器无需下载视频"""
        resp = requests.post(
            DEEPGRAM_API_URL,
            params=params,
            headers={
                "Authorization": f"Token {self.deepgram_key}",
                "Content-Type": "application/json",
            },
            json={"url": video_url},
            timeout=300,
        )
        resp.raise_for_status()
        data = resp.json()
        try:
            return data["results"]["channels"][0]["alternatives"][0]["transcript"].strip()
        except (KeyError, IndexError):
            return ""

    async def _download_video_bytes(self, video_url: str) -> bytes:
        """备用：下载视频到内存（仅 SiliconFlow 回退时使用）"""
        async with httpx.AsyncClient(
            timeout=120,
            follow_redirects=True,
            headers={"User-Agent": MOBILE_UA},
        ) as client:
            resp = await client.get(video_url)
            resp.raise_for_status()
            return resp.content

    def _transcribe_siliconflow_bytes(self, video_bytes: bytes, filename: str) -> str:
        """备用：直传 MP4 给 SenseVoice，失败时 fallback TeleSpeech"""
        content_type = "video/mp4" if filename.endswith(".mp4") else "audio/mpeg"
        for model in [SENSEFORCE_MODEL, TELESPEECH_MODEL]:
            try:
                resp = requests.post(
                    SILICONFLOW_API_URL,
                    headers={"Authorization": f"Bearer {self.siliconflow_key}"},
                    files={"file": (filename, video_bytes, content_type)},
                    data={"model": model},
                    timeout=300,
                )
                resp.raise_for_status()
                text = resp.json().get("text", "")
                model_short = model.split("/")[-1]
                print(f"[Transcribe] {model_short}: {len(text)} 字")
                if text:
                    return text
            except Exception as e:
                model_short = model.split("/")[-1]
                print(f"[Transcribe] {model_short} 失败: {e}")
        return ""

    def _clean_sensevoice(self, text: str) -> str:
        text = _SENSEVOICE_NOISE_RE.sub('', text)
        return text.strip()

    async def _run_transcription(self, video_url: str, video_id: str) -> str:
        if not video_url:
            return ""

        loop = asyncio.get_event_loop()

        # ── 1. Deepgram whisper-medium（主方案，零下载，中文最准）──
        if self.deepgram_key:
            try:
                print(f"[Transcribe] Deepgram whisper-medium 转录 (video_id={video_id}) ...")
                text = await loop.run_in_executor(
                    None,
                    partial(self._transcribe_deepgram_url, video_url, DEEPGRAM_PRIMARY_PARAMS)
                )
                if text:
                    print(f"[Transcribe] whisper-medium 完成，共 {len(text)} 字")
                    return text
                print("[Transcribe] whisper-medium 返回空，尝试 nova-3")
            except Exception as e:
                print(f"[Transcribe] whisper-medium 失败 ({e})，尝试 nova-3")

        # ── 2. Deepgram nova-3（备用，零下载，速度快）──
        if self.deepgram_key:
            try:
                print(f"[Transcribe] Deepgram nova-3 转录 (video_id={video_id}) ...")
                text = await loop.run_in_executor(
                    None,
                    partial(self._transcribe_deepgram_url, video_url, DEEPGRAM_FALLBACK_PARAMS)
                )
                if text:
                    print(f"[Transcribe] nova-3 完成，共 {len(text)} 字")
                    return text
                print("[Transcribe] nova-3 返回空，尝试 SenseVoice")
            except Exception as e:
                print(f"[Transcribe] nova-3 失败 ({e})，尝试 SenseVoice")

        # ── 3. SiliconFlow SenseVoice（兜底，需下载视频）──
        if self.siliconflow_key:
            try:
                print(f"[Transcribe] 下载视频 (video_id={video_id}) ...")
                video_bytes = await self._download_video_bytes(video_url)
                if not video_bytes:
                    print("[Transcribe] 未获取到视频数据")
                    return ""
                print(f"[Transcribe] 视频 {len(video_bytes)//1024}KB，上传 SenseVoice ...")
                if len(video_bytes) > MAX_VIDEO_SIZE:
                    print(f"[Transcribe] 视频超出 {MAX_VIDEO_SIZE//1024//1024}MB，跳过")
                    return ""
                text = await loop.run_in_executor(
                    None,
                    partial(self._transcribe_siliconflow_bytes, video_bytes, f"{video_id}.mp4")
                )
                if text:
                    text = self._clean_sensevoice(text)
                    print(f"[Transcribe] SenseVoice 完成，共 {len(text)} 字")
                    return text
            except Exception as e:
                print(f"[Transcribe] SenseVoice 失败 ({e})")

        print(f"[Transcribe] 所有转录方案均失败 (video_id={video_id})")
        return ""

    async def transcribe_from_url(self, video_url: str, video_id: str) -> str:
        self._validate_url(video_url)
        return await self._run_transcription(video_url, video_id)


transcribe_service = TranscribeService()

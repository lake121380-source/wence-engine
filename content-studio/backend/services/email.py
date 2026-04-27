"""
邮件服务：发送注册邮箱验证邮件
"""
from email.message import EmailMessage
from email.utils import formataddr
import smtplib

from config import settings


def is_email_service_configured() -> bool:
    return bool(settings.smtp_host and settings.email_from)


def send_verification_email(to_email: str, nickname: str, verify_url: str):
    """发送邮箱验证邮件，失败抛出异常。"""
    if not is_email_service_configured():
        raise RuntimeError("邮件服务未配置：请设置 SMTP_HOST 与 EMAIL_FROM")

    display_name = nickname or to_email.split("@")[0]
    subject = "请验证你的邮箱 - 文策引擎"
    text = (
        f"你好，{display_name}：\n\n"
        "感谢注册文策引擎。\n"
        "请点击下方链接完成邮箱验证（24小时内有效）：\n"
        f"{verify_url}\n\n"
        "如果不是你本人操作，请忽略本邮件。\n"
    )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((settings.email_from_name, settings.email_from))
    msg["To"] = to_email
    msg.set_content(text)

    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)

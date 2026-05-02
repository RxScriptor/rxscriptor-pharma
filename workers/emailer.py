"""Gmail SMTP digest sender.

Uses an App Password (not the account password). Generate at:
  myaccount.google.com → Security → 2-step verification → App passwords
"""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

DEFAULT_TEMPLATE_DIR = Path(__file__).parent / "templates"


def render_digest_html(
    digest: dict,
    template_name: str = "digest.html",
    template_dir: Path = DEFAULT_TEMPLATE_DIR,
) -> str:
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template(template_name)
    return template.render(**digest)


def _build_plain_body(digest: dict) -> str:
    lines = [digest.get("trend_summary_ko", ""), ""]
    for h in digest.get("highlights", []):
        lines.append(f"- [{h.get('source', '')}] {h.get('title', '')}")
        if h.get("ko_summary"):
            lines.append(f"  {h['ko_summary']}")
        if h.get("link"):
            lines.append(f"  {h['link']}")
        lines.append("")
    return "\n".join(lines)


def send_digest_email(
    digest: dict,
    recipients: Iterable[str],
    smtp_user: str,
    smtp_password: str,
    subject_prefix: str = "[RxScriptor]",
    smtp_host: str = "smtp.gmail.com",
    smtp_port: int = 465,
) -> None:
    """Send the digest as a Gmail HTML+plain multipart email."""
    recipients = [r.strip() for r in recipients if r and r.strip()]
    if not recipients:
        raise ValueError("No recipients provided")

    html_body = render_digest_html(digest)
    plain_body = _build_plain_body(digest)
    date_label = (digest.get("generated_at") or "")[:10]

    msg = EmailMessage()
    msg["Subject"] = f"{subject_prefix} {date_label} 제약 다이제스트"
    msg["From"] = smtp_user
    msg["To"] = ", ".join(recipients)
    msg.set_content(plain_body, charset="utf-8")
    msg.add_alternative(html_body, subtype="html", charset="utf-8")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
    logger.info("digest email sent to %d recipient(s)", len(recipients))

"""SMTP email delivery for meeting invites."""

from __future__ import annotations

import asyncio
import logging
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import get_settings
from app.services.meeting_invites import format_meeting_id

logger = logging.getLogger(__name__)


def _format_scheduled_at(scheduled_at: datetime | None) -> str:
    if scheduled_at is None:
        return "Join anytime — your meeting is ready now."
    dt = scheduled_at
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return f"Scheduled for {dt.astimezone(timezone.utc).strftime('%B %d, %Y at %I:%M %p UTC')}"


def _build_email_bodies(
    prospect_name: str,
    meeting_id: str,
    passcode: str,
    join_url: str,
    scheduled_at: datetime | None,
    company_name: str,
) -> tuple[str, str]:
    formatted_id = format_meeting_id(meeting_id)
    schedule_line = _format_scheduled_at(scheduled_at)

    text = f"""Hi {prospect_name},

Your AI sales agent meeting with {company_name} is ready.

Meeting ID: {formatted_id}
Passcode: {passcode}
{schedule_line}

Join with this link (one-time use):
{join_url}

Or go to the join page and enter your Meeting ID and Passcode manually.

This link can only be used once. If you already joined, request a new meeting from our website.

— {company_name}
"""

    html = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; color: #1e293b; line-height: 1.6;">
  <p>Hi {prospect_name},</p>
  <p>Your AI sales agent meeting with <strong>{company_name}</strong> is ready.</p>
  <table style="margin: 20px 0; border-collapse: collapse;">
    <tr><td style="padding: 6px 12px; color: #64748b;">Meeting ID</td>
        <td style="padding: 6px 12px; font-size: 20px; font-weight: bold; letter-spacing: 2px;">{formatted_id}</td></tr>
    <tr><td style="padding: 6px 12px; color: #64748b;">Passcode</td>
        <td style="padding: 6px 12px; font-size: 18px; font-weight: bold;">{passcode}</td></tr>
  </table>
  <p style="color: #64748b;">{schedule_line}</p>
  <p>
    <a href="{join_url}"
       style="display: inline-block; background: #4f46e5; color: white; padding: 12px 24px;
              text-decoration: none; border-radius: 8px; font-weight: bold;">
      Join Meeting
    </a>
  </p>
  <p style="font-size: 13px; color: #94a3b8;">
    Or enter your Meeting ID and Passcode on the join page.<br>
    This link can only be used once.
  </p>
  <p>— {company_name}</p>
</body>
</html>"""

    return text, html


def _send_smtp_sync(to_email: str, subject: str, text_body: str, html_body: str) -> None:
    settings = get_settings()
    if not settings.smtp_host or not settings.smtp_from_email:
        raise RuntimeError("SMTP is not configured. Set SMTP_HOST and SMTP_FROM_EMAIL.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    msg["To"] = to_email
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    if settings.smtp_use_tls:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.smtp_from_email, [to_email], msg.as_string())
    else:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.smtp_from_email, [to_email], msg.as_string())


def _build_details_email_bodies(
    prospect_name: str,
    detail_type: str,
    brochure_url: str,
    company_name: str,
) -> tuple[str, str]:
    """Build plain + HTML bodies for a resort details email."""
    detail_label = detail_type.replace("_", " ").title()

    text = f"""Hi {prospect_name},

Thank you for your interest in {detail_label} at InterContinental Maldives Maamunagau Resort!

Here are the details you requested:

Planet Trekkers Kids Club offers a programme of tailored services and activities for children aged 4-12 years old. The programme connects families with their island location and supports children's growth, curiosity, and creativity.

Highlights:
- Spacious indoor space with a library, arts & crafts area
- Outdoor area with splash pool, garden, and climbing frame
- Activities: nature walks, palm weaving, cooking classes, water sports, marine biology sessions
- Opening hours: 9:00 AM - 6:00 PM
- Babysitting available (24hr advance booking)

View the full brochure here: {brochure_url}

For reservations and enquiries:
Tel: +960 658 0500
WhatsApp (24/7): +960 730 9300
Email: reservations.icmaldives@ihg.com

We look forward to welcoming your family!

— {company_name}
"""

    html = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; color: #1e293b; line-height: 1.6;">
  <p>Hi {prospect_name},</p>
  <p>Thank you for your interest in <strong>{detail_label}</strong> at InterContinental Maldives Maamunagau Resort!</p>

  <h3 style="color: #4f46e5;">Planet Trekkers Kids Club</h3>
  <p>Planet Trekkers offers a programme of tailored services and activities for children aged 4-12 years old,
  connecting families with their island location and supporting children's growth, curiosity, and creativity.</p>

  <h4>Highlights:</h4>
  <ul>
    <li>Spacious indoor space with library, arts &amp; crafts area</li>
    <li>Outdoor area with splash pool, garden, and climbing frame</li>
    <li>Activities: nature walks, palm weaving, cooking classes, water sports, marine biology sessions</li>
    <li>Opening hours: 9:00 AM - 6:00 PM</li>
    <li>Babysitting available (24hr advance booking)</li>
  </ul>

  <p>
    <a href="{brochure_url}"
       style="display: inline-block; background: #4f46e5; color: white; padding: 12px 24px;
              text-decoration: none; border-radius: 8px; font-weight: bold;">
      View Full Brochure
    </a>
  </p>

  <p style="margin-top: 24px; font-size: 14px; color: #64748b;">
    <strong>Reservations &amp; Enquiries:</strong><br>
    Tel: +960 658 0500<br>
    WhatsApp (24/7): +960 730 9300<br>
    Email: reservations.icmaldives@ihg.com
  </p>

  <p>We look forward to welcoming your family!</p>
  <p>— {company_name}</p>
</body>
</html>"""

    return text, html


async def send_details_email(
    to_email: str,
    prospect_name: str,
    detail_type: str = "planet_trekkers",
    brochure_url: str = "",
    company_name: str = "InterContinental Maldives",
) -> None:
    """Send resort details (e.g. Planet Trekkers brochure) to a guest."""
    detail_label = detail_type.replace("_", " ").title()
    subject = f"{detail_label} — InterContinental Maldives"
    text_body, html_body = _build_details_email_bodies(
        prospect_name=prospect_name,
        detail_type=detail_type,
        brochure_url=brochure_url,
        company_name=company_name,
    )
    await asyncio.to_thread(_send_smtp_sync, to_email, subject, text_body, html_body)
    logger.info("Details email (%s) sent to %s", detail_type, to_email)


async def send_meeting_invite_email(
    to_email: str,
    prospect_name: str,
    meeting_id: str,
    passcode: str,
    join_url: str,
    scheduled_at: datetime | None,
    company_name: str = "Avatar Sales Agent",
) -> None:
    subject = (
        f"Your meeting with {company_name} is scheduled"
        if scheduled_at
        else f"Your meeting with {company_name} is ready"
    )
    text_body, html_body = _build_email_bodies(
        prospect_name=prospect_name,
        meeting_id=meeting_id,
        passcode=passcode,
        join_url=join_url,
        scheduled_at=scheduled_at,
        company_name=company_name,
    )
    await asyncio.to_thread(_send_smtp_sync, to_email, subject, text_body, html_body)
    logger.info("Meeting invite email sent to %s", to_email)

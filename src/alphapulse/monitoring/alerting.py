import os
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    level: AlertLevel
    title: str
    message: str
    metadata: Optional[Dict[str, Any]] = None


class AlertHandler(ABC):
    @abstractmethod
    def send(self, alert: Alert) -> bool:
        pass


class SlackAlertHandler(AlertHandler):
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")

    def send(self, alert: Alert) -> bool:
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False

        try:
            import requests

            emoji = {
                AlertLevel.INFO: ":information_source:",
                AlertLevel.WARNING: ":warning:",
                AlertLevel.ERROR: ":x:",
                AlertLevel.CRITICAL: ":rotating_light:",
            }
            payload = {
                "text": f"{emoji.get(alert.level, ':bell:')} *{alert.level.value.upper()}*: {alert.title}",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{emoji.get(alert.level, ':bell:')} {alert.title}",
                        },
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": alert.message},
                    },
                ],
            }
            if alert.metadata:
                fields = [
                    {"type": "mrkdwn", "text": f"*{k}:* {v}"}
                    for k, v in alert.metadata.items()
                ]
                payload["blocks"].append({"type": "section", "fields": fields[:10]})

            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False


class EmailAlertHandler(AlertHandler):
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        sender: Optional[str] = None,
        recipients: Optional[list] = None,
    ):
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST")
        self.smtp_port = smtp_port
        self.sender = sender or os.getenv("ALERT_SENDER")
        self.recipients = recipients or os.getenv("ALERT_RECIPIENTS", "").split(",")

    def send(self, alert: Alert) -> bool:
        if not self.smtp_host or not self.sender or not self.recipients:
            logger.warning("Email configuration incomplete")
            return False

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg["From"] = self.sender
            msg["To"] = ", ".join(self.recipients)
            msg["Subject"] = f"[AlphaPulse {alert.level.value.upper()}] {alert.title}"

            body = f"""
{alert.title}
{"=" * len(alert.title)}

Level: {alert.level.value.upper()}
Message: {alert.message}

"""
            if alert.metadata:
                body += "Additional Information:\n"
                for k, v in alert.metadata.items():
                    body += f"  - {k}: {v}\n"

            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                password = os.getenv("SMTP_PASSWORD")
                if password:
                    server.login(self.sender, password)
                server.sendmail(self.sender, self.recipients, msg.as_string())

            return True
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False


class ConsoleAlertHandler(AlertHandler):
    def send(self, alert: Alert) -> bool:
        prefix = {
            AlertLevel.INFO: "\033[94mINFO\033[0m",
            AlertLevel.WARNING: "\033[93mWARN\033[0m",
            AlertLevel.ERROR: "\033[91mERROR\033[0m",
            AlertLevel.CRITICAL: "\033[91mCRITICAL\033[0m",
        }
        print(f"{prefix.get(alert.level, 'INFO')}: {alert.title}")
        print(f"{alert.message}")
        if alert.metadata:
            for k, v in alert.metadata.items():
                print(f"  {k}: {v}")
        return True


class AlertManager:
    def __init__(self):
        self.handlers: list[AlertHandler] = []

    def add_handler(self, handler: AlertHandler) -> "AlertManager":
        self.handlers.append(handler)
        return self

    def add_slack(self, webhook_url: Optional[str] = None) -> "AlertManager":
        self.handlers.append(SlackAlertHandler(webhook_url))
        return self

    def add_email(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        sender: Optional[str] = None,
        recipients: Optional[list] = None,
    ) -> "AlertManager":
        self.handlers.append(
            EmailAlertHandler(smtp_host, smtp_port, sender, recipients)
        )
        return self

    def add_console(self) -> "AlertManager":
        self.handlers.append(ConsoleAlertHandler())
        return self

    def send_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        alert = Alert(level, title, message, metadata)
        success = True
        for handler in self.handlers:
            try:
                result = handler.send(alert)
                if not result:
                    success = False
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
                success = False
        return success


alert_manager = AlertManager()

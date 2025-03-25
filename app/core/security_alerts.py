"""
Security alerts system for the application.
This module provides functionality to detect and alert on suspicious security events.
"""

import logging
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
from pathlib import Path

from app.core.config import SETTINGS

# Setup logging
logger = logging.getLogger("app.core.security_alerts")

# Security events log file
SECURITY_LOG_DIR = Path(os.getenv("SECURITY_LOG_DIR", "logs/security"))
SECURITY_LOG_FILE = SECURITY_LOG_DIR / "security_events.log"

# Ensure the security log directory exists
os.makedirs(SECURITY_LOG_DIR, exist_ok=True)

# Alert thresholds
LOGIN_FAILURE_THRESHOLD = 5  # Number of failed logins before alerting
SUSPICIOUS_IP_THRESHOLD = 3  # Number of different usernames from same IP before alerting
TIME_WINDOW_MINUTES = 10     # Time window for counting events (in minutes)


class SecurityEvent:
    """
    Represents a security event in the system
    """
    def __init__(
        self,
        event_type: str,
        severity: str,
        source_ip: str,
        username: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        self.event_type = event_type
        self.severity = severity
        self.source_ip = source_ip
        self.username = username
        self.user_agent = user_agent
        self.details = details or {}
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the event to a dictionary
        """
        return {
            "event_type": self.event_type,
            "severity": self.severity,
            "source_ip": self.source_ip,
            "username": self.username,
            "user_agent": self.user_agent,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        """
        Convert the event to a JSON string
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecurityEvent':
        """
        Create a SecurityEvent from a dictionary
        """
        timestamp = datetime.fromisoformat(data.pop("timestamp"))
        return cls(timestamp=timestamp, **data)


def log_security_event(event: SecurityEvent) -> None:
    """
    Log a security event to the security log file
    """
    try:
        with open(SECURITY_LOG_FILE, "a") as f:
            f.write(f"{event.to_json()}\n")
        
        logger.info(f"Security event logged: {event.event_type} from {event.source_ip}")
        
        # Check if this event should trigger an alert
        check_alert_triggers(event)
    except Exception as e:
        logger.error(f"Error logging security event: {str(e)}")


def get_recent_events(event_type: Optional[str] = None, minutes: int = TIME_WINDOW_MINUTES) -> List[SecurityEvent]:
    """
    Get recent security events from the log file
    """
    events = []
    now = datetime.utcnow()
    
    try:
        if not os.path.exists(SECURITY_LOG_FILE):
            return []
        
        with open(SECURITY_LOG_FILE, "r") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    event = SecurityEvent.from_dict(data)
                    
                    # Check if the event is within the time window
                    event_time = event.timestamp
                    time_diff = (now - event_time).total_seconds() / 60
                    
                    if time_diff <= minutes:
                        if event_type is None or event.event_type == event_type:
                            events.append(event)
                except Exception as e:
                    logger.error(f"Error parsing security event: {str(e)}")
    except Exception as e:
        logger.error(f"Error reading security events: {str(e)}")
    
    return events


def check_alert_triggers(event: SecurityEvent) -> None:
    """
    Check if the event should trigger an alert
    """
    # Check for failed login attempts
    if event.event_type == "failed_login":
        check_failed_login_threshold(event)
    
    # Check for suspicious IP activity
    if event.event_type in ["failed_login", "successful_login"]:
        check_suspicious_ip_activity(event)
    
    # Check for credentials in URL
    if event.event_type == "credentials_in_url":
        # Always alert on credentials in URL
        send_security_alert(
            "Credentials detected in URL",
            f"Credentials were detected in a URL from IP {event.source_ip}",
            event
        )


def check_failed_login_threshold(event: SecurityEvent) -> None:
    """
    Check if the number of failed logins exceeds the threshold
    """
    # Get recent failed login events for this username or IP
    username_events = []
    ip_events = []
    
    if event.username:
        username_events = [
            e for e in get_recent_events("failed_login")
            if e.username == event.username
        ]
    
    ip_events = [
        e for e in get_recent_events("failed_login")
        if e.source_ip == event.source_ip
    ]
    
    # Check thresholds
    if len(username_events) >= LOGIN_FAILURE_THRESHOLD:
        send_security_alert(
            f"Multiple failed login attempts for user {event.username}",
            f"There have been {len(username_events)} failed login attempts for user {event.username} in the last {TIME_WINDOW_MINUTES} minutes.",
            event
        )
    
    if len(ip_events) >= LOGIN_FAILURE_THRESHOLD:
        send_security_alert(
            f"Multiple failed login attempts from IP {event.source_ip}",
            f"There have been {len(ip_events)} failed login attempts from IP {event.source_ip} in the last {TIME_WINDOW_MINUTES} minutes.",
            event
        )


def check_suspicious_ip_activity(event: SecurityEvent) -> None:
    """
    Check for suspicious IP activity (multiple usernames from same IP)
    """
    # Get all login events (failed and successful) from this IP
    login_events = [
        e for e in get_recent_events()
        if e.source_ip == event.source_ip and e.event_type in ["failed_login", "successful_login"]
    ]
    
    # Count unique usernames
    usernames = set(e.username for e in login_events if e.username)
    
    if len(usernames) >= SUSPICIOUS_IP_THRESHOLD:
        send_security_alert(
            f"Multiple users from same IP {event.source_ip}",
            f"There have been login attempts for {len(usernames)} different users from IP {event.source_ip} in the last {TIME_WINDOW_MINUTES} minutes.",
            event
        )


def send_security_alert(subject: str, message: str, event: SecurityEvent) -> None:
    """
    Send a security alert via email and log it
    """
    # Log the alert
    logger.warning(f"SECURITY ALERT: {subject} - {message}")
    
    # Send email alert if email is configured
    if SETTINGS.email_enabled:
        try:
            send_email_alert(subject, message, event)
        except Exception as e:
            logger.error(f"Error sending email alert: {str(e)}")


def send_email_alert(subject: str, message: str, event: SecurityEvent) -> None:
    """
    Send an email alert
    """
    # Create email
    email = MIMEMultipart()
    email["From"] = SETTINGS.email_sender
    email["To"] = SETTINGS.smtp_username  # Send to admin email
    email["Subject"] = f"SECURITY ALERT: {subject}"
    
    # Create email body
    body = f"""
    <html>
    <body>
        <h2>Security Alert</h2>
        <p><strong>{subject}</strong></p>
        <p>{message}</p>
        <h3>Event Details:</h3>
        <ul>
            <li><strong>Event Type:</strong> {event.event_type}</li>
            <li><strong>Severity:</strong> {event.severity}</li>
            <li><strong>Source IP:</strong> {event.source_ip}</li>
            <li><strong>Username:</strong> {event.username or 'N/A'}</li>
            <li><strong>User Agent:</strong> {event.user_agent or 'N/A'}</li>
            <li><strong>Timestamp:</strong> {event.timestamp.isoformat()}</li>
        </ul>
        <h3>Additional Details:</h3>
        <pre>{json.dumps(event.details, indent=2)}</pre>
    </body>
    </html>
    """
    
    email.attach(MIMEText(body, "html"))
    
    # Send email
    with smtplib.SMTP(SETTINGS.smtp_server, SETTINGS.smtp_port) as server:
        if SETTINGS.smtp_tls:
            server.starttls()
        
        if SETTINGS.smtp_username and SETTINGS.smtp_password:
            server.login(SETTINGS.smtp_username, SETTINGS.smtp_password)
        
        server.send_message(email)
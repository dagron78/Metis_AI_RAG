import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

from app.core.config import SETTINGS

logger = logging.getLogger(__name__)

async def send_email(
    recipient_email: str,
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    html_body: Optional[str] = None
) -> bool:
    """
    Send an email
    
    Args:
        recipient_email: Recipient email address
        subject: Email subject
        body: Email body (plain text)
        cc: CC recipients
        bcc: BCC recipients
        html_body: Email body (HTML)
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    # In development mode, just log the email
    if not SETTINGS.email_enabled:
        logger.info(f"Email would be sent to {recipient_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Body: {body}")
        return True
    
    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = SETTINGS.email_sender
    message["To"] = recipient_email
    
    # Add CC recipients
    if cc:
        message["Cc"] = ", ".join(cc)
    
    # Add BCC recipients
    if bcc:
        message["Bcc"] = ", ".join(bcc)
    
    # Add plain text body
    message.attach(MIMEText(body, "plain"))
    
    # Add HTML body if provided
    if html_body:
        message.attach(MIMEText(html_body, "html"))
    
    try:
        # Connect to SMTP server
        with smtplib.SMTP(SETTINGS.smtp_server, SETTINGS.smtp_port) as server:
            # Use TLS if enabled
            if SETTINGS.smtp_tls:
                server.starttls()
            
            # Login if credentials are provided
            if SETTINGS.smtp_username and SETTINGS.smtp_password:
                server.login(SETTINGS.smtp_username, SETTINGS.smtp_password)
            
            # Send email
            recipients = [recipient_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            server.sendmail(SETTINGS.email_sender, recipients, message.as_string())
            
            return True
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False
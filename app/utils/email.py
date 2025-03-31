import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import SETTINGS

logger = logging.getLogger(__name__)

async def send_password_reset_email(to_email: str, username: str, reset_url: str):
    """
    Send a password reset email
    
    Args:
        to_email: Recipient email
        username: Recipient username
        reset_url: Password reset URL
    """
    try:
        # Create message
        message = MIMEMultipart()
        message["From"] = SETTINGS.smtp_sender
        message["To"] = to_email
        message["Subject"] = "Metis RAG - Password Reset"
        
        # Create HTML content
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #007bff; color: white; padding: 10px 20px; text-align: center; }}
                .content {{ padding: 20px; border: 1px solid #ddd; border-top: none; }}
                .button {{ display: inline-block; background-color: #007bff; color: white; text-decoration: none; padding: 10px 20px; border-radius: 5px; margin-top: 20px; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #777; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset</h1>
                </div>
                <div class="content">
                    <p>Hello {username},</p>
                    <p>We received a request to reset your password for your Metis RAG account. If you didn't make this request, you can ignore this email.</p>
                    <p>To reset your password, click the button below:</p>
                    <p><a href="{reset_url}" class="button">Reset Password</a></p>
                    <p>Or copy and paste this URL into your browser:</p>
                    <p>{reset_url}</p>
                    <p>This link will expire in 24 hours.</p>
                    <p>Thank you,<br>The Metis RAG Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated message, please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML content
        message.attach(MIMEText(html, "html"))
        
        # Connect to SMTP server
        with smtplib.SMTP(SETTINGS.smtp_server, SETTINGS.smtp_port) as server:
            if SETTINGS.smtp_use_tls:
                server.starttls()
            
            if SETTINGS.smtp_username and SETTINGS.smtp_password:
                server.login(SETTINGS.smtp_username, SETTINGS.smtp_password)
            
            # Send email
            server.send_message(message)
        
        logger.info(f"Password reset email sent to {to_email}")
    except Exception as e:
        logger.error(f"Error sending password reset email: {str(e)}")
        # Don't raise the exception to prevent leaking information
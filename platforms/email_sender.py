"""
Email Sender Module
===================
Self-contained module for sending emails via SMTP with attachment support.
Supports Gmail and Outlook/Hotmail with automatic server detection.

Usage:
    from platforms.email_sender import send_email_smtp
    
    send_email_smtp(
        email_to="recipient@example.com",
        subject="Test Subject",
        body="Test message body",
        sender_email="sender@gmail.com",
        sender_password="app_password",
        log_fn=print,
        stop_event=threading.Event(),
        attachment_path="path/to/file.pdf"  # Optional
    )

Requirements:
    - smtplib (built-in)
    - email (built-in)
    - os (built-in)
    - time (built-in)
    - re (built-in)
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import time
import re


def send_email_smtp(email_to, subject, body, sender_email, sender_password, log_fn, stop_event, attachment_path=None):
    """
    Send an email via SMTP (Gmail/Outlook) with optional attachment.
    
    Args:
        email_to: str, recipient email address
        subject: str, email subject line
        body: str, email body (plain text or HTML)
        sender_email: str, sender email address
        sender_password: str, sender app password
        log_fn: callable, logging function
        stop_event: threading.Event, used to stop execution gracefully
        attachment_path: str, optional path to file to attach
    
    Returns:
        bool, True if sent successfully, False otherwise
    """
    if stop_event.is_set():
        log_fn("Stopped before sending email.")
        return False
    
    try:
        # Validate email format
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email_to):
            log_fn(f"❌ Invalid email format: {email_to}")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email_to
        msg['Subject'] = subject
        
        # Attach body
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach file if provided
        if attachment_path and os.path.exists(attachment_path):
            try:
                with open(attachment_path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(attachment_path)}",
                )
                msg.attach(part)
                log_fn(f"  📎 Attached: {os.path.basename(attachment_path)}")
            except Exception as e:
                log_fn(f"  ⚠️ Attachment failed: {e}")
        
        # Detect SMTP server based on email domain
        domain = sender_email.split('@')[1].lower()
        if 'gmail' in domain:
            smtp_server = 'smtp.gmail.com'
            smtp_port = 587
        elif 'outlook' in domain or 'hotmail' in domain:
            smtp_server = 'smtp-mail.outlook.com'
            smtp_port = 587
        else:
            smtp_server = 'smtp.gmail.com'
            smtp_port = 587
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email_to, msg.as_string())
        server.quit()
        
        log_fn(f"✅ Email sent to {email_to}")
        
        # Short delay between emails
        for remaining in range(2, 0, -1):
            if stop_event.is_set():
                break
            log_fn(f"  ⏳ Waiting {remaining} seconds...")
            time.sleep(1)
        
        return True
    
    except smtplib.SMTPAuthenticationError:
        log_fn(f"❌ Authentication failed. Check email/password (use App Password for Gmail).")
        return False
    except smtplib.SMTPException as e:
        log_fn(f"❌ SMTP error for {email_to}: {e}")
        return False
    except Exception as e:
        log_fn(f"❌ Failed to send email to {email_to}: {e}")
        return False

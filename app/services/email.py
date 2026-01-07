import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from ..config import settings

class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send an email"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            message["To"] = to_email
            message["Subject"] = subject
            
            # Add text version
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            # Add HTML version
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send email
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=settings.SMTP_TLS,
            )
            
            print(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False
    
    @staticmethod
    def get_welcome_email_html(name: str, email: str, username: str, password: str) -> str:
        """Generate welcome email HTML"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px 10px 0 0;
                    text-align: center;
                }}
                .content {{
                    background: #ffffff;
                    padding: 30px;
                    border: 1px solid #e5e7eb;
                    border-top: none;
                }}
                .credentials {{
                    background: #f9fafb;
                    border: 2px solid #3b82f6;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .credential-item {{
                    margin: 10px 0;
                }}
                .credential-label {{
                    font-size: 12px;
                    color: #6b7280;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                .credential-value {{
                    font-size: 16px;
                    font-weight: 600;
                    color: #1f2937;
                    font-family: 'Courier New', monospace;
                    background: #ffffff;
                    padding: 8px 12px;
                    border-radius: 4px;
                    margin-top: 4px;
                    border: 1px solid #e5e7eb;
                }}
                .password {{
                    color: #dc2626;
                }}
                .warning {{
                    background: #fef3c7;
                    border-left: 4px solid #f59e0b;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 600;
                    margin: 20px 0;
                }}
                .footer {{
                    background: #f9fafb;
                    padding: 20px;
                    border-radius: 0 0 10px 10px;
                    text-align: center;
                    font-size: 12px;
                    color: #6b7280;
                    border: 1px solid #e5e7eb;
                    border-top: none;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1 style="margin: 0;">Welcome to {settings.PROJECT_NAME}! 🎉</h1>
            </div>
            
            <div class="content">
                <p>Hi <strong>{name}</strong>,</p>
                
                <p>Welcome Ayatiworks Technologies LLP! Your employee account has been created successfully. We're excited to have you as part of our team.</p>
                
                <div class="credentials">
                    <h3 style="margin-top: 0; color: #1f2937;">Your Login Credentials</h3>
                    
                    <div class="credential-item">
                        <div class="credential-label">Email / Username</div>
                        <div class="credential-value">{username}</div>
                    </div>
                    
                    <div class="credential-item">
                        <div class="credential-label">Temporary Password</div>
                        <div class="credential-value password">{password}</div>
                    </div>
                </div>
                
                <div class="warning">
                    <strong>⚠️ Important Security Notice:</strong>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li>This is a temporary password that you should change immediately after your first login</li>
                        <li>Never share your password with anyone</li>
                        <li>Keep this email secure or delete it after changing your password</li>
                    </ul>
                </div>
                
                <p style="text-align: center;">
                    <a href="http://localhost:3000" class="button">Login to Your Account</a>
                </p>
                
                <p>If you have any questions or need assistance, please don't hesitate to contact the HR team.</p>
                
                <p>Best regards,<br>
                <strong>HR Team</strong><br>
                {settings.PROJECT_NAME}</p>
            </div>
            
            <div class="footer">
                <p>This is an automated email. Please do not reply to this message.</p>
                <p>&copy; 2024 {settings.PROJECT_NAME}. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def get_password_reset_email_html(name: str, username: str, password: str) -> str:
        """Generate password reset email HTML"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px 10px 0 0;
                    text-align: center;
                }}
                .content {{
                    background: #ffffff;
                    padding: 30px;
                    border: 1px solid #e5e7eb;
                    border-top: none;
                }}
                .credentials {{
                    background: #fef3c7;
                    border: 2px solid #f59e0b;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .credential-item {{
                    margin: 10px 0;
                }}
                .credential-label {{
                    font-size: 12px;
                    color: #6b7280;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                .credential-value {{
                    font-size: 16px;
                    font-weight: 600;
                    color: #1f2937;
                    font-family: 'Courier New', monospace;
                    background: #ffffff;
                    padding: 8px 12px;
                    border-radius: 4px;
                    margin-top: 4px;
                    border: 1px solid #e5e7eb;
                }}
                .password {{
                    color: #dc2626;
                }}
                .warning {{
                    background: #fee2e2;
                    border-left: 4px solid #dc2626;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 600;
                    margin: 20px 0;
                }}
                .footer {{
                    background: #f9fafb;
                    padding: 20px;
                    border-radius: 0 0 10px 10px;
                    text-align: center;
                    font-size: 12px;
                    color: #6b7280;
                    border: 1px solid #e5e7eb;
                    border-top: none;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1 style="margin: 0;">Password Reset 🔐</h1>
            </div>
            
            <div class="content">
                <p>Hi <strong>{name}</strong>,</p>
                
                <p>Your password has been reset by an administrator. Below are your new login credentials.</p>
                
                <div class="credentials">
                    <h3 style="margin-top: 0; color: #1f2937;">Your New Login Credentials</h3>
                    
                    <div class="credential-item">
                        <div class="credential-label">Username</div>
                        <div class="credential-value">{username}</div>
                    </div>
                    
                    <div class="credential-item">
                        <div class="credential-label">New Temporary Password</div>
                        <div class="credential-value password">{password}</div>
                    </div>
                </div>
                
                <div class="warning">
                    <strong>🔒 Security Reminder:</strong>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li>Please change this password immediately after logging in</li>
                        <li>If you did not request a password reset, please contact IT immediately</li>
                        <li>Never share your password with anyone</li>
                    </ul>
                </div>
                
                <p style="text-align: center;">
                    <a href="http://localhost:3000" class="button">Login to Your Account</a>
                </p>
                
                <p>If you have any concerns, please contact the IT support team immediately.</p>
                
                <p>Best regards,<br>
                <strong>IT Team</strong><br>
                {settings.PROJECT_NAME}</p>
            </div>
            
            <div class="footer">
                <p>This is an automated email. Please do not reply to this message.</p>
                <p>&copy; 2024 {settings.PROJECT_NAME}. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    async def send_welcome_email(name: str, email: str, username: str, password: str) -> bool:
        """Send welcome email to new employee"""
        html_content = EmailService.get_welcome_email_html(name, email, username, password)
        text_content = f"""
        Welcome to {settings.PROJECT_NAME}!
        
        Hi {name},
        
        Your employee account has been created successfully.
        
        Login Credentials:
        Username: {username}
        Temporary Password: {password}
        
        Please change your password after your first login.
        
        Best regards,
        HR Team
        """
        
        return await EmailService.send_email(
            to_email=email,
            subject=f"Welcome to {settings.PROJECT_NAME}! 🎉",
            html_content=html_content,
            text_content=text_content
        )
    
    @staticmethod
    async def send_password_reset_email(name: str, email: str, username: str, password: str) -> bool:
        """Send password reset email"""
        html_content = EmailService.get_password_reset_email_html(name, username, password)
        text_content = f"""
        Password Reset - {settings.PROJECT_NAME}
        
        Hi {name},
        
        Your password has been reset.
        
        New Login Credentials:
        Username: {username}
        Temporary Password: {password}
        
        Please change your password immediately after logging in.
        
        Best regards,
        IT Team
        """
        
        return await EmailService.send_email(
            to_email=email,
            subject="Password Reset - Action Required 🔐",
            html_content=html_content,
            text_content=text_content
        )

# Convenience function
email_service = EmailService()
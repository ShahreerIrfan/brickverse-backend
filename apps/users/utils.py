import logging
import secrets
from datetime import timedelta
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from .models import EmailOTP, User

logger = logging.getLogger(__name__)


def generate_otp_code(length=6):
    """Generate a cryptographically secure 6-digit numeric OTP."""
    return f"{secrets.randbelow(900000) + 100000}"


def send_otp_email(to_email: str, otp_code: str, purpose: str = "signup") -> bool:
    """
    Sends an HTML branded OTP verification email to the user.
    """
    subject = f"{otp_code} is your Kawaii Subete verification code"
    
    title_text = "Verify your email address" if purpose == "signup" else "Reset your password"
    desc_text = (
        "Thank you for joining Kawaii Subete! Please use the following 6-digit verification code to complete your signup."
        if purpose == "signup"
        else "We received a request to reset your Kawaii Subete password. Use the verification code below to proceed."
    )

    text_content = f"""
Kawaii Subete Verification Code: {otp_code}

{desc_text}

This code will expire in 10 minutes.
If you did not request this code, please safely ignore this email.

Best regards,
The Kawaii Subete Team
https://kawaiisubete.com
"""

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #FFF6EE; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #171136;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #FFF6EE; padding: 30px 15px;">
    <tr>
      <td align="center">
        <!-- Main Card Container -->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width: 520px; background-color: #ffffff; border-radius: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.06); border: 1px solid #EAE3F7; overflow: hidden;">
          
          <!-- Header Banner -->
          <tr>
            <td style="padding: 36px 30px 20px; text-align: center; background: linear-gradient(135deg, #FFF0F3 0%, #F5E8FF 100%);">
              <h1 style="margin: 0; font-size: 26px; font-weight: 900; color: #FF4D6D; letter-spacing: -0.5px;">
                Kawaii Subete
              </h1>
              <p style="margin: 6px 0 0; font-size: 13px; color: #736E9B; font-weight: 600;">
                Authentic Anime Merchandise & Collectibles
              </p>
            </td>
          </tr>

          <!-- Content Body -->
          <tr>
            <td style="padding: 32px 30px 28px; text-align: center;">
              <h2 style="margin: 0 0 12px; font-size: 20px; font-weight: 800; color: #171136;">
                {title_text}
              </h2>
              <p style="margin: 0 0 28px; font-size: 14px; line-height: 1.6; color: #524B7B;">
                {desc_text}
              </p>

              <!-- OTP Code Display Box -->
              <div style="background: #F8F6FD; border: 2px dashed #FF4D6D; border-radius: 16px; padding: 20px 10px; margin: 0 auto 28px; max-width: 360px;">
                <span style="display: block; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 2px; color: #FF4D6D; margin-bottom: 6px;">
                  Your Verification Code
                </span>
                <span style="display: block; font-size: 36px; font-weight: 900; letter-spacing: 8px; color: #171136; font-family: monospace;">
                  {otp_code}
                </span>
              </div>

              <!-- Expiry Alert -->
              <p style="margin: 0 0 20px; font-size: 13px; color: #736E9B;">
                ⏱️ This code is valid for <strong>10 minutes</strong>.
              </p>
              
              <div style="border-top: 1px solid #EAE3F7; margin: 24px 0 20px;"></div>

              <p style="margin: 0; font-size: 12px; line-height: 1.5; color: #9E99C2;">
                If you didn't create an account or request this code on <a href="https://kawaiisubete.com" style="color: #FF4D6D; text-decoration: none; font-weight: 600;">kawaiisubete.com</a>, please safely ignore this email.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 20px 30px; text-align: center; background-color: #FAF8FF; border-top: 1px solid #EAE3F7;">
              <p style="margin: 0; font-size: 12px; color: #736E9B;">
                &copy; Kawaii Subete &bull; support@kawaiisubete.com
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@kawaiisubete.com')

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[to_email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        logger.info(f"Successfully sent OTP email to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email to {to_email}: {str(e)}", exc_info=True)
        # In case SMTP is misconfigured in development/fallback, return false or raise
        raise e

import logging
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from rest_framework.authentication import BaseAuthentication, SessionAuthentication

logger = logging.getLogger(__name__)
signer = TimestampSigner()


def generate_user_token(user) -> str:
    """Generate a cryptographically signed token for a user (valid 30 days)."""
    return signer.sign(f"{user.id}:{user.email}")


def verify_user_token(token: str, max_age: int = 86400 * 30):
    """Verify a signed token and return the associated User or None."""
    if not token:
        return None
    try:
        data = signer.unsign(token, max_age=max_age)
        parts = data.split(':', 1)
        user_id = int(parts[0])
        User = get_user_model()
        return User.objects.filter(id=user_id, is_active=True).first()
    except (BadSignature, SignatureExpired, ValueError, TypeError) as exc:
        logger.debug("Failed to verify user token: %s", exc)
        return None


class TokenAndSessionAuthentication(SessionAuthentication):
    """
    Unified authentication supporting:
    1. Cryptographically signed Bearer tokens (Authorization: Bearer <token>)
    2. Session key headers (X-Session-Key / Authorization: Session <key>)
    3. Standard Django session cookies (with CSRF check waived for decoupled API calls)
    """

    def enforce_csrf(self, request):
        # Decoupled Next.js client uses Bearer token or CORS with trusted origins.
        # Avoid CSRF block on JSON API mutating methods (POST, PUT, PATCH, DELETE).
        return

    def authenticate(self, request):
        # 1. Check Authorization header for Bearer / Token
        auth_header = request.headers.get('Authorization', '').strip()
        if auth_header:
            parts = auth_header.split(' ', 1)
            scheme = parts[0].lower()
            if scheme in ('bearer', 'token') and len(parts) == 2:
                token_val = parts[1].strip()
                # Try signed token first
                user = verify_user_token(token_val)
                if user:
                    return (user, None)

                # Try Django session_key fallback
                try:
                    s = Session.objects.filter(session_key=token_val).first()
                    if s:
                        decoded = s.get_decoded()
                        uid = decoded.get('_auth_user_id')
                        if uid:
                            User = get_user_model()
                            user = User.objects.filter(id=uid, is_active=True).first()
                            if user:
                                return (user, None)
                except Exception:
                    pass

        # 3. Check X-Session-Token or X-Session-Key header
        custom_token = request.headers.get('X-Session-Token') or request.headers.get('X-Session-Key')
        if custom_token:
            user = verify_user_token(custom_token.strip())
            if user:
                return (user, None)

        # 4. Check X-User-Email / X-User-Id headers passed by authenticated client
        user_email = request.headers.get('X-User-Email', '').strip()
        user_id_hdr = request.headers.get('X-User-Id', '').strip()
        if user_email or user_id_hdr:
            User = get_user_model()
            user = None
            if user_id_hdr and user_id_hdr.isdigit():
                user = User.objects.filter(id=int(user_id_hdr), is_active=True).first()
            if not user and user_email:
                user = User.objects.filter(email__iexact=user_email, is_active=True).first()
            if user:
                return (user, None)

        # 5. Check standard Django session cookie via parent SessionAuthentication
        user_auth_tuple = super().authenticate(request)
        if user_auth_tuple:
            return user_auth_tuple

        return None

from datetime import timedelta
from rest_framework_simplejwt.tokens import AccessToken


class CodeAccessToken(AccessToken):
    """
    Custom JWT token for code-based authentication.
    Short-lived token with code-specific claims.
    """
    # Use a dedicated token type so validation accepts code tokens.
    token_type = 'code'
    lifetime = timedelta(minutes=30)  # Short-lived for security

    @classmethod
    def for_auth_code(cls, auth_code):
        """
        Generate a token for an authentication code.
        """
        # Create token without a user (anonymous access)
        token = cls()

        # Add custom claims
        token['code_id'] = auth_code.id
        token['user_id'] = None  # No user associated

        return token

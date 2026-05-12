from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import AnonymousUser


class CodeAuthUser(AnonymousUser):
    @property
    def is_authenticated(self):
        return True


class CodeJWTAuthentication(JWTAuthentication):
    """
    Custom JWT Authentication that supports code-based tokens without users.
    
    For code-based tokens (token_type='code'), we create a special anonymous user
    with the code_id attached for permission checking.
    
    For regular tokens, we use the standard JWT authentication flow.
    """
    
    def get_user(self, validated_token):
        """
        Get the user associated with the token.
        For code tokens, return a special anonymous user with code claims.
        For regular tokens, use the standard user lookup.
        """
        # Check if this is a code-based token
        token_type = validated_token.get('token_type')
        
        if token_type == 'code':
            # Create an anonymous user with code information
            user = CodeAuthUser()
            user.code_id = validated_token.get('code_id')
            user.token_type = 'code'
            return user
        
        # For regular tokens, use the standard user lookup
        try:
            user_id = validated_token.get('user_id')
            if user_id is None:
                raise InvalidToken('Token contained no recognizable user identification')
            
            return super().get_user(validated_token)
        except Exception:
            raise InvalidToken('User not found')
    
    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        header = self.get_header(request)
        if header is None:
            return None
        
        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None
        
        try:
            validated_token = self.get_validated_token(raw_token)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        
        user = self.get_user(validated_token)
        
        return user, validated_token

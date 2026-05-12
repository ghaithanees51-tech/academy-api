from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer for email-based authentication.
    """
    username_field = User.USERNAME_FIELD

    def validate(self, attrs):
        # Call parent to get token
        data = super().validate(attrs)

        # Add custom claims
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
            'is_super_admin': self.user.is_super_admin,
        }

        return data


class AdminLoginSerializer(EmailTokenObtainPairSerializer):
    """
    Admin login: same as email JWT but restricts to staff users and adds message.
    """

    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_staff:
            from rest_framework import serializers as ser
            raise ser.ValidationError(
                {'detail': 'Only staff accounts can access the admin panel.'}
            )
        data['message'] = 'Login successful'
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims to token
        token['email'] = user.email
        token['role'] = user.role
        token['is_super_admin'] = user.is_super_admin
        token['token_type'] = 'admin'

        return token

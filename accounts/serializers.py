from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.

    Exposes a single ``name`` field for the admin frontend (which displays one
    "Full Name" input) while persisting it as ``first_name`` / ``last_name``
    under the hood. ``phone_number`` is read/write.
    """

    name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'name',
            'phone_number',
            'role',
            'is_active',
            'date_joined',
        ]
        read_only_fields = ['id', 'email', 'role', 'is_active', 'date_joined']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        full = f'{instance.first_name} {instance.last_name}'.strip()
        data['name'] = full or instance.email
        return data

    def update(self, instance, validated_data):
        name = validated_data.pop('name', None)
        if name is not None:
            stripped = name.strip()
            if stripped:
                parts = stripped.split(' ', 1)
                instance.first_name = parts[0][:150]
                instance.last_name = (parts[1] if len(parts) > 1 else '')[:150]
            else:
                instance.first_name = ''
                instance.last_name = ''
        return super().update(instance, validated_data)


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


class ChangePasswordSerializer(serializers.Serializer):
    """
    Validates the current password and runs Django's configured password
    validators against the new one. The view is responsible for actually
    setting and saving the password on the user.
    """

    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value

    def validate_new_password(self, value):
        user = self.context['request'].user
        try:
            validate_password(value, user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def validate(self, attrs):
        if attrs.get('current_password') == attrs.get('new_password'):
            raise serializers.ValidationError(
                {'new_password': 'New password must be different from the current password.'}
            )
        return attrs


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

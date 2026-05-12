from rest_framework import serializers

from .models import AuthCode


class AuthCodeCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating authentication codes (admin use).
    """

    class Meta:
        model = AuthCode
        fields = []  # No fields needed - code is auto-generated


class AuthCodeSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying authentication codes.
    """
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = AuthCode
        fields = [
            'id',
            'code',
            'used_count',
            'status',
            'created_by_email',
            'created_at',
            'updated_at',
            'last_used_at',
            'is_valid',
        ]
        read_only_fields = [
            'id',
            'code',
            'used_count',
            'status',
            'created_at',
            'updated_at',
            'last_used_at',
        ]

    def get_is_valid(self, obj):
        return obj.is_valid()


class CodeLoginSerializer(serializers.Serializer):
    """
    Serializer for public code-based login.
    """
    code = serializers.CharField(
        max_length=8,
        required=True,
        help_text='8-digit authentication code',
    )

    def validate_code(self, value):
        """
        Validate the code format.
        """
        if not value:
            raise serializers.ValidationError('Code is required.')
        return value.strip()

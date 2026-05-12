import secrets
from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_auth_code():
    """
    Generate a cryptographically secure random 8-digit authentication code.
    Format: XXXXXXXX (8 digits)
    """
    # Generate a random 8-digit number
    return str(secrets.randbelow(90000000) + 10000000)


class AuthCode(models.Model):
    """
    Authentication code model for simple code-based access.
    Active codes can be used unlimited times until revoked.
    """

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('revoked', 'Revoked'),
    ]

    code = models.CharField(
        max_length=8,
        unique=True,
        db_index=True,
        default=generate_auth_code,
        help_text='Unique 8-digit authentication code',
    )
    used_count = models.PositiveIntegerField(
        default=0,
        help_text='Number of times this code has been used',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_auth_codes',
        help_text='Super admin who created this code',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last time this code was successfully used',
    )

    class Meta:
        verbose_name = 'Authentication Code'
        verbose_name_plural = 'Authentication Codes'
        db_table = 'auth_codes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code', 'status']),
        ]

    def __str__(self):
        return f'{self.code}'

    def is_valid(self):
        """
        Check if the code is valid for use.
        Active codes can be used unlimited times.
        """
        return self.status == 'active'

    def revoke(self):
        """
        Revoke this authentication code.
        """
        self.status = 'revoked'
        self.save(update_fields=['status', 'updated_at'])

    @property
    def unique_users_count(self):
        """
        Get the count of unique IP addresses that have used this code.
        """
        return self.usages.values('ip_address').distinct().count()

    def get_unique_ips(self):
        """
        Get list of unique IP addresses that have used this code.
        """
        return self.usages.values_list('ip_address', flat=True).distinct()


class AuthCodeUsage(models.Model):
    """
    Track each use of an authentication code with IP address.
    """
    auth_code = models.ForeignKey(
        AuthCode,
        on_delete=models.CASCADE,
        related_name='usages',
        help_text='The authentication code that was used',
    )
    ip_address = models.GenericIPAddressField(
        help_text='IP address of the user',
    )
    user_agent = models.TextField(
        blank=True,
        null=True,
        help_text='User agent string from the browser',
    )
    used_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When this code was used',
    )

    class Meta:
        verbose_name = 'Authentication Code Usage'
        verbose_name_plural = 'Authentication Code Usages'
        db_table = 'auth_code_usages'
        ordering = ['-used_at']
        indexes = [
            models.Index(fields=['auth_code', 'ip_address']),
            models.Index(fields=['auth_code', 'used_at']),
            models.Index(fields=['ip_address']),
        ]

    def __str__(self):
        return f'{self.auth_code.code} - {self.ip_address} at {self.used_at}'

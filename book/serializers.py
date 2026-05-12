from rest_framework import serializers

from category.models import Category

from .models import Book


class BookSerializer(serializers.ModelSerializer):
    cover_url = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    audio_file_url = serializers.SerializerMethodField()
    video_file_url = serializers.SerializerMethodField()
    has_text_extraction = serializers.SerializerMethodField()
    category = serializers.SlugRelatedField(slug_field='slug', queryset=Category.objects.all())

    class Meta:
        model = Book
        fields = (
            'id',
            'type',
            'category',
            'title',
            'author',
            'publisher',
            'edition',
            'year',
            'isbn',
            'language',
            'pages',
            'audio',
            'video',
            'audio_file',
            'video_file',
            'cover',
            'file',
            'date',
            'status',
            'created_at',
            'cover_url',
            'file_url',
            'audio_file_url',
            'video_file_url',
            'has_text_extraction',
        )

    def get_has_text_extraction(self, obj):
        return getattr(obj, 'text_extraction', None) is not None

    def get_cover_url(self, obj):
        request = self.context.get('request')
        if obj.cover and request:
            return request.build_absolute_uri(obj.cover.url)
        return None

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

    def get_audio_file_url(self, obj):
        request = self.context.get('request')
        if obj.audio_file and request:
            return request.build_absolute_uri(obj.audio_file.url)
        return None

    def get_video_file_url(self, obj):
        request = self.context.get('request')
        if obj.video_file and request:
            return request.build_absolute_uri(obj.video_file.url)
        return None


class PublicPublicationSerializer(serializers.ModelSerializer):
    subtitle = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    has_text_extraction = serializers.SerializerMethodField()
    extraction_summary = serializers.SerializerMethodField()
    category = serializers.SlugRelatedField(slug_field='slug', queryset=Category.objects.all())
    category_name = serializers.CharField(source='category.category_name', read_only=True)

    class Meta:
        model = Book
        fields = (
            'id',
            'type',
            'category',
            'category_name',
            'title',
            'subtitle',
            'cover',
            'date',
            'url',
            'pages',
            'author',
            'publisher',
            'edition',
            'year',
            'isbn',
            'language',
            'audio',
            'video',
            'has_text_extraction',
            'extraction_summary',
        )

    def get_cover(self, obj):
        request = self.context.get('request')
        if obj.cover and request:
            return request.build_absolute_uri(obj.cover.url)
        if obj.cover:
            return obj.cover.url
        return ""

    def get_subtitle(self, obj):
        return ""

    def get_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        if obj.file:
            return obj.file.url
        if obj.audio and obj.audio.strip():
            return obj.audio.strip()
        if obj.video and obj.video.strip():
            return obj.video.strip()
        return ""

    def get_has_text_extraction(self, obj):
        # _has_text_extraction is an Exists() annotation added by the public queryset
        return bool(getattr(obj, '_has_text_extraction', False))

    def get_extraction_summary(self, obj):
        # _extraction_summary is a Subquery() annotation added by the public queryset
        return getattr(obj, '_extraction_summary', None) or None
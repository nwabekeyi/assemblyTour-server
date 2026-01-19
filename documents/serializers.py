from rest_framework import serializers
from .models import Document, DocumentType
from django.contrib.auth import get_user_model

User = get_user_model()

class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = ['id', 'name', 'description', 'is_active', 'upload_by']


class DocumentSerializer(serializers.ModelSerializer):
    doc_type = serializers.PrimaryKeyRelatedField(queryset=DocumentType.objects.filter(is_active=True))

    class Meta:
        model = Document
        fields = ['id', 'user', 'doc_type', 'file_url', 'description', 'expiry_date', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at', 'user']

    def validate_doc_type(self, value):
        user = self.context['request'].user
        if value.upload_by == 'admin' and not user.is_staff:
            raise serializers.ValidationError("Only admin can upload this document type.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        if user.is_staff and 'user' in self.initial_data:
            user_id = self.initial_data['user']
            try:
                validated_data['user'] = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise serializers.ValidationError("Specified user does not exist.")
        else:
            validated_data['user'] = user
        return super().create(validated_data)

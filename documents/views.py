from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Document, DocumentType
from .serializers import DocumentSerializer, DocumentTypeSerializer
from core.cloudinary_settings import cloudinary, CLOUDINARY_ALLOWED_FILE_TYPES, CLOUDINARY_MAX_FILE_SIZE

class DocumentTypeListView(generics.ListAPIView):
    queryset = DocumentType.objects.filter(is_active=True)
    serializer_class = DocumentTypeSerializer
    permission_classes = [permissions.IsAuthenticated]


class DocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate file type
        if file.content_type not in CLOUDINARY_ALLOWED_FILE_TYPES:
            return Response({"error": "Invalid file type."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate file size
        if file.size > CLOUDINARY_MAX_FILE_SIZE:
            return Response({"error": "File too large."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate doc type
        doc_type_id = request.data.get('doc_type')
        try:
            doc_type = DocumentType.objects.get(id=doc_type_id)
        except DocumentType.DoesNotExist:
            return Response({"error": "Invalid document type."}, status=status.HTTP_400_BAD_REQUEST)

        # Determine folder
        folder_name = doc_type.name.replace(" ", "_").lower()

        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            file,
            folder=f"assembly-tour/{folder_name}/",
            resource_type='auto',
            allowed_formats=CLOUDINARY_ALLOWED_FILE_TYPES,
            use_filename=True,
            unique_filename=True
        )

        file_url = upload_result.get('secure_url')
        if not file_url:
            return Response({"error": "Upload failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = self.get_serializer(data={
            'doc_type': doc_type_id,
            'file_url': file_url,
            'description': request.data.get('description', ''),
            'expiry_date': request.data.get('expiry_date', None),
            'user': request.data.get('user', None)
        })
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)

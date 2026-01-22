from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Document, DocumentType
from .serializers import DocumentSerializer, DocumentTypeSerializer
from core.services.cloudinary_service import CloudinaryService

# Initialize Cloudinary service
cloudinary_service = CloudinaryService()


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
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate file type using CloudinaryService global list
        ext = file.name.split(".")[-1].lower()
        if ext not in CloudinaryService.ALLOWED_FILE_TYPES:
            return Response(
                {"error": f"Invalid file type. Allowed: {CloudinaryService.ALLOWED_FILE_TYPES}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Optional: Validate file size (if needed)
        if file.size > 10 * 1024 * 1024:  # 10 MB limit
            return Response({"error": "File too large."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate document type
        doc_type_id = request.data.get("doc_type")
        try:
            doc_type = DocumentType.objects.get(id=doc_type_id)
        except DocumentType.DoesNotExist:
            return Response({"error": "Invalid document type."}, status=status.HTTP_400_BAD_REQUEST)

        # Determine Cloudinary folder
        folder_name = doc_type.name.replace(" ", "_").lower()

        # Upload file using CloudinaryService
        try:
            upload_result = cloudinary_service.upload(file, subfolder=folder_name)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        file_url = upload_result.get("secure_url")
        if not file_url:
            return Response({"error": "Upload failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Save the document
        serializer = self.get_serializer(
            data={
                "doc_type": doc_type_id,
                "file_url": file_url,
                "description": request.data.get("description", ""),
                "expiry_date": request.data.get("expiry_date"),
                "user": request.user.id,
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)

from django.contrib.auth.models import User
from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import logging
from .models import Image
from .serializers import RegisterSerializer, ImageSerializer, UserSerializer
from .tasks import process_image
logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer


class UserInfoView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Successfully logged out."}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class ImageUploadView(generics.CreateAPIView):
    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        print("Hello")
        logger.debug(
            f"Storage backend 111: {Image._meta.get_field('image').storage.__class__.__name__}"
        )
        image = serializer.save(user=self.request.user)
        task = process_image.delay(image.id)

        print(f"Task ID: {task.id}")

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ImageStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            image = Image.objects.get(pk=pk, user=request.user)
            serializer = ImageSerializer(image)
            return Response(serializer.data)
        except Image.DoesNotExist:
            return Response({"error": "Image not found"}, status=404)


class UserImageListView(generics.ListAPIView):
    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Image.objects.filter(user=self.request.user)


class ImageDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Ensure the image belongs to the authenticated user
        try:
            image = Image.objects.get(pk=self.kwargs["pk"], user=self.request.user)
            return image
        except Image.DoesNotExist:
            return None

    def delete(self, request, *args, **kwargs):
        image = self.get_object()
        if image is None:
            return Response(
                {
                    "error": "Image not found or you do not have permission to delete it."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Remove the image from S3
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            config=Config(signature_version="s3v4"),
        )
        try:
            s3_client.delete_object(Bucket="aizen-imgs", Key=str(image.image))
        except ClientError as e:
            return Response(
                {"error": "Failed to delete the image from S3.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Delete the image record from the database
        image.delete()

        return Response(
            {"message": "Image deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )

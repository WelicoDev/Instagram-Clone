from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.generics import (
    ListAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView,
    ListCreateAPIView, RetrieveAPIView
)
from shared.custom_pagination import CustomPagination
from .models import Post, PostLike, PostComment, CommentLike
from .serializers import PostSerializer, PostLikeSerializer, CommentSerializer, CommentLikeSerializers


class PostListApiView(ListAPIView):
    queryset = Post.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = PostSerializer
    pagination_class = CustomPagination


class PostCreateApiView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PostSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostEditApiView(RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = PostSerializer

    def put(self, request, *args, **kwargs):
        post = self.get_object()
        serializer = self.serializer_class(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "message": "Post successfully updated", "data": serializer.data})

    def delete(self, request, *args, **kwargs):
        post = self.get_object()
        post.delete()
        return Response({"success": True, "message": "Post successfully deleted"})


class PostCommentListApiView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        post_id = self.kwargs.get("pk")
        return PostComment.objects.filter(post_id=post_id).order_by('-created_at')


class PostCommentCreateApiView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer
    queryset = PostComment.objects.all()  # ✅ Swagger xatosini oldini olish

    def perform_create(self, serializer):
        post_id = self.kwargs.get('pk')
        serializer.save(author=self.request.user, post_id=post_id)


class CommentListCreateApiView(ListCreateAPIView):
    queryset = PostComment.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class CommentDetailApiView(RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = PostComment.objects.all()
    serializer_class = CommentSerializer


class PostLikeListApiView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = PostLikeSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        post_id = self.kwargs.get('pk')
        return PostLike.objects.filter(post_id=post_id).order_by('-created_at')


class CommentLikeListView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CommentLikeSerializers
    pagination_class = CustomPagination

    def get_queryset(self):
        comment_id = self.kwargs.get('pk')
        return CommentLike.objects.filter(comment_id=comment_id).order_by('-created_at')


class PostLikeApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        post = Post.objects.filter(id=pk).first()
        if not post:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        post_like, created = PostLike.objects.get_or_create(
            author=request.user, post_id=pk
        )
        if not created:
            post_like.delete()
            return Response({"success": True, "message": "Post like successfully removed."},
                            status=status.HTTP_204_NO_CONTENT)

        serializer = PostLikeSerializer(post_like)
        return Response({"success": True, "message": "Post like successfully added.", "data": serializer.data},
                        status=status.HTTP_201_CREATED)


class CommentLikeApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        comment = PostComment.objects.filter(id=pk).first()
        if not comment:
            return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)

        comment_like, created = CommentLike.objects.get_or_create(
            author=request.user, comment_id=pk
        )
        if not created:
            comment_like.delete()
            return Response({"success": True, "message": "Comment like successfully removed."},
                            status=status.HTTP_204_NO_CONTENT)

        serializer = CommentLikeSerializers(comment_like)
        return Response({"success": True, "message": "Comment like successfully added.", "data": serializer.data},
                        status=status.HTTP_201_CREATED)

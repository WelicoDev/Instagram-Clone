from django.urls import path
from .views import PostListApiView, PostCreateApiView, PostEditApiView, PostCommentListApiView,\
                    PostCommentCreateApiView, CommentListCreateApiView, PostLikeListApiView, CommentDetailApiView, \
                    CommentLikeListView,  CommentLikeApiView, PostLikeApiView

urlpatterns = [
    path('posts/', PostListApiView.as_view(), name="posts_list"),
    path('post/create/', PostCreateApiView.as_view(), name="post_create"),
    path('posts/<uuid:pk>/edit/', PostEditApiView.as_view(), name="post_edit"),
    path('posts/<uuid:pk>/comments/', PostCommentListApiView.as_view(), name="post_comments"),
    path('posts/<uuid:pk>/comments/create/', PostCommentCreateApiView.as_view(), name="post_comments_create"),
    path('post/comments/', CommentListCreateApiView.as_view(), name="comments_create"),
    path('post/comments/<uuid:pk>/', CommentDetailApiView.as_view(), name="post_comment_detail"),
    path('post/<uuid:pk>/likes/', PostLikeListApiView.as_view(), name="post_likes_list"),
    path('post/comments/<uuid:pk>/likes/', CommentLikeListView.as_view(), name="post_comment_likes"),
    path('post/<uuid:pk>/like/', PostLikeApiView.as_view(), name="post_like"),
    path('post/comments/<uuid:pk>/like/', CommentLikeApiView.as_view(), name="comment_like"),
]
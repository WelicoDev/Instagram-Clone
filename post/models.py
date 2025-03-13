from django.core.validators import FileExtensionValidator, MaxLengthValidator
from django.db import models
from django.db.models import UniqueConstraint
from users.models import User
from shared.models import BaseModel

# Post model
class Post(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    image = models.ImageField(upload_to='post-images/', validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp", "svg", "ico"])])
    caption = models.TextField(validators=[MaxLengthValidator(3000)])

    class Meta:
        db_table = "posts"
        verbose_name = "post"
        verbose_name_plural = "posts"

    def __str__(self):
        return self.caption[:128]


# PostComment model
class PostComment(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    comment = models.TextField(validators=[MaxLengthValidator(5000)])
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='child', null=True, blank=True)

    class Meta:
        db_table = "post_comments"
        verbose_name = "post comment"
        verbose_name_plural = "post comments"

    def __str__(self):
        return self.comment[:128]


# PostLike model
class PostLike(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['author', 'post'], name='unique_post_like'
            )
        ]
        db_table = "post_likes"
        verbose_name = "post like"
        verbose_name_plural = "post likes"

    def __str__(self):
        return f'{self.author.username} likes {self.post.caption[:32]}'


# CommentLike model
class CommentLike(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, related_name="likes")

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['author', 'comment'], name='unique_comment_like'
            )
        ]
        db_table = "comment_likes"
        verbose_name = "comment like"
        verbose_name_plural = "comment likes"

    def __str__(self):
        return f'{self.author.username} likes comment {self.comment.id}'

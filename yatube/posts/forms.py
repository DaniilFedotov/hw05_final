from django.forms import ModelForm, Textarea
from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        widgets = {
            'text': Textarea(attrs={'cols': 80, 'rows': 20}),
        }
        labels = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу, к которой будет относиться пост',
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': Textarea(attrs={'cols': 40, 'rows': 10}),
        }

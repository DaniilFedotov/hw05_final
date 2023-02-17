import shutil
import tempfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import Post, Group, Comment


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
            description='test-description',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user)

    def test_post_create(self):
        """Валидная форма создает пост."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'test-text',
            'group': self.group.pk,
            'image': uploaded
        }
        self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='test-text',
                group=self.group.pk,
                image='posts/small.gif'
            ).exists()
        )

    def test_post_edit(self):
        """Валидная форма редактирует пост."""
        post = Post.objects.create(
            text='test-text',
            author=self.user,
            group=self.group,
        )
        posts_count = Post.objects.count()
        another_group = Group.objects.create(
            title='test-another_group',
            slug='test-another_slug',
            description='test-another_description',
        )
        form_data = {
            'text': 'test-text-change',
            'group': another_group.pk,
        }
        self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': f'{post.id}'}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='test-text-change',
                group=another_group.pk,
                author=self.user,
            ).exists()
        )

    def test_post_edit_not_author(self):
        """Валидная форма не от автора не редактирует пост."""
        post = Post.objects.create(
            text='test-text',
            author=self.user,
            group=self.group,
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'test-text-change',
            'group': self.group.pk,
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': f'{post.id}'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'users:login'
            ) + f'?next=/posts/{post.id}/edit/'
        )
        self.assertEqual(Post.objects.count(), posts_count)


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            text='test-text',
            author=cls.user,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_comment_for_authorized_client(self):
        """Валидная форма авторизированного
        пользователя добавляет комментарий.
        """
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'test-comment-text',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': f'{self.post.id}'}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)

    def test_comment_for_guest_client(self):
        """Валидная форма неавторизированного
        пользователя не добавляет комментарий.
        """
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'test-comment-text',
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': f'{self.post.id}'}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertRedirects(
            response, reverse(
                'users:login'
            ) + f'?next=/posts/{self.post.id}/comment/'
        )

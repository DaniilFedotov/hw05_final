from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache
from ..models import Post, Group


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
            description='test-description',
        )
        cls.post = Post.objects.create(
            text='test-text',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.post.author)
        cache.clear()

    def test_pages_access(self):
        """Все страницы доступны согласно правам доступа пользователей."""
        url_user_status = {
            '': (self.guest_client, HTTPStatus.OK),
            f'/group/{self.post.group.slug}/':
                (self.guest_client, HTTPStatus.OK),
            f'/profile/{self.user}/': (self.guest_client, HTTPStatus.OK),
            f'/posts/{self.post.id}/': (self.guest_client, HTTPStatus.OK),
            f'/posts/{self.post.id}/edit/':
                (self.author_client, HTTPStatus.OK),
            '/create/': (self.authorized_client, HTTPStatus.OK),
            '/unexisting_page/': (self.guest_client, HTTPStatus.NOT_FOUND),
        }
        for url, user_status in url_user_status.items():
            with self.subTest(url=url):
                response = user_status[0].get(url)
                self.assertEqual(response.status_code, user_status[1])

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates_names = {
            '/': 'posts/index.html',
            f'/group/{self.post.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.post.author}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/unexisting_page/': 'core/404.html'
        }
        for url, template in url_templates_names.items():
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)

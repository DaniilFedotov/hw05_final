import shutil
import tempfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from ..models import Post, Group, Follow
from ..utilities import POSTS_ON_PAGES


User = get_user_model()
NUM_OF_TESTS_POSTS = 13
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
            description='test-description',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='test-text',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.post.author)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse(
                'posts:index'
            ): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{self.post.group.slug}'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': f'{self.post.author}'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.id}'}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_create'
            ): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.post.id}'}
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('posts:index'))
        last_add_object = response.context['posts'][0]
        self.assertEqual(last_add_object, self.post)
        self.assertContains(response, '<img')

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{self.post.group.slug}'}
            )
        )
        posts = response.context['posts']
        for post in posts:
            self.assertEqual(post.group.slug, self.post.group.slug)
        self.assertContains(response, '<img')

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': f'{self.post.author}'}
            )
        )
        posts = response.context['posts']
        for post in posts:
            self.assertEqual(post.author, self.post.author)
        self.assertContains(response, '<img')

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.id}'}
            )
        )
        post = response.context['post']
        self.assertEqual(post.id, self.post.id)
        self.assertContains(response, '<img')

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse('posts:post_create')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.post.id}'}
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
            description='test-description',
        )
        for i in range(NUM_OF_TESTS_POSTS):
            Post.objects.create(
                text=f'test-text{i}',
                author=cls.user,
                group=cls.group,
            )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.user)
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """На первой странице присутствует необходимое количество постов."""
        pages = {
            'posts:index': None,
            'posts:group_list': ('slug', f'{self.group.slug}'),
            'posts:profile': ('username', f'{self.user.username}'),
        }
        for page, attrs in pages.items():
            if attrs is None:
                response = self.author_client.get(reverse(page))
                self.assertEqual(
                    len(response.context['page_obj']),
                    POSTS_ON_PAGES
                )
                break
            response = self.author_client.get(
                reverse(page, kwargs={attrs[0]: attrs[1]})
            )
            self.assertEqual(len(response.context['page_obj']), POSTS_ON_PAGES)

    def test_second_page_contains_rest_records(self):
        """На второй странице присутствует оставшееся количество постов."""
        pages = {
            'posts:index': None,
            'posts:group_list': ('slug', f'{self.group.slug}'),
            'posts:profile': ('username', f'{self.user.username}'),
        }
        for page, attrs in pages.items():
            if attrs is None:
                response = self.author_client.get(
                    reverse(page) + '?page=2'
                )
                self.assertEqual(
                    len(response.context['page_obj']),
                    NUM_OF_TESTS_POSTS - POSTS_ON_PAGES
                )
                break
            response = self.author_client.get(
                reverse(
                    page,
                    kwargs={attrs[0]: attrs[1]}
                ) + '?page=2'
            )
            self.assertEqual(
                len(response.context['page_obj']),
                NUM_OF_TESTS_POSTS - POSTS_ON_PAGES
            )


class CreationPostTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
            description='test-description',
        )
        cls.another_group = Group.objects.create(
            title='test-another_group',
            slug='test-another_slug',
            description='test-another_description',
        )
        cls.post = Post.objects.create(
            text='test-text',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.post.author)
        cache.clear()

    def test_new_post_with_group_added_where_needed(self):
        """При создании поста с группой
        он появляется на соответствующих страницах.
        """
        where_needed = {
            'posts:index': None,
            'posts:group_list': ('slug', f'{self.post.group.slug}'),
            'posts:profile': ('username', f'{self.post.author.username}'),
        }
        for page, attrs in where_needed.items():
            if attrs is None:
                response = self.author_client.get(reverse(page))
                self.assertIn(self.post, response.context['posts'])
                break
            response = self.author_client.get(
                reverse(page, kwargs={attrs[0]: attrs[1]})
            )
            self.assertIn(self.post, response.context['posts'])

    def test_new_post_with_group_not_added_in_other_groups(self):
        """При создании поста с группой
        он не появляется на странице другой группы.
        """
        response = self.author_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{self.another_group.slug}'}
            )
        )
        self.assertNotIn(self.post, response.context['posts'])


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

    def setUp(self):
        self.author_client = Client()

    def test_cache(self):
        """Список записей на главной странице кешируется,
        и обновляется раз в 20 секунд
        """
        response_first = self.author_client.get(
            reverse('posts:index')
        )
        Post.objects.create(
            text='test-text',
            author=self.user,
        )
        response_second = self.author_client.get(
            reverse('posts:index')
        )
        self.assertEqual(response_first.content, response_second.content)
        cache.clear()
        response_third = self.author_client.get(
            reverse('posts:index')
        )
        self.assertNotEqual(response_first.content, response_third.content)

    def test_cache_delete(self):
        """При удалении записи из базы, она остается
         на главной странице пока кеш не очищен
        """
        post = Post.objects.create(
            text='test-text',
            author=self.user,
        )
        response_first = self.author_client.get(
            reverse('posts:index')
        )
        post.delete()
        response_second = self.author_client.get(
            reverse('posts:index')
        )
        self.assertEqual(response_first.content, response_second.content)
        cache.clear()
        response_third = self.author_client.get(
            reverse('posts:index')
        )
        self.assertNotEqual(response_first.content, response_third.content)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_author')
        cls.user = User.objects.create_user(username='auth_follower')
        cls.user_unfollower = User.objects.create_user(username='auth_unfollower')
        cls.post = Post.objects.create(
            text='test-text',
            author=cls.author
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_unfollower = Client()
        self.authorized_client_unfollower.force_login(self.user_unfollower)

    def test_profile_follow(self):
        """Авторизованный пользователь может подписываться на
        других пользователей и удалять их из подписок.
        """
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author.username}
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.author,
            ).exists()
        )
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author.username}
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.author,
            ).exists()
        )

    def test_follow_index(self):
        """Новая запись пользователя появляется в ленте его подписчиков,
         и не появляется в ленте других пользователей.

        """
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author.username}
            )
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertIn(self.post, response.context['posts'])
        response = self.authorized_client_unfollower.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(self.post, response.context['posts'])



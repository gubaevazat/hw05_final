from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='one')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )
        cls.urls_templates = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{cls.post.pk}/edit/': 'posts/create_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTest.user)

    def test_public_pages_available_to_guest_user(self):
        """Публичные страницы доступны неавторизованному пользователю."""
        public_pages_url = (
            '/',
            f'/group/{PostURLTest.group.slug}/',
            f'/profile/{PostURLTest.user.username}/',
            f'/posts/{PostURLTest.post.pk}/',
        )
        for url in public_pages_url:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_private_pages_to_guest_user(self):
        """Приватные страницы редиректят неавторизованного пользователя."""
        private_pages_url = (
            '/create/',
            f'/posts/{PostURLTest.post.pk}/edit/',
            f'/posts/{PostURLTest.post.pk}/comment/'
        )
        for url in private_pages_url:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(
                    response,
                    f'{reverse("users:login")}?next={url}'
                )

    def test_unexisting_page_url(self):
        """Несуществующая страница выдает ошибку в кастомный шаблон."""
        response = self.guest_client.get('unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_urls_for_authorized_user(self):
        """Доступность страниц авторизованному пользователю/автору поста."""
        for url in PostURLTest.urls_templates.keys():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_redirect_not_author(self):
        """Редирект со страницы редактирования не-автора поста."""
        self.another_authorized_client = Client()
        self.another_authorized_client.force_login(
            User.objects.create_user(username='two')
        )
        post_id = PostURLTest.post.pk
        response = self.another_authorized_client.get(
            f'/posts/{post_id}/edit/',
            follow=True
        )
        self.assertRedirects(response, f'/posts/{post_id}/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in PostURLTest.urls_templates.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

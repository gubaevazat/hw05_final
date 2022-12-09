from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Post, User


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='one')
        cls.follow_user = User.objects.create_user(username='follow')
        cls.post = Post.objects.create(
            author=cls.follow_user,
            text='Тестовый пост'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(FollowTest.user)
        cache.clear()

    def test_authorized_follow_unfollow(self):
        """Авторизованный пользователь может подписаться/отписаться."""
        follows_count = Follow.objects.count()
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': FollowTest.follow_user.username}
        ))
        self.assertEqual(Follow.objects.count(), follows_count + 1)
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': FollowTest.follow_user.username}
        ))
        self.assertEqual(Follow.objects.count(), follows_count)

    def test_displayed_follow_posts(self):
        """Проверка отображения ленты подписок."""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': FollowTest.follow_user.username}
        ))
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertIn(FollowTest.post.text, response.content.decode())
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': FollowTest.follow_user.username}
        ))
        cache.clear()
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(FollowTest.post.text, response.content.decode())

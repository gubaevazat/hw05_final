import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import CommentForm
from posts.models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='one')
        cls.follower_user = User.objects.create_user(username='two')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост #0',
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewsTest.user)
        self.follower_client = Client()
        self.follower_client.force_login(PostViewsTest.follower_user)
        cache.clear()

    def reversor(self, page_value):
        if len(page_value) > 1:
            return reverse(page_value[0], args=[page_value[1]])
        return reverse(page_value[0])

    def test_views_uses_correct_template(self):
        """Проверка view-функции используют правильные шаблоны."""
        posts_pages = {
            ('posts:index',):
            'posts/index.html',
            ('posts:group_list', PostViewsTest.group.slug):
            'posts/group_list.html',
            ('posts:profile', PostViewsTest.user.username):
            'posts/profile.html',
            ('posts:post_detail', PostViewsTest.post.pk):
            'posts/post_detail.html',
            ('posts:post_create',):
            'posts/create_post.html',
            ('posts:post_edit', PostViewsTest.post.pk):
            'posts/create_post.html',
        }
        for page_name, template in posts_pages.items():
            with self.subTest(page_name=page_name):
                response = self.authorized_client.get(
                    self.reversor(page_name)
                )
                self.assertTemplateUsed(response, template)

    def test_views_paginator(self):
        """Тест пагинатора index, group_posts, profile."""
        pages = (
            ('posts:index',),
            ('posts:group_list', PostViewsTest.group.slug),
            ('posts:profile', PostViewsTest.user.username),
        )
        posts_on_pages = (
            (1, 10),
            (2, 3),
        )
        Post.objects.bulk_create([
            Post(
                author=PostViewsTest.user,
                group=PostViewsTest.group,
                text=f'Тест пост #{i}'
            )
            for i in range(1, 13)
        ])
        for page in pages:
            for page_number, posts_on_page in posts_on_pages:
                with self.subTest(page=page, page_number=page_number):
                    response = self.authorized_client.get(
                        self.reversor(page) + f'?page={page_number}'
                    )
                    self.assertIn('page_obj', response.context)
                    self.assertEqual(
                        len(response.context['page_obj']),
                        posts_on_page
                    )

    def test_index_context(self):
        """Тест контекста index."""
        context = self.authorized_client.get(reverse('posts:index')).context
        self.assertIn('page_obj', context)
        self.assertEqual(
            context['page_obj'].object_list,
            list(Post.objects.all())
        )
        self.assertEqual(
            context['page_obj'][0].image,
            f'posts/{PostViewsTest.uploaded.name}'
        )

    def test_post_detail_context(self):
        """Тест контекста post_detail."""
        expected_context = ('post', 'form', 'comments')
        context = self.authorized_client.get(self.reversor(
            ('posts:post_detail', PostViewsTest.post.pk)
        )).context
        for context_var in expected_context:
            with self.subTest(context_var=context_var):
                self.assertIn(context_var, context)
        self.assertEqual(context['post'], PostViewsTest.post)
        self.assertEqual(
            context['post'].image,
            f'posts/{PostViewsTest.uploaded.name}'
        )
        self.assertIsInstance(context['form'], CommentForm)

    def test_group_posts_context(self):
        """Тест контекста group_posts."""
        expected_context = ('page_obj', 'group')
        context = self.authorized_client.get(self.reversor(
            ('posts:group_list', PostViewsTest.group.slug)
        )).context
        for context_var in expected_context:
            with self.subTest(context_var=context_var):
                self.assertIn(context_var, context)
        self.assertEqual(
            context['page_obj'].object_list,
            list(PostViewsTest.group.posts.all())
        )
        self.assertEqual(context['group'], PostViewsTest.group)
        self.assertEqual(
            context['page_obj'][0].image,
            f'posts/{PostViewsTest.uploaded.name}'
        )

    def test_profile_context(self):
        """Тест контекста profile."""
        expected_context = ('page_obj', 'author')
        context = self.authorized_client.get(self.reversor(
            (('posts:profile', PostViewsTest.user.username))
        )).context
        for context_var in expected_context:
            with self.subTest(context_var=context_var):
                self.assertIn(context_var, context)
        self.assertEqual(
            context['page_obj'].object_list,
            list(PostViewsTest.group.posts.all())
        )
        self.assertEqual(context['author'], PostViewsTest.user)
        self.assertEqual(
            context['page_obj'][0].image,
            f'posts/{PostViewsTest.uploaded.name}'
        )

    def test_post_create_context(self):
        """Тест post_create на ожидаемые типы полей."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        response = self.authorized_client.get(reverse('posts:post_create'))
        for value, expected in form_fields.items():
            form_field = response.context['form'].fields[value]
            self.assertIsInstance(form_field, expected)

    def test_post_edit_context(self):
        """Тест post_edit на ожидаемый контекст."""
        post = PostViewsTest.post
        form_fields = {
            'text': post.text,
            'group': post.group.id,
            'image': post.image
        }
        response = self.authorized_client.get(self.reversor(
            ('posts:post_edit', post.pk)
        ))
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'][value].value()
                self.assertEqual(form_field, expected)

    def test_post_not_displayed_in_another_group(self):
        """Пост созданный в одной группе не отображается на странице другой."""
        self.another_group = Group.objects.create(
            title='Другая тест группа',
            slug='test-slug-another'
        )
        context = self.authorized_client.get(self.reversor(
            ('posts:group_list', self.another_group.slug)
        )).context
        self.assertIn('page_obj', context)
        self.assertNotIn(PostViewsTest.post, context['page_obj'])

    def test_add_comment_displayed_in_post_detail(self):
        """Отправленный комментарий отображается на странице поста."""
        form_data = {'text': 'Тест коммент'}
        self.authorized_client.post(
            self.reversor(('posts:add_comment', PostViewsTest.post.pk)),
            data=form_data,
            follow=True
        )
        context = self.authorized_client.get(self.reversor(
            ('posts:post_detail', PostViewsTest.post.pk)
        )).context
        self.assertIn('comments', context)
        self.assertEqual(context['comments'][0].text, form_data['text'])

    def post_text_content_return(self, post, page=('posts:index',)):
        response = self.authorized_client.get(self.reversor(page))
        return post.text, response.content.decode()

    def test_index_cache(self):
        """Тест кэширования главной страницы."""
        post_cache = Post.objects.create(
            text='Тест кэша',
            author=PostViewsTest.user
        )
        self.assertIn(*self.post_text_content_return(post_cache))
        post_cache.delete()
        self.assertIn(*self.post_text_content_return(post_cache))
        cache.clear()
        self.assertNotIn(*self.post_text_content_return(post_cache))

    def test_user_can_follow_an_author_not_following(self):
        """Пользователь может подписаться на автора,на которого не подписан."""
        follow = Follow.objects.filter(
            author=PostViewsTest.user,
            user=PostViewsTest.follower_user
        )
        self.assertTrue(not follow.exists())
        self.follower_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': PostViewsTest.user.username}
        ))
        self.assertTrue(follow.exists())

    def test_user_can_unfollow_an_author_following(self):
        """Пользователь может отписаться от автора, на которого подписан."""
        Follow.objects.create(
            author=PostViewsTest.user,
            user=PostViewsTest.follower_user
        )
        self.follower_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': PostViewsTest.user.username}
        ))
        self.assertTrue(not Follow.objects.filter(
            author=PostViewsTest.user,
            user=PostViewsTest.follower_user
        ).exists())

    def test_post_appears_on_following_page(self):
        """Пост появляется на странице подписок у подписчика."""
        self.follower_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': PostViewsTest.user.username}
        ))
        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertIn(PostViewsTest.post.text, response.content.decode())

    def test_post_appears_on_following_page(self):
        """Пост не появляется на странице подписок у не-подписчика."""
        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertNotIn(PostViewsTest.post.text, response.content.decode())

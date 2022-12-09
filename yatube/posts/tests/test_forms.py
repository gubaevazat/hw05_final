import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='one')
        cls.group = Group.objects.create(
            title=f'Тестовая группа #{cls.user.username}',
            slug=f'test-slug-{cls.user.username}',
            description=f'Тестовое описание #{cls.user.username}',
        )
        cls.form = PostForm()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.expected_data = {
            'group': cls.group,
            'author': cls.user,
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_create_post(self):
        """Валидная форма создает запись в базе данных."""
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=PostFormTests.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тест пост #1',
            'group': PostFormTests.group.pk,
            'image': uploaded,
        }
        PostFormTests.expected_data['text'] = form_data['text']
        PostFormTests.expected_data['image'] = (
            f"posts/{form_data['image'].name}"
        )
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post = Post.objects.latest('pub_date')
        self.assertEqual(Post.objects.count(), posts_count + 1)
        for field, value in PostFormTests.expected_data.items():
            with self.subTest(field=field):
                self.assertEqual(getattr(post, field), value)

    def test_edit_post(self):
        """Форма редактирования изменяет пост и не создает новую запись."""
        self.post = Post.objects.create(
            text='Тест пост #1',
            author=PostFormTests.user,
        )
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='another_small.gif',
            content=PostFormTests.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тест пост #2',
            'group': PostFormTests.group.pk,
            'image': uploaded,
        }
        PostFormTests.expected_data['text'] = form_data['text']
        PostFormTests.expected_data['image'] = (
            f"posts/{form_data['image'].name}"
        )
        self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}
            ),
            data=form_data,
            follow=True
        )
        post = Post.objects.latest('pub_date')
        self.assertEqual(Post.objects.count(), posts_count)
        for field, value in PostFormTests.expected_data.items():
            with self.subTest(field=field):
                self.assertEqual(getattr(post, field), value)

    def test_form_labels(self):
        """Проверка названий полей формы."""
        form_labels = {
            'text': 'Текст поста',
            'group': 'Группа',
        }
        for label, value in form_labels.items():
            with self.subTest(label=label):
                self.assertEqual(PostFormTests.form.fields[label].label, value)

    def test_form_help_text(self):
        """Проверка вспомагательного текста полей формы."""
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        for help_text, value in help_texts.items():
            with self.subTest(help_text=help_text):
                self.assertEqual(
                    PostFormTests.form.fields[help_text].help_text,
                    value
                )

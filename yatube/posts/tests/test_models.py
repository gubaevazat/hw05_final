from django.test import TestCase

from posts.models import Group, Post, User


class PostModelTest(TestCase):
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
            text='Тестовый пост ' * 5,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        expected_object_name = PostModelTest.group.title
        self.assertEqual(str(PostModelTest.group), expected_object_name)
        expected_object_name = (
            f'{PostModelTest.post.text[:15]} '
            f'Автор: {PostModelTest.post.author}, '
            f'дата: {PostModelTest.post.pub_date:%d-%m-%Y %H:%M}.'
        )
        self.assertEqual(str(PostModelTest.post), expected_object_name)

    def check_model_fields_verbose_names(self, field_verboses, model_object):
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    model_object._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_models_fields_verbose_names(self):
        """Проверяем корректность verbose_name у полей моделей."""
        field_verboses_group = {
            'title': 'Название',
            'slug': 'Идентификатор',
            'description': 'Описание',
        }
        field_verboses_post = {
            'text': 'Текст',
            'pub_date': 'Дата',
            'author': 'Автор',
            'group': 'Группа',
        }
        self.check_model_fields_verbose_names(
            field_verboses_group,
            PostModelTest.group
        )
        self.check_model_fields_verbose_names(
            field_verboses_post,
            PostModelTest.post
        )

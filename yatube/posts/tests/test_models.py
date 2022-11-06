from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый-слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост c текстом более 15 симфолов',
            group=cls.group
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        expected_values = [
            (
                self.post,
                self.post.text[:Post.LETTERS_LIMIT]
            ),
            (
                self.group,
                self.group.title
            )
        ]

        for obj, expected_obj_name in expected_values:
            with self.subTest():
                self.assertEqual(
                    str(obj),
                    expected_obj_name,
                    (
                        f'Не совпало имя объекта класса"{obj.__class__}". '
                        f'Ожидалось "{expected_obj_name}"'
                    )
                )

    def test_post_verbose_name(self):
        """Проверяем verbose_name в полях модели Post"""
        field_verboses = [
            ('title', 'Заголовок'),
            ('text', 'Текст статьи'),
            ('created', 'Дата создания'),
            ('author', 'Автор'),
            ('group', 'Сообщество')
        ]

        for field, expected_value in field_verboses:
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value,
                    f'Не совпало verbose_name у поля "{field}"')

    def test_post_help_text(self):
        """Проверяем help_text в полях модели Post"""
        field_help_texts = [
            ('title', 'Укажите заголовок Вашей статьи'),
            ('text', 'напишите что-нибудь интересное'),
            ('created', 'Укажите дату создания'),
            ('author', 'Укажите автора поста'),
            (
                'group',
                (
                    'укажите рубрику, в которой будет опубликован '
                    'пост или оставьте пустым'
                )
            )
        ]

        for field, expected_value in field_help_texts:
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text,
                    expected_value,
                    f'Не совпал help_text у поля "{field}"')

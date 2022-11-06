from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from posts.models import Post, Group

User = get_user_model()


class UserCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.user = User.objects.create(username='test_user')

        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group
        )

    def test_user_creates_correctly(self):
        """Проверяем, что новый пользователь создается корректно"""

        data = {
            'username': 'new_test_user',
            'first_name': 'Тестер',
            'last_name': 'Тестеров',
            'email': 'test@test.test',
            'password1': 'djry_123_djfnl',
            'password2': 'djry_123_djfnl'
        }
        response = self.client.post(reverse('users:signup'), data, follow=True)

        # Проверяем, что пользователь создался
        self.assertTrue(
            User.objects.filter(
                username=data['username']
            ).exists(),
            (
                'Ожидалось, что будет создан пользователь '
                f'с username = {data["username"]}, '
                'но такой пользователь не найден'
            )
        )

        # Проверяем, что после создания нового пользователя
        # произошел redirect на страницу index.html
        self.assertRedirects(
            response, reverse('posts:index'),
            msg_prefix=(
                'Ожидалось, что после регистрации '
                'пользователь будет перенаправлен '
                'на страницу index.html'
            )
        )

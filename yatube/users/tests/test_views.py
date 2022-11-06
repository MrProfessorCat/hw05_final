from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django import forms

User = get_user_model()


class UserPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(UserPagesTest.user)

    def test_pages_correct_templates(self):
        """Проверяем, что во view-функциях используются
        правильные html-шаблоны"""

        view_names_tamplates = {
            'users:signup': 'users/signup.html',
            'users:password_reset_form': 'users/password_reset_form.html',
            'users:password_reset_done': 'users/password_reset_done.html',
            'users:password_reset_complete': ('users/'
                                              'password_reset_complete.html'),
            'users:password_change': 'users/password_change_form.html',
            'users:password_change_done': 'users/password_change_done.html',
            'users:login': 'users/login.html',
            'users:logout': 'users/logged_out.html',
        }

        for view_name, template in view_names_tamplates.items():
            with self.subTest(view_name=view_name):
                response = self.authorized_client.get(reverse(view_name))
                self.assertTemplateUsed(response, template)

        response = self.authorized_client.get(
            reverse(
                'users:password_reset_confirm',
                kwargs={
                    'uidb64': 'NA',
                    'token': '653-5463ce7afc2926af7bc7'
                }
            )
        )
        self.assertTemplateUsed(response, 'users/password_reset_confirm.html')

    def test_signup_page_shows_correct_context(self):
        """Проверяем, что signup.html сформирован с правильным контекстом.
        Проверьте, что на страницу в контексте передаётся форма
        для создания нового пользователя.
        """
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField,
            'password1': forms.CharField,
            'password2': forms.CharField
        }
        response = self.authorized_client.get(reverse('users:signup'))
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(
                    form_field, expected,
                    (
                        f'Тип поля формы "{value}" '
                        f'не совпал с ожидаемым {expected}'
                    )
                )

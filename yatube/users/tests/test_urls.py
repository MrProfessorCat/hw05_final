'''TODO:
    1. Страницы доступны по ожидаемому адресу.
    2. Для страницы вызывается ожидаемый HTML-шаблон.
    3. Если у пользователя нет прав для просмотра страниц — они недоступны;
       происходит переадресация на ожидаемую целевую страницу.
'''

from http import HTTPStatus

from django.test import Client, TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UserURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='test_user',
            password='jdhfgih__21232'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(UserURLTest.user)

    def test_urls_uses_correct_templates(self):
        """Проверяем, что для страницы вызывается ожидаемый HTML-шаблон"""
        templates_url_names = {
            '/auth/password_change/': 'users/password_change_form.html',
            '/auth/password_change/done/': 'users/password_change_done.html',
            '/auth/login/': 'users/login.html',
            '/auth/signup/': 'users/signup.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
            '/auth/reset/NA/653-5463ce/': 'users/password_reset_confirm.html',
            '/auth/reset/done/': 'users/password_reset_complete.html',
            '/auth/logout/': 'users/logged_out.html',

        }

        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(
                    response, template,
                    f'По адресу {url} ожидался шаблон {template}'
                )

    def test_pages_available_by_url(self):
        """Проверяем, что страницы доступны по ожидаемому адресу."""
        urls = [
            '/auth/password_change/',
            '/auth/password_change/done/',
            '/auth/login/',
            '/auth/signup/',
            '/auth/password_reset/',
            '/auth/password_reset/done/',
            '/auth/reset/NA/653-5463ce/',
            '/auth/reset/done/',
            '/auth/logout/'
        ]

        for url in urls:
            response = self.authorized_client.get(url)
            self.assertEqual(
                response.status_code,
                HTTPStatus.OK,
                (
                    f'По адресу {url} получен '
                    f'код ответа {response.status_code}, '
                    f'а ожидался {HTTPStatus.OK}'
                )
            )

    def test_guest_redirects(self):
        """Проверяем, что неавторизованный пользователь будет
        перенаправлен со страниц изменения пароля, подтверждения
        смены пароля"""
        urls = [
            '/auth/password_change/',
            '/auth/password_change/done/',
        ]
        redirect_prefix = '/auth/login/?next='
        for url in urls:
            response = self.client.get(url)
            self.assertRedirects(
                response,
                redirect_prefix + url
            )

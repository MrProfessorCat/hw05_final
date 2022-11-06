from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse


class AboutURLTest(TestCase):
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/about/author/': 'about/about.html',
            '/about/tech/': 'about/tech.html'
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertTemplateUsed(
                    response, template,
                    f'По адресу {url} ожидался шаблон {template}'
                )

    def test_url_exists(self):
        """Проверяем доступность страниц"""
        urls = [
            '/about/author/',
            '/about/tech/'
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    (
                        f'По адресу {url} ожидался код ответа {HTTPStatus.OK} '
                        f'а получен {response.status_code}'
                    )
                )

    def test_pages_correct_templates(self):
        """Проверяем, что во view-функциях используются
       правильные html-шаблоны"""
        views_names_templates = {
            'about:author': 'about/about.html',
            'about:tech': 'about/tech.html'
        }

        for view_name, template in views_names_templates.items():
            with self.subTest(view_name=view_name):
                response = self.client.get(reverse(view_name))
                self.assertTemplateUsed(response, template)

'''TODO:
    1. Страницы доступны по ожидаемому адресу.
    2. Для страницы вызывается ожидаемый HTML-шаблон.
    3. Если у пользователя нет прав для просмотра страниц — они недоступны;
       происходит переадресация на ожидаемую целевую страницу.
    4. Проверьте, что запрос к несуществующей странице вернёт ошибку 404
'''

from http import HTTPStatus
from collections import namedtuple

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse

from ..models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст тестового поста',
            group=cls.group
        )
        cls.user_noauthor = User.objects.create_user(username='user_noauthor')
        cls.unexisting_page_url = '/unexisting_page/'

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_reverse(self):
        """Проверяем соответствие фактических url с их именами"""
        url_names = (
            ('/', reverse('posts:index')),
            ('/create/', reverse('posts:post_create')),
            (
                f'/group/{self.group.slug}/',
                reverse(
                    'posts:group_list',
                    kwargs={'slug': self.group.slug}
                )
            ),
            (
                f'/profile/{self.user.username}/',
                reverse(
                    'posts:profile',
                    kwargs={'username': self.user.username}
                )
            ),
            (
                f'/posts/{self.post.id}/',
                reverse(
                    'posts:post_detail',
                    kwargs={'post_id': self.post.id}
                )
            ),
            (
                f'/posts/{self.post.id}/edit/',
                reverse(
                    'posts:post_edit',
                    kwargs={'post_id': self.post.id}
                )
            ),
            (
                f'/posts/{self.post.id}/comment/',
                reverse(
                    'posts:add_comment',
                    kwargs={'post_id': self.post.id}
                )
            ),
            (
                '/follow/',
                reverse('posts:follow_index')
            ),
            (
                f'/profile/{self.user.username}/follow/',
                reverse(
                    'posts:profile_follow',
                    kwargs={'username': self.user.username}
                )
            ),
            (
                f'/profile/{self.user.username}/unfollow/',
                reverse(
                    'posts:profile_unfollow',
                    kwargs={'username': self.user.username}
                )
            )
        )

        for url, reversed_url_name in url_names:
            with self.subTest():
                self.assertEqual(
                    url, reversed_url_name,
                    f'Ожидалось получить фактический путь {url}, '
                    f'а получили {reversed_url_name}'
                )

    def test_urls_uses_correct_templates(self):
        """Проверяем, что для страницы вызывается ожидаемый HTML-шаблон"""
        templates_url_names = [
            (reverse('posts:index'), 'posts/index.html'),
            (reverse('posts:post_create'), 'posts/create_post.html'),
            (
                reverse(
                    'posts:group_list',
                    kwargs={'slug': self.group.slug}
                ),
                'posts/group_list.html'
            ),
            (
                reverse(
                    'posts:profile',
                    kwargs={'username': self.user.username}
                ),
                'posts/profile.html'
            ),
            (
                reverse(
                    'posts:post_detail',
                    kwargs={'post_id': self.post.id}
                ),
                'posts/post_detail.html'
            ),
            (
                reverse(
                    'posts:post_edit',
                    kwargs={'post_id': self.post.id}
                ),
                'posts/create_post.html'
            ),
            (
                self.unexisting_page_url,
                'core/404.html'
            )
        ]
        for url, template in templates_url_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(
                    response, template,
                    f'По адресу {url} ожидался шаблон {template}'
                )

    def test_url_exists(self):
        """Проверяем, что страницы доступны по ожидаемому адресу."""
        UrlsStatus = namedtuple(
            'UrlsStatus',
            ['url', 'status_code', 'need_authorise']
        )
        urls = [
            UrlsStatus(
                url=reverse('posts:index'),
                status_code=HTTPStatus.OK,
                need_authorise=False),
            UrlsStatus(
                url=reverse(
                    'posts:group_list',
                    kwargs={'slug': self.group.slug}),
                status_code=HTTPStatus.OK,
                need_authorise=False),
            UrlsStatus(
                url=reverse(
                    'posts:profile',
                    kwargs={'username': self.user.username}),
                status_code=HTTPStatus.OK,
                need_authorise=False),
            UrlsStatus(
                url=reverse(
                    'posts:post_detail',
                    kwargs={'post_id': self.post.id}),
                status_code=HTTPStatus.OK,
                need_authorise=False),
            UrlsStatus(
                url=self.unexisting_page_url,
                status_code=HTTPStatus.NOT_FOUND,
                need_authorise=False),
            UrlsStatus(
                url=reverse('posts:post_create'),
                status_code=HTTPStatus.OK,
                need_authorise=True),
            UrlsStatus(
                url=reverse(
                    'posts:post_edit',
                    kwargs={'post_id': self.post.id}),
                status_code=HTTPStatus.OK,
                need_authorise=True
            )
        ]

        for url_status in urls:
            with self.subTest(url=url_status.url):
                if url_status.need_authorise:
                    response = self.authorized_client.get(url_status.url)
                else:
                    response = self.client.get(url_status.url)
                self.assertEqual(
                    response.status_code,
                    url_status.status_code,
                    (
                        f'По адресу {url_status.url} получен '
                        f'код ответа {response.status_code}, '
                        f'а ожидался {url_status.status_code}'
                    )
                )

    def test_redirects_for_guest_user(self):
        """Проверяем, что происходит перенаправление неавторизованного
        пользователя при попытке обратится к страницам, доступным только
        авторизованному пользователю"""
        redirect_prefix = '/auth/login/?next='
        urls = [
            reverse('posts:post_create'),
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}),
        ]
        for url in urls:
            with self.subTest():
                response = self.client.get(url, follow=True)
                self.assertRedirects(
                    response,
                    f'{redirect_prefix}{url}'
                )

    def test_edit_page_redirects_noauthor(self):
        """Проверяем, что неавтор поста перенаправляется со страницы
        изменения поста на страницу информации о посте"""

        url = reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.id})
        expected_url = reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id})
        self.authorized_client.force_login(
            self.user_noauthor
        )
        response = self.authorized_client.get(url)
        self.assertRedirects(
            response,
            expected_url,
            msg_prefix=(
                'Ожидалось что неавтор поста будет перенаправлен '
                f'на страницу {expected_url}'
            )
        )

'''TODO:
    Протестируйте шаблоны, словарь контекста, паджинатор и
       отображение поста на различных страницах проекта.
    1. Напишите тесты, проверяющие, что во view-функциях используются
       правильные html-шаблоны.
    2. Проверьте, соответствует ли ожиданиям словарь context,
       передаваемый в шаблон при вызове.
    3. Проверьте, что если при создании поста указать группу,
       то этот пост появляется
        - на главной странице сайта,
        - на странице выбранной группы,
        - в профайле пользователя.
       Проверьте, что этот пост не попал в группу,
       для которой не был предназначен.
'''
import math
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.core.cache import cache
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Post, Group, Comment, Follow


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.user_to_follow = User.objects.create(username='follow_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.new_group = Group.objects.create(
            title='Новая тестовая группа',
            slug='new-test-slug',
            description='Новое тестовое описание',
        )
        test_image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded_img = SimpleUploadedFile(
            name='image.gif',
            content=test_image,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст тестового поста',
            group=cls.group,
            image=uploaded_img
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Тестовый комментарий',
            post=cls.post
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def match_model_fields(self, model, expected_data):
        for field in model._meta.fields:
            with self.subTest():
                if field.name in expected_data.keys():
                    self.assertEqual(
                        field.value_from_object(model),
                        expected_data.get(field.name),
                        (
                            f'Ожидалось, что у поля {field.name} '
                            f'будет значение {expected_data.get(field.name)}, '
                            f'а получили {field.value_from_object(model)}'
                        )
                    )

    def context_matches_expected_fields(self, post):
        context_expected_fields = [
            ('text', post.text, self.post.text),
            ('author', post.author, self.post.author),
            ('group', post.group, self.post.group),
            ('image', post.image, self.post.image)
        ]
        for field, field_value, expected_value in context_expected_fields:
            with self.subTest(field=field):
                self.assertEqual(
                    field_value, expected_value,
                    (
                        f'У поля {field} '
                        f'ожидалось значение "{expected_value}", '
                        f'а получили "{field_value}"'
                    )
                )

    def test_pages_shows_correct_context(self):
        """Проверяем, что шаблоны сформированы с правильным контекстом.
        """
        urls = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        ]
        for url in urls:
            with self.subTest():
                response = self.authorized_client.get(url)
                posts = response.context.get('page_obj')
                self.context_matches_expected_fields(posts[0])

    def test_post_detail_page_shows_correct_context(self):
        """Проверяем, что post_detail.html сформирован с правильным контекстом.
        """
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        post = response.context.get('post')
        self.context_matches_expected_fields(post)

    def test_create_post_page_shows_correct_context(self):
        """Проверяем, что create_post.html при создании поста
         сформирован с правильным контекстом.
        """
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertIsInstance(
            response.context.get('form'),
            PostForm)

    def test_created_post_not_in_other_group(self):
        """Проверяем, что созданный пост с указанной группой
        не не попал в группу, для которой не был предназначен"""

        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.new_group.slug})
        )
        posts_on_page = response.context.get('page_obj')
        self.assertNotIn(
            self.post, posts_on_page,
            (
                f'Пост со слагом группы "{self.group.slug}" '
                'попал на страницу group_list.html c выборкой групп '
                f'по слагу "{self.new_group.slug}"'
            )
        )

    def test_edit_post_page_shows_correct_context(self):
        """Проверяем, что create_post.html при редактировании
         сформирован с правильным контекстом.
        """
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertIsInstance(
            response.context.get('form'), PostForm
        )
        self.assertEqual(
            response.context.get('form').instance,
            self.post)

    def test_comment_appears_on_page(self):
        """Проверяем, что после отправки комментарий появился на странице"""

        response = self.client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertIn(
            self.comment,
            response.context.get('comments'),
            (
                f'Ожидалось, что комментарий "{self.comment}" '
                f'попадет на страницу поста {self.post} '
            )
        )

    def test_cache(self):
        """Проверяем работу кеша"""
        # Кеш очищен. Создаем пост
        post = Post.objects.create(
            author=self.user,
            text='Текст поста для кеша',
            group=self.group
        )
        # Обращаемся к главной странице. Данные попадают в кеш
        response_before = self.client.get(reverse('posts:index'))

        # Удаляем пост из базы
        post.delete()

        # Получаем данные с главной страницы и проверяем,
        # что контент страницы не изменился
        self.assertEqual(
            response_before.content,
            self.client.get(reverse('posts:index')).content,
            (
                f'Ожтдалось что пост «{post}» будет закеширован '
                'и отобразится на главной странице'
            )
        )

        # принудительно очищаем кеш
        cache.clear()

        # проверяем, что теперь удаленного поста нет на странице
        self.assertNotIn(
            post,
            self.client.get(reverse('posts:index')).context.get('page_obj')
        )

    def test_authorised_user_can_follow(self):
        """Проверяем, что авторизованный пользователь может
        подписываться на других пользователей"""

        # user подписывается на пользователя user_to_follow
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_to_follow.username}
            )
        )
        # Проверяем, что в таблице posts_follow появилась запись
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.user_to_follow
            ).exists()
        )

    def test_authorised_user_can_unfollow(self):
        """Проверяем, что авторизованный пользователь может
        отписываться от других пользователей"""

        Follow.objects.create(
            user=self.user,
            author=self.user_to_follow
        )

        # user отписывается от пользователя user_to_follow
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user_to_follow.username}
            )
        )

        # Проверяем, что из таблицы posts_follow удалилась запись
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.user_to_follow
            ).exists()
        )

    def test_user_cannot_follow_himself(self):
        """Проверяем, что пользователь не может подписаться
        на самого себя"""
        Follow.objects.all().delete()
        # user подписывается на самого себя
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user.username}
            )
        )
        # Проверяем, что в таблице posts_follow нет записей
        EXPECTED_FOLLOWERS = 0
        self.assertEqual(
            Follow.objects.count(),
            EXPECTED_FOLLOWERS,
            f'Ожидалось, что будет {EXPECTED_FOLLOWERS} записей'
        )

    def test_new_post_available_for_followers(self):
        """Проверяем, что новая запись пользователя появляется
        в ленте тех, кто на него подписан и не появляется в ленте
        тех, кто не подписан."""
        # user подписывается на пользователя user_to_follow
        Follow(
            user=self.user,
            author=self.user_to_follow
        ).save()

        # user_to_follow создает новый пост
        post = Post.objects.create(
            author=self.user_to_follow,
            text='Тестовый текст'
        )
        # user обращается к странице с избранными авторами
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        # проверяем, что на этой странице появился новый пост
        self.assertIn(
            post,
            response.context.get('page_obj'),
            (
                f'Ожидалось, что пост "{post}" '
                f'попадет на страницу'
            )
        )

        # user_to_follow обращается к странице с избранными авторами
        self.authorized_client.force_login(self.user_to_follow)
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )

        # проверяем, что на этой странице нет нового пост,
        # так как user_to_follow не подписан сам на себя
        self.assertNotIn(
            post,
            response.context.get('page_obj'),
            (
                f'Ожидалось, что пост "{post}" '
                f'попадет на страницу'
            )
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        ADDITIONAL_POSTS = 5
        cls.posts_num = settings.POSTS_ON_PAGE + ADDITIONAL_POSTS
        cls.posts = Post.objects.bulk_create(
            [
                Post(
                    author=cls.user,
                    text='Текст тестового поста',
                    group=cls.group
                ) for _ in range(cls.posts_num)
            ]
        )
        cls.views_names = [
            ('posts:index', None),
            ('posts:group_list', {'slug': cls.group.slug}),
            ('posts:profile', {'username': cls.user.username})
        ]

    def setUp(self):
        cache.clear()

    def test_first_page_contains_propper_records_count(self):
        """Проверяем, что первая страница содержит нужное
        кол-во постов"""
        for view_name, kwargs in self.views_names:
            with self.subTest(view_name=view_name):
                response = self.client.get(
                    reverse(view_name, kwargs=kwargs)
                )
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.POSTS_ON_PAGE)

    def test_last_page_contains_remaining_records(self):
        """Проверяем, что последняя страница содержит оставшиеся посты"""
        pages_num = math.ceil(self.posts_num / settings.POSTS_ON_PAGE)

        posts_num_on_last_page = (
            self.posts_num
            - (pages_num - 1) * settings.POSTS_ON_PAGE
        )

        for view_name, kwargs in self.views_names:
            with self.subTest(view_name=view_name):
                response = self.client.get(
                    reverse(view_name, kwargs=kwargs) + f'?page={pages_num}'
                )
                self.assertEqual(
                    len(response.context['page_obj']),
                    posts_num_on_last_page,
                    (
                        f'На последней странице ожидалось '
                        f'{posts_num_on_last_page} постов, '
                        f'а получено {len(response.context["page_obj"])}'
                    )
                )

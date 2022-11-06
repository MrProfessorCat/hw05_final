import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Post, Group, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
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
        # Новая группу, которая будет указана в измененном посту
        cls.new_group = Group.objects.create(
            title='Тестовая группа, в которую поместим пост при изменении',
            slug='new-test-edit-slug',
            description='Тестовое описание',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Очищаем кеш, чтобы его содержимое не повлияло на тесты
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def match_model_fields(self, model, expected_data):
        for field in model._meta.fields:
            with self.subTest():
                if (field.name in expected_data.keys()
                        and field.name != 'image'):
                    self.assertEqual(
                        field.value_from_object(model),
                        expected_data.get(field.name),
                        (
                            f'Ожидалось, что у поля {field.name} '
                            f'будет значение {expected_data.get(field.name)}, '
                            f'а получили {field.value_from_object(model)}'
                        )
                    )

    def test_post_creates_correctly(self):
        """Проверяем, что пост создается корректно"""

        # Данные для записи
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

        data = {
            'text': 'Новый тестовый пост',
            'group': self.group.id,
            'image': uploaded_img
        }

        Post.objects.all().delete()

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=data, follow=True
        )

        # Проверяем, что после создания поста произошел redirect
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ),
            msg_prefix=(
                'Ожидалось, что после создания поста '
                'пользователь будет перенаправлен '
                'на страницу profile.html'
            )
        )

        # Ожидаемое число постов после записи нового поста
        EXPECTED_POST_COUNT = 1

        self.assertEqual(
            Post.objects.count(), EXPECTED_POST_COUNT,
            'Ожидалось, что после создания поста '
            f'общее число постов станет равным {EXPECTED_POST_COUNT}, '
            f'а получили {Post.objects.count()} постов'
        )

        # Проверяем, что пост записался с заданными данными
        post = Post.objects.first()
        self.match_model_fields(post, data)

        # Отдельно проверяем, что записалась картинка
        self.assertEqual(
            post.image,
            f'posts/{uploaded_img.name}',
            'Ожидалось, что картинка запишется в базу'
        )

        # Проверяем, что автором поста стал авторизованный пользователь
        self.assertEqual(
            post.author,
            self.user,
            (
                'Ожидалось, что автором поста будет '
                f'авторизованный пользователь {self.user}, '
                f'а автором является {post.author}'
            )
        )

    def test_post_edits_correctly(self):
        """Проверяем, что редактирование поста осуществляется корректно"""
        # Измененные данные поста
        new_data = {
            'text': 'Текст поста с изменениями',
            'group': self.new_group.id
        }

        url = reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.id}
        )
        post_author_before = self.post.author
        self.authorized_client.post(url, new_data)

        # Проверяем, что пост записался с измененными данными
        post = Post.objects.get(id=self.post.id)
        self.match_model_fields(post, new_data)

        self.assertEqual(
            post.author,
            post_author_before,
            'Ожидалось, что автор поста не изменится'
        )

    def test_guest_denied_comments(self):
        """Проверяем, что неавторизованный пользователь не может
        комментировать посты"""

        Comment.objects.all().delete()

        self.client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data={'text': 'Текст комментария'}
        )

        comments_count = Comment.objects.count()
        EXPECTED_COMMENTS_COUNT = 0
        self.assertEqual(
            comments_count,
            EXPECTED_COMMENTS_COUNT,
            f'Ожидалось что комментариев будет {EXPECTED_COMMENTS_COUNT}, '
            f'а получили {comments_count}'
        )

from django.contrib.auth import get_user_model
from django.db import models

from core.models import CreatedModel

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Название',
        help_text='Укажите название группы'
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Адрес',
        help_text='Адрес страницы с постами из группы'
    )
    description = models.TextField(
        verbose_name='Описание',
        help_text=('Укажите описание группы - набор тем и вопросов, '
                   'которые будут обсуждаться в группе')
    )

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self) -> str:
        return self.title


class Post(CreatedModel):
    LETTERS_LIMIT = 15

    text = models.TextField(
        verbose_name='Текст статьи',
        help_text='напишите что-нибудь интересное'
    )
    title = models.CharField(
        max_length=100,
        verbose_name='Заголовок',
        help_text='Укажите заголовок Вашей статьи',
        blank=True,
        null=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
        help_text='Укажите автора поста'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='Сообщество',
        help_text=(
            'укажите рубрику, в которой будет опубликован пост '
            'или оставьте пустым'
        ),
        related_name='posts'
    )
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        verbose_name='Картинка к посту',
        help_text='добавьте каринку и ваш пост станет ярче'
    )

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:self.LETTERS_LIMIT]


class Comment(CreatedModel):
    LETTERS_LIMIT = 15

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Комментарий',
        help_text='Укажите пост, к которому пишите комментарий',
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор комментария',
        help_text='Выберите автора комментария',
        related_name='comments'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Напишите комментарий и нажмите кнопку Отправить'
    )

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text[:self.LETTERS_LIMIT]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        help_text='Пользователь, который подписывается',
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        help_text='Автор, на которого пдписываемся',
        related_name='following'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from django.contrib.auth.decorators import login_required

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow


def get_page_posts(page_number, posts):
    paginator = Paginator(posts, settings.POSTS_ON_PAGE)
    return paginator.get_page(page_number)


def index(request):
    posts = Post.objects.select_related(
        'author',
        'group')
    context = {
        'page_obj': get_page_posts(request.GET.get('page'), posts),
        'cache_time': settings.CACHE_TIME
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    context = {
        'group': group,
        'page_obj': get_page_posts(request.GET.get('page'), posts),
        'group_posts_page': True
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(
        User,
        username=username
    )
    author_posts = author.posts.select_related('group')
    context = {
        'page_obj': get_page_posts(request.GET.get('page'), author_posts),
        'author': author,
        'editable': author == request.user,
        'following': (
            not request.user.is_anonymous
            and Follow.objects.filter(
                author=author,
                user=request.user
            ).exists()
        )
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        pk=post_id
    )
    comments = post.comments.select_related('author')
    context = {
        'post': post,
        'posts_count': post.author.posts.count(),
        'form': CommentForm(),
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    post_form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if post_form.is_valid():
        post = post_form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)

    context = {'form': post_form}
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post.objects.select_related('author'), id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post.id)
    post_form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if post_form.is_valid():
        post_form.save()
        return redirect('posts:post_detail', post.id)
    context = {
        'form': post_form,
        'is_edit': True}
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    followers = Follow.objects.filter(
        user=request.user).select_related('author')
    posts = []
    for follower in followers:
        posts.extend(
            follower.author.posts.select_related('author', 'group')
        )
    context = {'page_obj': get_page_posts(request.GET.get('page'), posts)}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if (
        author != request.user
        and not Follow.objects.filter(
            user=request.user,
            author=author).exists()
    ):
        Follow.objects.create(
            user=request.user,
            author=author
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    get_object_or_404(
        Follow,
        user=request.user,
        author=User.objects.get(username=username)
    ).delete()
    return redirect('posts:profile', username=username)

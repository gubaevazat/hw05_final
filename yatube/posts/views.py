from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from posts.forms import CommentForm, PostForm
from posts.models import Follow, Group, Post, User

POSTS_PER_PAGE = 10


def paginator_page(request, query_set, posts_per_page=POSTS_PER_PAGE):
    return Paginator(
        query_set, posts_per_page
    ).get_page(request.GET.get('page'))


def index(request):
    return render(request, 'posts/index.html', {
        'page_obj': paginator_page(
            request,
            Post.objects.select_related('author', 'group'),
        ),
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': paginator_page(
            request,
            group.posts.select_related('author')
        ),
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    return render(request, 'posts/profile.html', {
        'author': author,
        'page_obj': paginator_page(
            request,
            author.posts.select_related('group')
        ),
        'following': user.is_authenticated and user.follower.filter(
            author=author
        ).exists()
    })


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        pk=post_id
    )
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'comments': post.comments.all(),
        'form': CommentForm()
    })


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {
            'form': form,
            'is_edit': False,
        })
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', request.user)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/create_post.html', {
        'form': form,
        'is_edit': True,
    })


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if not form.is_valid():
        return redirect('posts:post_detail', post_id)
    comment = form.save(commit=False)
    comment.author = request.user
    comment.post = post
    comment.save()
    return redirect('posts:post_detail', post_id)


@login_required
def follow_index(request):
    return render(request, 'posts/follow.html', {
        'page_obj': paginator_page(
            request,
            Post.objects.filter(author__following__user=request.user)
        )
    })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username)

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Post


def broadcast_post_update(action, post_data=None, post_id=None):
    """WebSocketを通じて投稿の変更をブロードキャスト"""
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            "posts_updates",
            {
                "type": f"post_{action}",
                "post": post_data,
                "post_id": post_id,
            },
        )


def index(request):
    """ホームページ - 投稿一覧を表示"""
    posts = Post.objects.all()
    return render(request, "sampleapp/index.html", {"posts": posts})


def post_detail(request, pk):
    """投稿詳細ページ"""
    post = get_object_or_404(Post, pk=pk)
    return render(request, "sampleapp/detail.html", {"post": post})


def create_post(request):
    """投稿作成"""
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")

        if title and content:
            post = Post.objects.create(title=title, content=content)
            messages.success(request, "投稿が作成されました！")

            # WebSocketで新しい投稿をブロードキャスト
            post_data = {
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "created_at": post.created_at.isoformat(),
                "updated_at": post.updated_at.isoformat(),
            }
            broadcast_post_update("created", post_data)

            return redirect("post_detail", pk=post.pk)
        else:
            messages.error(request, "タイトルと内容は必須です。")

    return render(request, "sampleapp/create.html")


def delete_post(request, pk):
    """投稿削除"""
    if request.method == "POST":
        post = get_object_or_404(Post, pk=pk)
        post_id = post.id
        post.delete()
        messages.success(request, "投稿が削除されました！")

        # WebSocketで削除をブロードキャスト
        broadcast_post_update("deleted", post_id=post_id)

        return redirect("index")
    return redirect("index")


def api_posts(request):
    """API: 投稿一覧を JSON で返す"""
    posts = Post.objects.all().values("id", "title", "content", "created_at")
    return JsonResponse({"posts": list(posts)})


def health_check(request):
    """ヘルスチェック用エンドポイント"""
    return JsonResponse({"status": "ok", "service": "Django + Nginx Sample"})

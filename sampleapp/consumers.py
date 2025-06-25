import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Post
from .tasks import random_message_generator


class PostConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """WebSocket接続時の処理"""
        self.room_group_name = "posts_updates"

        # グループに参加
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        # 接続時に現在の投稿一覧を送信
        posts = await self.get_posts()
        await self.send(text_data=json.dumps({"type": "posts_list", "posts": posts}))

        # ランダムメッセージタスクを開始（最初の接続時のみ）
        if not random_message_generator.is_running:
            # バックグラウンドでタスクを開始
            import threading

            def start_task():
                import asyncio

                asyncio.run(random_message_generator.start_random_messages())

            thread = threading.Thread(target=start_task, daemon=True)
            thread.start()
        await self.send(text_data=json.dumps({"type": "posts_list", "posts": posts}))

    async def disconnect(self, close_code):
        """WebSocket切断時の処理"""
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """クライアントからのメッセージ受信"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get("type")

            if message_type == "get_posts":
                # 投稿一覧の取得要求
                posts = await self.get_posts()
                await self.send(text_data=json.dumps({"type": "posts_list", "posts": posts}))

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"type": "error", "message": "Invalid JSON"}))

    async def post_created(self, event):
        """新しい投稿が作成された時の処理"""
        await self.send(text_data=json.dumps({"type": "post_created", "post": event["post"]}))

    async def post_updated(self, event):
        """投稿が更新された時の処理"""
        await self.send(text_data=json.dumps({"type": "post_updated", "post": event["post"]}))

    async def post_deleted(self, event):
        """投稿が削除された時の処理"""
        await self.send(text_data=json.dumps({"type": "post_deleted", "post_id": event["post_id"]}))

    async def random_message(self, event):
        """ランダムメッセージを受信した時の処理"""
        await self.send(text_data=json.dumps({"type": "random_message", "message": event["message"]}))

    @database_sync_to_async
    def get_posts(self):
        """投稿一覧を取得"""
        posts = list(Post.objects.all().values("id", "title", "content", "created_at", "updated_at"))
        # 日時をISO形式の文字列に変換
        for post in posts:
            post["created_at"] = post["created_at"].isoformat()
            post["updated_at"] = post["updated_at"].isoformat()
        return posts

import asyncio
import random
import string
import time
from datetime import datetime
from channels.layers import get_channel_layer


class RandomMessageGenerator:
    """ランダムメッセージを定期的に生成するクラス"""

    def __init__(self):
        self.is_running = False
        self.task = None

    def generate_random_string(self, length=10):
        """ランダムな文字列を生成"""
        characters = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
        return "".join(random.choice(characters) for _ in range(length))

    def get_random_message_type(self):
        """ランダムなメッセージタイプを選択"""
        message_types = ["システム通知", "お知らせ", "アラート", "更新情報", "ニュース", "ランダムメッセージ"]
        return random.choice(message_types)

    async def send_random_message(self):
        """ランダムメッセージをWebSocketで送信"""
        channel_layer = get_channel_layer()
        if not channel_layer:
            print("Channel layerが利用できません")
            return

        # ランダムなメッセージを生成
        message_content = self.generate_random_string(random.randint(10, 50))
        message_type = self.get_random_message_type()

        message_data = {
            "type": "random_message",
            "message": {
                "id": int(time.time() * 1000),  # タイムスタンプをIDとして使用
                "content": message_content,
                "message_type": message_type,
                "timestamp": datetime.now().isoformat(),
                "color": f"#{random.randint(0, 0xFFFFFF):06x}",  # ランダムな色
            },
        }

        # WebSocketグループに送信
        await channel_layer.group_send("posts_updates", message_data)
        print(f"ランダムメッセージを送信: {message_type} - {message_content}")

    async def start_random_messages(self):
        """ランダムメッセージの定期送信を開始"""
        if self.is_running:
            return

        self.is_running = True
        print("ランダムメッセージ生成を開始しました")

        while self.is_running:
            try:
                # ランダムな間隔（5-20秒）で待機
                wait_time = random.randint(5, 20)
                print(f"次のメッセージまで {wait_time} 秒待機...")

                await asyncio.sleep(wait_time)

                if self.is_running:
                    await self.send_random_message()

            except Exception as e:
                print(f"ランダムメッセージ送信中にエラー: {e}")
                await asyncio.sleep(5)  # エラー時は5秒待機

    def start(self):
        """同期的にタスクを開始"""
        if not self.is_running:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.start_random_messages())
                else:
                    loop.run_until_complete(self.start_random_messages())
            except RuntimeError:
                # 新しいイベントループを作成
                asyncio.run(self.start_random_messages())

    def stop(self):
        """タスクを停止"""
        self.is_running = False
        if self.task:
            self.task.cancel()


# グローバルインスタンス
random_message_generator = RandomMessageGenerator()


def start_random_message_task():
    """ランダムメッセージタスクを開始する関数"""
    try:
        # 非同期でタスクを開始
        import threading

        def run_async_task():
            asyncio.run(random_message_generator.start_random_messages())

        if not random_message_generator.is_running:
            thread = threading.Thread(target=run_async_task, daemon=True)
            thread.start()

    except Exception as e:
        print(f"ランダムメッセージタスク開始中にエラー: {e}")


def stop_random_message_task():
    """ランダムメッセージタスクを停止する関数"""
    random_message_generator.stop()

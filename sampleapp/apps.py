from django.apps import AppConfig


class SampleappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sampleapp"

    def ready(self):
        """アプリケーション起動時の処理"""
        # ランダムメッセージタスクを遅延起動
        # Djangoの起動プロセスが完了してから開始
        import threading
        import time

        def start_background_tasks():
            time.sleep(5)  # Django起動完了まで待機
            try:
                from .tasks import start_random_message_task

                start_random_message_task()
                print("ランダムメッセージタスクを開始しました")
            except Exception as e:
                print(f"ランダムメッセージタスク開始中にエラー: {e}")

        # バックグラウンドスレッドで開始
        thread = threading.Thread(target=start_background_tasks, daemon=True)
        thread.start()

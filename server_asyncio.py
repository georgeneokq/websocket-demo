import asyncio
import websockets
import json

# これまでのアンケート回答を保存するリスト
# 実際の本番環境では、データベースなどに永続化することが推奨されます。
CLIENTS = set() # 接続中のクライアントを管理
ANSWER_HISTORY = [] # アンケート回答履歴

async def register(websocket):
    """新しいクライアントを登録する."""
    CLIENTS.add(websocket)
    print(f"新しいクライアントが接続しました: {websocket.remote_address} (現在の接続数: {len(CLIENTS)})")
    # 新規接続時にこれまでの回答履歴を送信
    if ANSWER_HISTORY:
        await websocket.send(json.dumps({"type": "history", "data": ANSWER_HISTORY}))
    else:
        await websocket.send(json.dumps({"type": "history", "data": [], "message": "まだ回答はありません。"}))

async def unregister(websocket):
    """クライアントの登録を解除する."""
    CLIENTS.remove(websocket)
    print(f"クライアントが切断しました: {websocket.remote_address} (現在の接続数: {len(CLIENTS)})")

async def notify_clients(new_answer=None):
    """全ての接続中のクライアントに新しい回答、または更新を通知する."""
    if CLIENTS: # 接続中のクライアントがいる場合のみ
        if new_answer:
            message = {"type": "new_answer", "data": new_answer}
        else:
            # 全履歴を再度送る場合はこのロジックを調整します
            message = {"type": "history_updated", "data": ANSWER_HISTORY} # 例: 履歴全体を更新通知
        
        # 全クライアントに非同期でメッセージを送信
        await asyncio.gather(*[client.send(json.dumps(message)) for client in CLIENTS])

async def survey_handler(websocket):
    """WebSocket接続を処理し、アンケート回答を受け取る."""
    await register(websocket) # クライアントを登録

    try:
        async for message in websocket:
            print(f"受信メッセージ: {message}")
            try:
                data = json.loads(message)
                if data.get("type") == "survey_response":
                    # 新しい回答を履歴に追加
                    answer = {
                        "name": data.get('name', '未回答'),
                        "destination": data.get('destination', '未回答'),
                        "purpose": data.get('purpose', ['未回答']),
                        "comment": data.get('comment', 'なし')
                    }
                    ANSWER_HISTORY.append(answer)
                    print("\n--- 新しいアンケート回答を受信 ---")
                    print(f"お名前: {answer['name']}")
                    print(f"最も行きたい観光地: {answer['destination']}")
                    print(f"旅行の目的: {', '.join(answer['purpose'])}")
                    print(f"コメント: {answer['comment']}")
                    print("----------------------------------\n")
                    
                    # 回答を受け付けたことをクライアントに送信
                    await websocket.send(json.dumps({"status": "success", "message": "アンケート回答を受け付けました！"}))
                    
                    # 全ての接続中のクライアントに新しい回答を通知
                    await notify_clients(new_answer=answer)

                elif data.get("type") == "request_history":
                    # 履歴要求があった場合に送信
                    await websocket.send(json.dumps({"type": "history", "data": ANSWER_HISTORY}))
                    print(f"クライアント {websocket.remote_address} に履歴を送信しました。")

                else:
                    await websocket.send(json.dumps({"status": "error", "message": "不明なメッセージタイプです。"}))
            except json.JSONDecodeError:
                print(f"無効なJSONメッセージを受信しました: {message}")
                await websocket.send(json.dumps({"status": "error", "message": "無効なJSON形式です。"}))
            except Exception as e:
                print(f"処理中にエラーが発生しました: {e}")
                await websocket.send(json.dumps({"status": "error", "message": f"サーバーエラーが発生しました: {e}"}))

    except websockets.exceptions.ConnectionClosedOK:
        print(f"クライアントが正常に切断しました: {websocket.remote_address}")
    except Exception as e:
        print(f"WebSocketエラー: {e}")
    finally:
        await unregister(websocket) # 接続が閉じたらクライアントの登録を解除

async def main():
    print("WebSocketサーバーを開始します...")
    async with websockets.serve(survey_handler, "localhost", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
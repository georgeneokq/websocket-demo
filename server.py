from websocket_server import WebsocketServer
import json
# import logging # loggingライブラリは不要になります

# これまでのアンケート回答を保存するリスト
ANSWER_HISTORY = []

# --- WebSocketイベントハンドラー関数 ---

def new_client(client, server):
    """新しいクライアントが接続したときに呼び出されます。"""
    print(f"INFO: 新しいクライアントが接続しました: {client['handler'].client_address} (ID: {client['id']})")
    # 新規接続時にこれまでの回答履歴を送信
    if ANSWER_HISTORY:
        server.send_message(client, json.dumps({"type": "history", "data": ANSWER_HISTORY}))
    else:
        server.send_message(client, json.dumps({"type": "history", "data": [], "message": "まだ回答はありません。"}))

def client_left(client, server):
    """クライアントが切断したときに呼び出されます。"""
    print(f"INFO: クライアントが切断しました: {client['handler'].client_address} (ID: {client['id']})")

def message_received(client, server, message):
    """クライアントからメッセージを受信したときに呼び出されます。"""
    print(f"INFO: クライアント {client['id']} からメッセージを受信: {message}")
    try:
        data = json.loads(message)
        if data.get("type") == "survey_response":
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
            server.send_message(client, json.dumps({"status": "success", "message": "アンケート回答を受け付けました！"}))

            # 全ての接続中のクライアントに新しい回答を通知
            server.send_message_to_all(json.dumps({"type": "new_answer", "data": answer}))

        elif data.get("type") == "request_history":
            # 履歴要求があった場合に送信
            server.send_message(client, json.dumps({"type": "history", "data": ANSWER_HISTORY}))
            print(f"INFO: クライアント {client['id']} に履歴を送信しました。")

        else:
            server.send_message(client, json.dumps({"status": "error", "message": "不明なメッセージタイプです。"}))
    except json.JSONDecodeError:
        print(f"ERROR: 無効なJSONメッセージを受信しました: {message}")
        server.send_message(client, json.dumps({"status": "error", "message": "無効なJSON形式です。"}))
    except Exception as e:
        print(f"ERROR: 処理中にエラーが発生しました: {e}")
        server.send_message(client, json.dumps({"status": "error", "message": f"サーバーエラーが発生しました: {e}"}))

# --- メインのサーバー起動部分 ---

if __name__ == "__main__":
    PORT = 8765
    HOST = "localhost" # '0.0.0.0' にすると、どのIPアドレスからの接続も許可されます。

    server = WebsocketServer(host=HOST, port=PORT)

    # 各イベントに関数をバインド
    server.set_fn_new_client(new_client)
    server.set_fn_client_left(client_left)
    server.set_fn_message_received(message_received)

    print(f"INFO: WebSocketサーバーを開始します: ws://{HOST}:{PORT}")
    server.run_forever()
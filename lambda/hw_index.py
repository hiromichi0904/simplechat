# lambda/hw_index.py
import json
import os
import re
import urllib.request
from urllib.error import HTTPError, URLError

# 環境変数から My API のエンドポイントを取得, URLは毎回正しく設定すること
INFERENCE_API_URL = os.environ.get("INFERENCE_API_URL", "https://5379-34-127-70-79.ngrok-free.app/generate")

def lambda_handler(event, context):
    try:
        if not INFERENCE_API_URL:
            raise ValueError("INFERENCE_API_URL 環境変数が設定されていません")

        print("Received event:", json.dumps(event))

        # Cognitoで認証されたユーザー情報を取得
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")

        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])
        messages = conversation_history.copy()

        print("Received message:", message)

        # FastAPIに送信する形式に変換
        request_payload = {
            "prompt": message,
            "max_new_tokens": 512,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9
        }

        # HTTPリクエスト送信
        req = urllib.request.Request(
            INFERENCE_API_URL,
            data=json.dumps(request_payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        # レスポンスを解析
        with urllib.request.urlopen(req) as response:
            response_body = json.loads(response.read().decode())
            print("API Response:", json.dumps(response_body))

        # アシスタントの応答を取得
        assistant_response = response_body.get('generated_text', '')

        # 会話履歴を更新
        conversation_history = body.get('conversationHistory', [])
        conversation_history.append({"role": "user", "content": message})
        conversation_history.append({"role": "assistant", "content": assistant_response})

        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": conversation_history
            })
        }

    except (HTTPError, URLError) as http_err:
        error_message = f"Inference API HTTPError: {http_err.code} - {http_err.read().decode() if hasattr(http_err, 'read') else str(http_err)}"
        print("HTTP error:", error_message)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": error_message
            })
        }

    except Exception as error:
        print("Error:", str(error))
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
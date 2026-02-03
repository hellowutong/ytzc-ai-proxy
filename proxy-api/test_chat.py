#!/usr/bin/env python3
"""测试聊天补全API"""
import httpx

API_URL = "http://localhost:8080/proxy/v1/chat/completions"
PROXY_KEY = "tw-537294261af9b0d492653794"

payload = {
    "model": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
    "messages": [
        {"role": "user", "content": "你好，请介绍一下你自己"}
    ],
    "temperature": 0.7,
    "max_tokens": 1000
}

headers = {
    "Authorization": f"Bearer {PROXY_KEY}",
    "Content-Type": "application/json"
}

response = httpx.post(API_URL, json=payload, headers=headers, timeout=120.0)
print(f"状态码: {response.status_code}")
data = response.json()

# 写入文件避免编码问题
with open("chat_response.json", "w", encoding="utf-8") as f:
    import json
    json.dump(data, f, ensure_ascii=False, indent=2)
print("响应已保存到 chat_response.json")

#!/usr/bin/env python3
"""配置硅基流动DeepSeek提供商"""
import httpx
import json
import secrets

API_URL = "http://localhost:8080/api/v1/providers"

proxy_key = f"tw-{secrets.token_hex(12)}"
print(f"生成的Proxy Key: {proxy_key}")

providers = [
    {
        "type": "deepseek",
        "name": "硅基流动DeepSeek",
        "small_model": {
            "id": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
            "api_key": "sk-dyxgnhjyiwvzxkefgdgvgjcrrbrehagxqmmwtavwsutpndyw",
            "api_base": "https://api.siliconflow.cn/v1",
            "max_tokens": 32768
        },
        "big_model": {
            "id": "deepseek-ai/DeepSeek-V3-0324",
            "api_key": "sk-dyxgnhjyiwvzxkefgdgvgjcrrbrehagxqmmwtavwsutpndyw",
            "api_base": "https://api.siliconflow.cn/v1",
            "max_tokens": 65536
        },
        "proxy_key": proxy_key
    }
]

response = httpx.put(API_URL, json=providers, follow_redirects=True)
print(f"状态码: {response.status_code}")
print(f"响应内容: {response.text}")

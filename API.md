# Kimi & SiliconFlow API 调用指南

本文档总结了 SeedGlow 项目中调用 Moonshot (Kimi) 和 SiliconFlow 模型的完整方法。两者均使用 **OpenAI 兼容的 Chat Completions API**，可直接复用 OpenAI SDK 或原始 HTTP 请求。

---

## 1. 统一协议：OpenAI Chat Completions

Kimi 和 SiliconFlow **都**实现了 OpenAI `/v1/chat/completions` 接口，区别仅在于 Base URL 和模型 ID。

### 请求格式

```
POST {base_url}/chat/completions
Content-Type: application/json
Authorization: Bearer {api_key}
```

```json
{
    "model": "模型ID",
    "messages": [
        {"role": "system", "content": "系统提示词"},
        {"role": "user", "content": "用户消息"}
    ],
    "max_tokens": 1024
}
```

### 响应格式

```json
{
    "choices": [
        {
            "message": {
                "content": "模型的回复文本"
            }
        }
    ],
    "usage": {
        "prompt_tokens": 100,
        "completion_tokens": 50
    }
}
```

---

## 2. 可用模型一览

### Moonshot (Kimi)

| 模型名称 | 模型 ID | Base URL | 输入价格 ($/M tokens) | 输出价格 ($/M tokens) |
|---|---|---|---|---|
| Kimi K2.5 | `kimi-k2.5` | `https://api.moonshot.cn/v1` | 0.6 | 3.0 |
| Kimi K2 | `kimi-k2-0905-preview` | `https://api.moonshot.cn/v1` | 0.6 | 2.5 |

### SiliconFlow

| 模型名称 | 模型 ID | Base URL | 输入价格 ($/M tokens) | 输出价格 ($/M tokens) |
|---|---|---|---|---|
| MiniMax M2.5 | `Pro/MiniMaxAI/MiniMax-M2.5` | `https://api.siliconflow.cn/v1` | 2.1 | 8.4 |
| GLM-4.7 | `Pro/zai-org/GLM-4.7` | `https://api.siliconflow.cn/v1` | 4.0 | 16.0 |
| DeepSeek V3.2 | `Pro/deepseek-ai/DeepSeek-V3.2` | `https://api.siliconflow.cn/v1` | 2.0 | 3.0 |
| DS V3.1 Terminus | `Pro/deepseek-ai/DeepSeek-V3.1-Terminus` | `https://api.siliconflow.cn/v1` | 4.0 | 12.0 |
| Step 3.5 Flash | `stepfun-ai/Step-3.5-Flash` | `https://api.siliconflow.cn/v1` | 0.7 | 2.1 |
| GLM-5 | `Pro/zai-org/GLM-5` | `https://api.siliconflow.cn/v1` | 4.0 | 22.0 |

> **注意**：SiliconFlow 的模型 ID 包含路径前缀（如 `Pro/`），这不是笔误，必须完整传入。

---

## 3. Python 实现

### 3.1 使用 `requests` 库（项目实际使用方式）

```python
import requests
import time

class OpenAICompatibleClient:
    """适用于 Kimi 和 SiliconFlow 的统一客户端。"""

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    def complete(
        self,
        system: str,
        user_message: str,
        *,
        max_tokens: int = 1024,
        temperature: float | None = None,
    ) -> dict:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
            "max_tokens": max_tokens,
        }
        # 重要：Kimi K2.5 等推理模型会拒绝 temperature != 1 的请求
        # 仅在明确需要时传入 temperature
        if temperature is not None and temperature != 0.0:
            payload["temperature"] = temperature

        # 带重试的请求（处理 429 限流和 5xx 服务器错误）
        retryable_codes = {429, 502, 503, 504}
        max_retries = 3

        for attempt in range(max_retries):
            try:
                resp = self._session.post(
                    f"{self._base_url}/chat/completions",
                    json=payload,
                    timeout=180,  # 3分钟超时（LLM 响应可能较慢）
                )
            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    raise
                wait = 5 * 2 ** attempt  # 5s, 10s, 20s
                time.sleep(wait)
                continue

            if resp.status_code in retryable_codes:
                if attempt == max_retries - 1:
                    resp.raise_for_status()
                # 优先使用服务器返回的 Retry-After
                retry_after = resp.headers.get("Retry-After")
                wait = float(retry_after) if retry_after else 5 * 2 ** attempt
                time.sleep(wait)
                continue

            resp.raise_for_status()
            data = resp.json()
            return {
                "text": data["choices"][0]["message"]["content"] or "",
                "input_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                "output_tokens": data.get("usage", {}).get("completion_tokens", 0),
            }

        raise RuntimeError("Max retries exceeded")
```

### 3.2 使用 OpenAI Python SDK

```python
from openai import OpenAI

# ── Kimi ──
kimi_client = OpenAI(
    base_url="https://api.moonshot.cn/v1",
    api_key="你的 Moonshot API Key",
)

response = kimi_client.chat.completions.create(
    model="kimi-k2.5",
    messages=[
        {"role": "system", "content": "你是一个有帮助的助手。"},
        {"role": "user", "content": "你好"},
    ],
    max_tokens=1024,
    # 不要传 temperature=0，Kimi K2.5 推理模型会报错
)
print(response.choices[0].message.content)
print(f"输入 tokens: {response.usage.prompt_tokens}")
print(f"输出 tokens: {response.usage.completion_tokens}")

# ── SiliconFlow ──
sf_client = OpenAI(
    base_url="https://api.siliconflow.cn/v1",
    api_key="你的 SiliconFlow API Key",
)

response = sf_client.chat.completions.create(
    model="Pro/deepseek-ai/DeepSeek-V3.2",  # 注意完整路径
    messages=[
        {"role": "system", "content": "你是一个有帮助的助手。"},
        {"role": "user", "content": "你好"},
    ],
    max_tokens=1024,
    temperature=0.7,
)
print(response.choices[0].message.content)
```

### 3.3 使用 curl

```bash
# Kimi K2.5
curl -X POST https://api.moonshot.cn/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $MOONSHOT_API_KEY" \
  -d '{
    "model": "kimi-k2.5",
    "messages": [
      {"role": "system", "content": "你是一个有帮助的助手。"},
      {"role": "user", "content": "你好"}
    ],
    "max_tokens": 1024
  }'

# SiliconFlow DeepSeek V3.2
curl -X POST https://api.siliconflow.cn/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SILICONFLOW_API_KEY" \
  -d '{
    "model": "Pro/deepseek-ai/DeepSeek-V3.2",
    "messages": [
      {"role": "system", "content": "你是一个有帮助的助手。"},
      {"role": "user", "content": "你好"}
    ],
    "max_tokens": 1024,
    "temperature": 0.7
  }'
```

---

## 4. 关键注意事项

### 4.1 Temperature 处理（重要）

```
Kimi K2.5 是推理模型（reasoning model），会拒绝 temperature != 1 的请求。
```

**最佳实践**：对于 Kimi K2.5，**不要在请求中传入 `temperature` 字段**（让服务器使用默认值）。仅在需要非零温度且确认模型支持时才传入。

项目中的处理方式：
```python
# 仅当 temperature 不为 0 时才加入 payload
if temperature != 0.0:
    payload["temperature"] = temperature
```

### 4.2 重试策略

| 状态码 | 含义 | 处理方式 |
|---|---|---|
| 429 | 请求限流 | 指数退避重试，优先使用 `Retry-After` 头 |
| 502/503/504 | 服务器错误 | 指数退避重试（5s → 10s → 20s） |
| 请求超时 | 网络/服务端慢 | 指数退避重试，timeout 设为 180s |

最多重试 3 次。

### 4.3 推理模型的 `<think>` 标签

部分推理模型（如 Kimi K2.5）会在响应中包含思考过程：

```
<think>
让我分析一下这个问题...
</think>

实际回复内容
```

**处理方式**：用正则去除 `<think>` 块：
```python
import re
text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
```

### 4.4 Markdown 代码围栏

LLM 返回 JSON 时可能会包裹在 markdown 代码围栏中：
````
```json
{"key": "value"}
```
````

**处理方式**：
```python
text = re.sub(r"```(?:json)?\s*", "", text).strip()
```

### 4.5 超时设置

推荐 `timeout=180`（3 分钟）。LLM API 响应可能较慢，尤其是长文本生成时。

---

## 5. 认证方式

两个平台都使用 **Bearer Token** 认证：

| 平台 | 获取 API Key | Header |
|---|---|---|
| Moonshot (Kimi) | [platform.moonshot.cn](https://platform.moonshot.cn) | `Authorization: Bearer {key}` |
| SiliconFlow | [cloud.siliconflow.cn](https://cloud.siliconflow.cn) | `Authorization: Bearer {key}` |

---

## 6. 快速开始模板

以下是一个最精简的、可直接运行的调用模板：

```python
"""最小化 Kimi / SiliconFlow 调用模板。"""

from openai import OpenAI


def call_llm(
    base_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_message: str,
    max_tokens: int = 2048,
) -> str:
    """调用 Kimi 或 SiliconFlow 模型，返回文本。"""
    client = OpenAI(base_url=base_url, api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        max_tokens=max_tokens,
        # 不传 temperature（兼容推理模型）
    )
    return response.choices[0].message.content


# ── 使用示例 ──

# Kimi K2.5
result = call_llm(
    base_url="https://api.moonshot.cn/v1",
    api_key="sk-...",
    model="kimi-k2.5",
    system_prompt="你是一个代码审查专家。",
    user_message="请审查以下代码...",
)

# SiliconFlow DeepSeek V3.2（性价比最高）
result = call_llm(
    base_url="https://api.siliconflow.cn/v1",
    api_key="sk-...",
    model="Pro/deepseek-ai/DeepSeek-V3.2",
    system_prompt="你是一个代码审查专家。",
    user_message="请审查以下代码...",
)
```

---


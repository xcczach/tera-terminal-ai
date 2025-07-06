# Common LLM Sources

Below are some publicly available endpoints compatible with the OpenAI API. All information may change at any time—please refer to the official pages for the latest details.

> ⚠️ Always read and comply with each provider's terms of service. Quotas or free tiers can change without notice.

---

## 1. Aliyun Bailian Platform – Qwen Models

| Item | Value |
| ---- | ----- |
| Base URL | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| How to get API key | Log in to [Aliyun Bailian Console](https://bailian.console.aliyun.com/?tab=model#/api-key) and create a key. |
| Model list | Check [Model Market](https://bailian.console.aliyun.com/?tab=model#/model-market) and look for models with free quota (e.g. `qwen-turbo`, `qwen-plus`). |

---

## 2. ChatAnywhere

| Item | Value |
| ---- | ----- |
| Base URL | `https://api.chatanywhere.tech/v1` |
| How to get API key | Follow instructions in their GitHub project: <https://github.com/chatanywhere/GPT_API_free#how-to-use> |
| Free models (2025-07-06) | `gpt-4o` / `gpt-4.1` (5 requests/day), `deepseek-r1`, `deepseek-v3` (30 req/day), `gpt-4o-mini`, `gpt-3.5-turbo`, `gpt-4.1-mini`, `gpt-4.1-nano` (200 req/day) |

---

## 3. Any OpenAI-compatible Endpoint

If you have a self-hosted model or another service that implements the OpenAI Chat Completion API (e.g. OpenRouter, OpenAI itself, local deployments), simply supply its `base_url` and `api_key` when running:

```bash
tera source add
```

Then paste the URL, key, and model name when prompted. 
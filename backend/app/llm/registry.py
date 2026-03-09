"""Registry of supported LLM providers with their configuration details."""

SUPPORTED_PROVIDERS: dict[str, dict] = {
    "openai": {
        "display_name": "OpenAI",
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
        ],
        "docs_url": "https://platform.openai.com/api-keys",
        "litellm_prefix": "",
        "env_key": "OPENAI_API_KEY",
    },
    "anthropic": {
        "display_name": "Anthropic",
        "models": [
            "claude-sonnet-4-20250514",
            "claude-haiku-35-20241022",
            "claude-3-5-sonnet-20241022",
        ],
        "docs_url": "https://console.anthropic.com/settings/keys",
        "litellm_prefix": "anthropic/",
        "env_key": "ANTHROPIC_API_KEY",
    },
    "google": {
        "display_name": "Google Gemini",
        "models": [
            "gemini/gemini-2.0-flash",
            "gemini/gemini-2.0-flash-lite",
            "gemini/gemini-1.5-pro",
            "gemini/gemini-1.5-flash",
        ],
        "docs_url": "https://aistudio.google.com/apikey",
        "litellm_prefix": "gemini/",
        "env_key": "GEMINI_API_KEY",
    },
    "deepseek": {
        "display_name": "DeepSeek",
        "models": [
            "deepseek/deepseek-chat",
            "deepseek/deepseek-reasoner",
        ],
        "docs_url": "https://platform.deepseek.com/api_keys",
        "litellm_prefix": "deepseek/",
        "env_key": "DEEPSEEK_API_KEY",
    },
    "moonshot": {
        "display_name": "Moonshot (Kimi)",
        "models": [
            "kimi-k2.5",
            "kimi-k2-0905-preview",
        ],
        "docs_url": "https://platform.moonshot.cn",
        "litellm_prefix": "openai/",
        "env_key": "MOONSHOT_API_KEY",
        "api_base": "https://api.moonshot.cn/v1",
        # Kimi K2.5 is a reasoning model that rejects temperature != 1
        "skip_temperature_models": ["kimi-k2.5"],
    },
    "siliconflow": {
        "display_name": "SiliconFlow",
        "models": [
            "Pro/deepseek-ai/DeepSeek-V3.2",
            "Pro/MiniMaxAI/MiniMax-M2.5",
            "Pro/zai-org/GLM-4.7",
            "Pro/deepseek-ai/DeepSeek-V3.1-Terminus",
            "stepfun-ai/Step-3.5-Flash",
            "Pro/zai-org/GLM-5",
        ],
        "docs_url": "https://cloud.siliconflow.cn",
        "litellm_prefix": "openai/",
        "env_key": "SILICONFLOW_API_KEY",
        "api_base": "https://api.siliconflow.cn/v1",
    },
}

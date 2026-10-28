# providers/: the only place that talks to an LLM

| File | What it does |
|---|---|
| `base.py` | The `ChatModel` and `Embedder` interfaces, `ProviderError`, and `with_retry` |
| `gemini.py` | Google Gemini (default) |
| `openai.py` | OpenAI (`LLM_PROVIDER=openai`) |
| `__init__.py` | `get_chat_model()` / `get_embedder()` pick the provider; `use_providers()` swaps in your own |

Add a provider: see [docs/EXTENDING.md](../../../docs/EXTENDING.md#add-an-llm-provider).

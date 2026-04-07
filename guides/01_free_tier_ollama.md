# Running with Ollama (Free, Local LLMs)

Every stage can run with local models via Ollama — zero API spend required.

## Install Ollama

Visit [ollama.com](https://ollama.com) and install for your platform.

## Pull a Model

```bash
ollama pull llama3.1        # Recommended for most stages
ollama pull llama3.1:8b     # Faster, lighter
ollama pull llama3.1:70b    # Better quality for multi-agent stages
```

## Configure .env

```bash
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
```

## Model Recommendations by Stage

| Stage | Min Model | Recommended |
|-------|-----------|-------------|
| 1 — Awareness | llama3.1:8b | llama3.1 |
| 2 — Consideration | llama3.1 | llama3.1:70b |
| 3 — Decision | llama3.1:8b | llama3.1 |
| 4 — Onboarding | llama3.1 | llama3.1:70b |
| 5 — Retention | llama3.1 | llama3.1:70b |
| 6 — Advocacy | llama3.1:8b | llama3.1 |
| Capstone | llama3.1 | llama3.1:70b |

## Notes

- Multi-agent stages (2, 4, 5) benefit from larger models
- Tool calling quality varies — GPT-4.1 and Claude produce the best structured output
- Use 8b models for fast iteration during development

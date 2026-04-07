# Running with Ollama (Free, Local LLMs)

Every project in this book can run with local models via Ollama — zero API spend required.

## Step 1: Install Ollama

Visit [ollama.com](https://ollama.com) and install for your platform.

## Step 2: Pull a Model

```bash
# Recommended for most projects
ollama pull llama3.1

# Smaller model for faster iteration
ollama pull llama3.1:8b

# Larger model for better quality
ollama pull llama3.1:70b
```

## Step 3: Configure Your .env

```bash
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
```

## Step 4: Run Any Project

All projects use the OpenAI-compatible client, so they automatically work with Ollama's OpenAI-compatible endpoint.

```bash
cd 2_openai_sdk/project1_journey_twin
python app.py
```

## Model Recommendations by Project

| Project | Min Model | Recommended |
|---------|-----------|-------------|
| 1–2 (OpenAI SDK) | llama3.1:8b | llama3.1 |
| 3–4 (CrewAI) | llama3.1 | llama3.1:70b |
| 5–6 (LangGraph) | llama3.1:8b | llama3.1 |
| 7 (AutoGen) | llama3.1 | llama3.1:70b |
| 8 (Capstone) | llama3.1 | llama3.1:70b |

## Notes

- CrewAI and AutoGen multi-agent projects benefit from larger models (70b+)
- Tool calling quality varies by model — GPT-4.1 and Claude produce the best structured output
- If Ollama responses are slow, try the 8b variant for faster iteration

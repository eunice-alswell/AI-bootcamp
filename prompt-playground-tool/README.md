# Prompt Playground Tool

An interactive CLI prompt tool for experimenting with different AI models and prompt styles using the **Groq API** - my first LLM prayground tool. This tool allows you to ask questions and receive responses in different "styles" (basic, teacher, reasoning) from various open-source LLMs.

## Features

- 🎯 **Multiple Prompt Styles**: Choose between basic, teacher, and reasoning styles to shape model responses
- 🤖 **Multiple AI Models**: Access to Groq-hosted open-source models (Qwen, GPT, Llama)
- 🚀 **Streaming Support**: Stream responses in real-time for faster feedback
- ⚙️ **Customizable Parameters**: Adjust temperature and other generation parameters
- 🔌 **Easy API Integration**: Simple Python interface to Groq API

## Available Prompt Styles

| Style | Description |
|-------|-------------|
| **basic** | Helpful assistant that answers clearly and directly |
| **teacher** | Expert teacher who explains concepts simply with examples |
| **reasoning** | Careful reasoner who thinks step-by-step before answering |

## Available AI Models

The following Groq-hosted models are currently available:

- `qwen/qwen3-32b` – Qwen 3 32B model
- `openai/gpt--oss-20b` – OpenAI GPT OSS 20B model
- `llama-3.3-70b-versatile` – Llama 3.3 70B Versatile model

> **Note**: The `gamma2-9b-it` model has been removed due to access restrictions with the Groq API.

## Setup

### Prerequisites

- Python 3.9 or higher
- A Groq API key (get one at [console.groq.com](https://console.groq.com))

### Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone https://github.com/eunice-alswell/AI-bootcamp.git
   cd AI-bootcamp/prompt-playground-tool
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .pgtenv
   ```

3. **Activate the virtual environment**:
   - **Windows (PowerShell)**:
     ```powershell
     .\.pgtenv\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt)**:
     ```cmd
     .pgtenv\Scripts\activate.bat
     ```
   - **macOS/Linux**:
     ```bash
     source .pgtenv/bin/activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**:
   - Copy the example environment file:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your Groq API key:
     ```
     groq_api_key = "your_actual_groq_api_key_here"
     ```

## Usage

### Run the Interactive CLI

```bash
python main.py
```

### Example Session

```
Enter your question: What is machine learning?

--- Style: basic ---
Machine learning is a type of artificial intelligence that enables computers to learn from data without being explicitly programmed...

--- Style: teacher ---
Machine learning is like teaching a computer to recognize patterns, much like how a student learns...

--- Style: reasoning ---
Let me think about this step by step:
1. First, consider what learning means...
```

## Project Structure

```
prompt-playground-tool/
├── main.py                    # Main CLI application
├── prompt_styles.py           # System prompts for different styles
├── available_ai_models.py     # List of available Groq models
├── requirements.txt           # Python dependencies
├── .env.example              # Example environment variables
├── .pgtenv/                  # Virtual environment (auto-created)
└── README.md                 # This file
```

## Dependencies

- **groq** – Official Groq API Python client
- **python-dotenv** – Load environment variables from `.env` file
- **fastapi** – (Optional) For future web API extensions
- **uvicorn** – (Optional) ASGI server for FastAPI

See `requirements.txt` for exact versions.

## Troubleshooting

### Import Error: "Unable to import 'groq'"

**Problem**: `ModuleNotFoundError: No module named 'groq'`

**Solutions**:
1. Verify the virtual environment is activated:
   ```bash
   # Check if prompt appears with (.pgtenv) prefix
   # If not, activate:
   .\.pgtenv\Scripts\Activate.ps1  # Windows
   source .pgtenv/bin/activate     # macOS/Linux
   ```

2. Reinstall dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. In VS Code, select the correct Python interpreter:
   - Open Command Palette: `Ctrl+Shift+P`
   - Search: `Python: Select Interpreter`
   - Choose: `.\.pgtenv\Scripts\python.exe`

### Model Not Found Error: 404 - "The model does not exist or you do not have access to it"

**Problem**: Error like `'gamma2-9b-it' does not exist or you do not have access to it`

**Reason**: The model is either outdated, deprecated, or your API key doesn't have access.

**Solutions**:
1. **Use a verified model** from [`available_ai_models.py`](available_ai_models.py):
   - `qwen/qwen3-32b`
   - `openai/gpt--oss-20b`
   - `llama-3.3-70b-versatile`

2. **Check your Groq API key**:
   - Verify it's set correctly in `.env`
   - Log in to [console.groq.com](https://console.groq.com) to confirm API key and available models

3. **Update model list**:
   - Check the [Groq documentation](https://console.groq.com/docs/models) for current available models
   - Update `available_ai_models.py` with verified models

### Groq API Key Error

**Problem**: `Error code: 401 - Invalid API Key`

**Solution**:
1. Verify your API key is correct in `.env`
2. Get a new key from [console.groq.com/keys](https://console.groq.com/keys)
3. Ensure there are no extra spaces or quotes in the `.env` file

## Future Enhancements

- [ ] Web UI with FastAPI/Uvicorn
- [ ] Model benchmarking and comparison
- [ ] Response caching
- [ ] Temperature and parameter tuning UI
- [ ] Additional prompt styles (creative, summarizer, translator, etc.)

## Contributing

Contributions are welcome! Please feel free to:
- Report bugs or issues
- Suggest new prompt styles or features
- Update model lists as Groq adds/removes models
- Improve documentation

## License

This project is part of the AI Bootcamp. See the parent repository for license details.

## Resources

- [Groq Console](https://console.groq.com)
- [Groq API Documentation](https://console.groq.com/docs/api)
- [Groq Python SDK](https://github.com/groq/groq-python)

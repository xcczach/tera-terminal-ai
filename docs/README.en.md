<p align="right">
  <a href="../README.md">中文</a>
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)

# Tera Terminal AI

Tera Terminal AI is a lightweight terminal chat agent supporting multiple **LLM endpoints**, multiple **role presets**, **code execution feedback**, and optional **long-term memory**, focusing on minimalism and cross-platform use.

> **Supported OS:** Windows / macOS / Linux (Python 3.9+ required)

## Download & Install (Python 3.9+)

```bash
# Clone repository and enter
git clone https://github.com/yourname/tera-terminal-ai.git
cd tera-terminal-ai

# Install in editable mode (allows local tweaks)
pip install -e .

# Run
tera <command>
```

## Quick Start

Add at least one LLM endpoint before chatting. For available endpoints, see [Common LLM Sources](./llm_sources.en.md).

```bash
# 1. Add an LLM source (required on first use)
tera source add   # The name is only an identifier used when switching endpoints later

# 2. Start chatting
tera
```

(Optional) The memory feature uses a local embedding model (~hundreds MB). It is disabled by default and must be enabled manually. To speed up inference with CUDA, install the appropriate `torch` build (see the [PyTorch website](https://pytorch.org/get-started/locally/)).

```bash
pip install -e .[memory]
tera memory on
```

More examples:

```bash
# List all commands
tera --help

# Switch current endpoint
tera source use my-openai

# Add and switch role
tera character add
tera character use anime-girl

# Toggle long-term memory
tera memory on
tera memory off
```

## Features

- 🛰️ **Multiple endpoints** – store several OpenAI-compatible endpoints and switch with one command.  
- 🧑‍🎤 **Role system** – save different prompts for various scenarios and switch personas instantly.  
- 💻 **Code execution feedback** – execute Python / Shell code blocks in AI replies locally and send the output back to the model.  
- 💾 **Long-term memory** (optional) – local vector store powered by Sentence-Transformer + Faiss to retrieve personal preferences.  
- 🖥️ **Cross-platform CLI** – minimal dependencies, pure Python + Click.

## License

MIT – see [LICENSE](../LICENSE). 
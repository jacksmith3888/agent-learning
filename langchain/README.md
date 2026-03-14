# 🔗 LangChain Essentials Python


## 🚀 Setup 

### Prerequisites

- Ensure you're using Python 3.11 - 3.13.
- [uv](https://docs.astral.sh/uv/) package manager or [pip](https://pypi.org/project/pip/)
- 本地已安装并启动 Ollama
- 已拉取可用模型，例如 `qwen2.5:7b`
- Node.js and npx (required for MCP server in notebook 3):
```bash
# Install Node.js (includes npx)
# On macOS with Homebrew:
brew install node

# On Ubuntu/Debian:
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installation:
node --version
npx --version
```

### Installation

在仓库根目录执行。

```bash
# 进入当前项目根目录
cd /Users/jason/Documents/github/agent-learning
```

Make a copy of example.env

```bash
# Create .env file
cp example.env .env
```

将本地 Ollama 配置写入 `.env`。

```bash
# 本地 Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b

```

Make a virtual environment and install dependencies
```bash
# 在项目根目录创建虚拟环境并安装依赖
uv sync
```

Run notebooks

```bash
# 在项目根目录启动 Jupyter
uv run jupyter lab
```

### 使用说明

- 当前 notebook 已统一切换为本地 `Ollama`，默认模型为 `qwen2.5:7b`。
- 运行前请先确认 `ollama serve` 已启动，并已执行 `ollama pull qwen2.5:7b`。
<img width="600" alt="Screenshot 2025-10-16 at 8 28 03 AM" src="https://github.com/user-attachments/assets/e39b8364-c3e3-4c75-a287-d9d4685caad5" />
<img width="600" alt="Screenshot 2025-10-16 at 8 29 57 AM" src="https://github.com/user-attachments/assets/2e916b2d-e3b0-4c59-a178-c5818604b8fe" />

# 📚 Lessons
This repository contains nine short notebooks that serve as brief introductions to many of the most-used features in LangChain, starting with the new **Create Agent**.

---

### `L1_fast_agent.ipynb` - 🤖 Create Agent 🤖
- In this notebook, you will use LangChain’s `create_agent` to build an SQL agent in just a few lines of code.  
- It demonstrates how quick and easy it is to build a powerful agent. You can easily take this agent and apply it to your own project. 

---

### `L2-7.ipynb` - 🧱 Building Blocks 🧱
In Lessons 2–7, you will learn how to use some of the fundamental building blocks in LangChain. These lessons explain and complement `create_agent`, and you’ll find them useful when creating your own agents. Each lesson is concise and focused.

- **L2_messages.ipynb**: Learn how messages convey information between agent components.  
- **L3_streaming.ipynb**: Learn how to reduce user-perceived latency using streaming.  
- **L4_tools.ipynb**: Learn basic tool use to enhance your model with custom or prebuilt tools.  
- **L5_tools_with_mcp.ipynb**: Learn to use the LangChain MCP adapter to access the world of MCP tools.  
- **L6_memory.ipynb**: Learn how to give your agent the ability to maintain state between invocations.  
- **L7_structuredOutput.ipynb**: Learn how to produce structured output from your agent.  

---

### `L8-9.ipynb` - 🪛 Customize Your Agent 🤖
Lessons 2–7 covered out-of-the-box features. However, `create_agent` also supports both prebuilt and user-defined customization through **Middleware**. This section describes middleware and includes two lessons highlighting specific use cases.

- **L8_dynamic.ipynb**: Learn how to dynamically modify the agent’s system prompt to react to changing contexts.  
- **L9_HITL.ipynb**: Learn how to use Interrupts to enable Human-in-the-Loop interactions.

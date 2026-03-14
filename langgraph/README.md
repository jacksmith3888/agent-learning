## 🦜
# __LangGraph Essentials__

This course will cover an introduction to key LangGraph concepts: State, Nodes, Edges, Memory, and Interrupts. It consists of five core labs and one cumulative tutorial demonstrating how to build a production-style email support workflow.

## 🚀 Setup 

### Prerequisites

- Ensure you're using Python 3.11 - 3.13.
- [uv](https://docs.astral.sh/uv/) package manager or [pip](https://pypi.org/project/pip/)
- 本地已安装并启动 Ollama
- 已拉取可用模型，例如 `qwen2.5:7b`

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

Make a virtual environment and install dependancies
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
<img width="1196" height="693" alt="Screenshot 2025-10-16 at 8 28 03 AM" src="https://github.com/user-attachments/assets/e39b8364-c3e3-4c75-a287-d9d4685caad5" />
<img width="1196" height="468" alt="Screenshot 2025-10-16 at 8 29 57 AM" src="https://github.com/user-attachments/assets/2e916b2d-e3b0-4c59-a178-c5818604b8fe" />



## 📚 Tutorial Overview

This repository contains notebooks for Labs 1-5, and an additional notebook showcasing an end-to-end email agent. These labs cover the foundations of LangGraph that will enable you to build any workflow or agent.

### `L1-5.ipynb` - LangGraph Essentials
- You will use all the components of LangGraph
    - State and Nodes
    - Edges
        - Parallel
        - Conditional
    - Memory
    - Interrupts/ Human-In-The-Loop  

### `EmailAgent.ipynb` - Build A Workflow
Learn to implement structured workflow to process customer emails. This notebook utilizes all of the building blocks from the first notebook in an example application.:
- Task tracking with status management (pending/in_progress/completed)  

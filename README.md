# agent-learning

这是一个按 `lecture01` 到 `lecture84` 组织的 Agent 学习与实作仓库。
目标是通过可运行脚本、测试和每周总结，系统化推进 Agent 工程能力。

## 项目结构

- `lectures/lectureXX/`：每天/每讲的代码产出（脚本、测试、草稿）
- `docs/weekly/`：周总结
- `docs/comparisons/`：框架对比记录（如 LangChain vs Semantic Kernel）
- `shared/`：跨 lecture 复用代码
- `AGENT_LEARNING.md`：完整学习计划与执行细则

## 快速开始

```bash
# 安装依赖（若本地尚未安装）
uv sync

# 运行某个 lecture 的脚本
./run lecture01

# 运行某个 lecture 的测试
./test lecture19

# 等价 make 用法
make run lecture01
make test lecture19
```

## 课程资料来源

本仓库的学习路径由以下公开资料整理而成，代码与练习基于这些资料进行二次实践。

### 1) LangChain / LangGraph 官方学习线（主线）

- LangChain Academy: LangChain Essentials (Python)
  - https://academy.langchain.com/courses/langchain-essentials-python
- LangChain Academy: Intro to LangGraph
  - https://academy.langchain.com/courses/intro-to-langgraph
- LangChain Academy: Deep Research with LangGraph
  - https://academy.langchain.com/courses/deep-research-with-langgraph
- LangChain Academy: Deep Agents with LangGraph
  - https://academy.langchain.com/courses/deep-agents-with-langgraph
- LangChain 官方文档
  - Overview: https://docs.langchain.com/oss/python/langchain/overview
  - Retrieval: https://docs.langchain.com/oss/python/langchain/retrieval
  - Multi-Agent: https://docs.langchain.com/oss/python/langchain/multi-agent
  - Supervisor: https://docs.langchain.com/oss/python/langchain/supervisor

### 2) LearnGraph 实战参考

- LearnGraph 1.X 系列（按课程计划分段引用）
  - 示例入口：
    - Chain: https://www.learngraph.online/LearnGraph%201.X/module-2-agent-chain-router/2.2%20Chain.html
    - Memory: https://www.learngraph.online/LearnGraph%201.X/module-2-agent-chain-router/2.5%20Memory.html
    - Multi-Agent Collaboration:
      https://www.learngraph.online/LearnGraph%201.X/module-12-multi-agent-workflows/12.4%20Multi-Agent%20Collaboration.html

### 3) 中文与通用补充资料

- Datawhale Happy-LLM（章节化配套阅读）
  - https://github.com/datawhalechina/happy-llm
- Hugging Face Agents Course
  - Unit1: https://huggingface.co/learn/agents-course/unit1/introduction
  - Unit3: https://huggingface.co/learn/agents-course/unit3/introduction

### 4) RAG / 评测 / 工具链补充

- LlamaIndex 文档（Rerank 等主题）
  - https://docs.llamaindex.ai/
- LangSmith 文档（追踪与评测）
  - https://docs.smith.langchain.com/

### 5) 对照框架来源

- Semantic Kernel 官方文档（用于与 LangChain/LangGraph 对照学习）
  - https://learn.microsoft.com/en-us/semantic-kernel/overview/

## 来源使用说明

- 本仓库以“学习与复现”为目的，对公开资料进行路线整合与代码化练习。
- 各外部资料的版权归原作者/原平台所有。
- 若你在本仓库中继续扩展某讲内容，建议在对应 `lectures/lectureXX/README.md` 里补充该讲具体参考链接，便于追溯。

## 备注

最新、最完整的学习任务拆解与周计划，请以 `AGENT_LEARNING.md` 为准。

## License

本项目使用 `MIT` 许可证，详见 `LICENSE`。

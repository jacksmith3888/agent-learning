# Agent 学习计划（12周 / D1-D84 / 官方资料优先版）

更新时间：2026-03-20

适用背景：化学专利分析 Agent 项目

学习节奏：

- 工作日：30-60 分钟
- 周末：120 分钟

---

## 0. 先回答你的核心问题：四类知识是否被上述教程覆盖？

### Prompt 设计与约束输出

- 结论：**覆盖较好**
- 在哪些教程：
  - [LangChain Academy - LangChain Essentials](https://academy.langchain.com/courses/langchain-essentials-python)
  - [LangChain Structured Output](https://docs.langchain.com/oss/python/langchain/structured-output)
  - [HF Agents Course Unit1](https://huggingface.co/learn/agents-course/en/unit1/introduction)

### RAG（切分、召回、重排、引用）

- 结论：**覆盖较好，但需要把“基础 RAG”与“Agentic RAG”拆开学**
- 在哪些教程：
  - [HF Agents Course Unit3 - Agentic RAG](https://huggingface.co/learn/agents-course/en/unit3/agentic-rag/introduction)
  - [LangChain Retrieval](https://docs.langchain.com/oss/python/langchain/retrieval)
  - [Build a RAG agent with LangChain](https://docs.langchain.com/oss/python/langchain/rag)
- 缺口补充：
  - [Build a custom RAG agent with LangGraph](https://docs.langchain.com/oss/python/langgraph/agentic-rag)
  - [Build a semantic search engine with LangChain](https://docs.langchain.com/oss/python/langchain/knowledge-base)
  - [LlamaIndex Rerank](https://docs.llamaindex.ai/en/stable/module_guides/querying/node_postprocessors/node_postprocessors/)
  - [LlamaIndex Citation Query Engine](https://docs.llamaindex.ai/en/stable/examples/query_engine/citation_query_engine/)

### Memory（短期摘要、长期记忆、用户画像）

- 结论：**覆盖较好，但工程细节需补**
- 在哪些教程：
  - [LangChain Academy - Introduction to LangGraph](https://academy.langchain.com/courses/intro-to-langgraph)
  - [LangGraph Memory Overview](https://docs.langchain.com/oss/python/langgraph/memory)
  - [LangGraph Add Memory Guide](https://docs.langchain.com/oss/python/langgraph/add-memory)
- 缺口补充：
  - [LangGraph Overview](https://docs.langchain.com/oss/python/langgraph/overview)
  - [Introduction to Agent Observability & Evaluations](https://academy.langchain.com/courses/intro-to-langsmith)

### 多 Agent 协作（Supervisor、Planner-Worker）

- 结论：**覆盖较好**
- 在哪些教程：
  - [LangChain Academy - Deep Research with LangGraph](https://academy.langchain.com/courses/deep-research-with-langgraph)
  - [LangChain Academy - Deep Agents](https://academy.langchain.com/courses/deep-agents-with-langgraph)
  - [LangChain Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)
  - [LangChain Subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents)
- 缺口补充：
  - [Build a personal assistant with subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents-personal-assistant)
  - [LangGraph Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)

### 补充：Semantic Kernel（对照学习）

- 结论：**主线用 LangChain/LangGraph，Semantic Kernel 作为对照框架学习**
- 说明：Semantic Kernel 是微软开源的 AI 编排框架，与 LangChain 定位相似但设计理念不同。通过对照学习可以加深对 Agent 编排模式的理解。
- 学习时机：第 3 周末（D21）和第 8 周（D55）各安排 1 次对照实验
- 参考文档：
  - [Semantic Kernel Python 官方文档](https://learn.microsoft.com/en-us/semantic-kernel/overview/)
  - [Semantic Kernel GitHub](https://github.com/microsoft/semantic-kernel)
  - [Semantic Kernel Concepts](https://learn.microsoft.com/en-us/semantic-kernel/concepts/)

---

## 1. 教程索引（后续 D1-D84 都会引用）

### Hugging Face Agents Course

- [Unit0](https://huggingface.co/learn/agents-course/en/unit0/introduction)
- [Unit1](https://huggingface.co/learn/agents-course/en/unit1/introduction)
- [Unit2](https://huggingface.co/learn/agents-course/en/unit2/introduction)
- [Unit2.3 - LangGraph](https://huggingface.co/learn/agents-course/en/unit2/langgraph/introduction)
- [Unit3 - Agentic RAG](https://huggingface.co/learn/agents-course/en/unit3/agentic-rag/introduction)
- [Bonus Unit1](https://huggingface.co/learn/agents-course/en/bonus-unit1/introduction)
- [Unit4 - Final Project](https://huggingface.co/learn/agents-course/en/unit4/introduction)

### Happy-LLM

- [Chapter1](https://github.com/datawhalechina/happy-llm/tree/main/docs/chapter1)
- [Chapter2](https://github.com/datawhalechina/happy-llm/tree/main/docs/chapter2)
- [Chapter3](https://github.com/datawhalechina/happy-llm/tree/main/docs/chapter3)
- [Chapter4](https://github.com/datawhalechina/happy-llm/tree/main/docs/chapter4)
- [Chapter5](https://github.com/datawhalechina/happy-llm/tree/main/docs/chapter5)
- [Chapter7](https://github.com/datawhalechina/happy-llm/tree/main/docs/chapter7)
- [Chapter8](https://github.com/datawhalechina/happy-llm/tree/main/docs/chapter8)

### LangChain Academy

**Quickstart（快速入门）**:

- [LangChain Essentials - Python](https://academy.langchain.com/courses/langchain-essentials-python) — `create_agent`、messages、tools、MCP、streaming、structured outputs
- [LangGraph Essentials - Python](https://academy.langchain.com/courses/langgraph-essentials-python) — State、Nodes、Edges、Memory，email workflow 实战
- [LangGraph Essentials - TypeScript](https://academy.langchain.com/courses/quickstart-langgraph-essentials-typescript) — 同 Python 版，TypeScript 生态，配套 [langgraph-101-ts](https://github.com/langchain-ai/langgraph-101-ts)

**Foundation（基础）**:

- [Introduction to LangGraph](https://academy.langchain.com/courses/intro-to-langgraph) — 从图原语、memory、HITL 到 deployment 的系统课程

**Deep Dive（深入）**:

- [Deep Research with LangGraph](https://academy.langchain.com/courses/deep-research-with-langgraph)
- [Deep Agents](https://academy.langchain.com/courses/deep-agents-with-langgraph)

**Observability（可观测）**:

- [Introduction to Agent Observability & Evaluations](https://academy.langchain.com/courses/intro-to-langsmith)

### 仓库内官方 Notebook（已同步到本项目，优先穿插到日程中）

#### LangChain Notebook 主线

- `langchain/L1_fast_agent.ipynb`：快速搭建 `create_agent`，适合放在第 3 周作为工程化起点
- `langchain/L2_messages.ipynb`：理解 messages 作为上下文载体，适合放在第 3 周做上下文拼装
- `langchain/L3_streaming.ipynb`：理解流式输出与事件流，适合放在第 3 周补链路可观测与交互体验
- `langchain/L4_tools.ipynb`：工具定义、描述与调用，适合放在第 3 周工具工程化
- `langchain/L5_tools_with_mcp.ipynb`：MCP 工具接入，适合放在第 3 周和第 9 周工具生态专题
- `langchain/L6_memory.ipynb`：基于 Agent 的消息持久化与记忆，适合放在第 5 周记忆体系
- `langchain/L7_structuredOutput.ipynb`：结构化输出与 Schema 约束，适合放在第 2 周
- `langchain/L8_dynamic.ipynb`：动态 Prompt 与中间件，适合放在第 2 周
- `langchain/L9_HITL.ipynb`：Human-in-the-Loop 中断，适合放在第 8 周协作审批与第 9 周安全控制

#### LangGraph Notebook 主线

- `langgraph/L1_nodes.ipynb`：State / Nodes 基础，适合放在第 4 周第一天
- `langgraph/L2_edges.ipynb`：并行 Edges 与状态归并，适合放在第 4 周第二天
- `langgraph/L3-L4_cedges_memory.ipynb`：Conditional Edges + Memory，适合放在第 4-5 周
- `langgraph/L5_interrupt.ipynb`：Interrupt / Human-in-the-Loop，适合放在第 8 周和第 9 周
- `langgraph/L6_EmailAgent.ipynb`：完整 email workflow，适合放在第 4 周周末做整合

#### 建议编排原则

- 第 2-3 周优先消化 LangChain Notebook，目标是把单体 Agent 的输入、输出、工具、Prompt、记忆边界理清楚
- 第 4-5 周切到 LangGraph Notebook，目标是把状态流、路由、记忆、人工中断连成工作流
- 第 8-9 周回看 `L9_HITL.ipynb` 与 `L5_interrupt.ipynb`，把多 Agent 协作和安全控制接起来
- 每个 notebook 学完后都要产出一个“迁移到专利助手”的小改造，不只停留在 notebook 跑通

### 补充官方文档（用于缺口）

- [LangChain Overview](https://docs.langchain.com/oss/python/langchain/overview)
- [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents)
- [LangChain Tools](https://docs.langchain.com/oss/python/langchain/tools)
- [LangChain MCP](https://docs.langchain.com/oss/python/langchain/mcp)
- [LangChain Structured Output](https://docs.langchain.com/oss/python/langchain/structured-output)
- [LangChain Guardrails](https://docs.langchain.com/oss/python/langchain/guardrails)
- [LangChain Retrieval](https://docs.langchain.com/oss/python/langchain/retrieval)
- [LangChain Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)
- [Build a personal assistant with subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents-personal-assistant)
- [LangChain Human-in-the-loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)
- [LangChain Studio](https://docs.langchain.com/oss/python/langchain/studio)
- [LangChain Deploy](https://docs.langchain.com/oss/python/langchain/deploy)
- [LangGraph Overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [LangGraph Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
- [LangGraph Quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart)
- [LangGraph Functional API](https://docs.langchain.com/oss/python/langgraph/functional-api)
- [LangGraph Subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)
- [LangGraph Memory](https://docs.langchain.com/oss/python/langgraph/memory)
- [LangGraph Interrupts](https://docs.langchain.com/oss/python/langgraph/human-in-the-loop)
- [LangGraph Studio](https://docs.langchain.com/oss/python/langgraph/studio)
- [LlamaIndex Rerank](https://docs.llamaindex.ai/en/stable/module_guides/querying/node_postprocessors/node_postprocessors/)
- [LlamaIndex Citation](https://docs.llamaindex.ai/en/stable/examples/query_engine/citation_query_engine/)
- [LangSmith Local Server](https://docs.langchain.com/langsmith/local-server)
- [LangSmith Deployment](https://docs.langchain.com/langsmith/deploy-to-cloud)

### Semantic Kernel（对照学习）

- [SK Overview](https://learn.microsoft.com/en-us/semantic-kernel/overview/)
- [SK Get Started (Python)](https://learn.microsoft.com/en-us/semantic-kernel/get-started/quick-start-guide?pivots=programming-language-python)
- [SK Concepts - Kernel](https://learn.microsoft.com/en-us/semantic-kernel/concepts/kernel)
- [SK Concepts - Plugins](https://learn.microsoft.com/en-us/semantic-kernel/concepts/plugins/)
- [SK Concepts - Planner](https://learn.microsoft.com/en-us/semantic-kernel/concepts/planning)
- [SK Concepts - Agents](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/)
- [SK GitHub Examples](https://github.com/microsoft/semantic-kernel/tree/main/python/samples)

### LearnGraph 1.X（补充阅读）

> 来源：[LearnGraph.online](https://www.learngraph.online/LearnGraph%201.X/README.html)，中文 LangGraph 系统教程，作为官方内容的深度补充。

**核心机制（Ch3）**:

- [3.1 State Schema](https://www.learngraph.online/LearnGraph%201.X/module-3/3.1%20State%20Schema.html)
- [3.2 State Reducers](https://www.learngraph.online/LearnGraph%201.X/module-3/3.2%20State%20Reducers.html)
- [3.3 Multiple Schemas](https://www.learngraph.online/LearnGraph%201.X/module-3/3.3%20Multiple%20Schemas.html)
- [3.4 Trim & Filter Messages](https://www.learngraph.online/LearnGraph%201.X/module-3/3.4%20Trim%20Filter%20Messages.html)
- [3.5 Chatbot Summarization](https://www.learngraph.online/LearnGraph%201.X/module-3/3.5%20Chatbot%20Summarization.html)
- [3.6 Chatbot External Memory](https://www.learngraph.online/LearnGraph%201.X/module-3/3.6%20Chatbot%20External%20Memory.html)

**人机协作（Ch4）**:

- [4.1 Breakpoints](https://www.learngraph.online/LearnGraph%201.X/module-4-human-in-the-loop/4.1%20Breakpoints.html)
- [4.2 Dynamic Breakpoints](https://www.learngraph.online/LearnGraph%201.X/module-4-human-in-the-loop/4.2%20Dynamic%20Breakpoints.html)
- [4.3 State Editing Human Feedback](https://www.learngraph.online/LearnGraph%201.X/module-4-human-in-the-loop/4.3%20State%20Editing%20Human%20Feedback.html)
- [4.4 Streaming Interruption](https://www.learngraph.online/LearnGraph%201.X/module-4-human-in-the-loop/4.4%20Streaming%20Interruption.html)
- [4.5 Time Travel](https://www.learngraph.online/LearnGraph%201.X/module-4-human-in-the-loop/4.5%20Time%20Travel.html)

**高级模式（Ch5）**:

- [5.1 Parallelization](https://www.learngraph.online/LearnGraph%201.X/module-5-advanced-patterns/5.1%20Parallelization.html)
- [5.2 Sub-Graph](https://www.learngraph.online/LearnGraph%201.X/module-5-advanced-patterns/5.2%20Sub-Graph.html)
- [5.3 Map-Reduce](https://www.learngraph.online/LearnGraph%201.X/module-5-advanced-patterns/5.3%20Map-Reduce.html)
- [5.4 Research Assistant](https://www.learngraph.online/LearnGraph%201.X/module-5-advanced-patterns/5.4%20Research%20Assistant.html)

**记忆系统（Ch6）**:

- [6.1 Memory Agent](https://www.learngraph.online/LearnGraph%201.X/module-6-memory-system/6.1%20Memory%20Agent.html)
- [6.2 Memory Store](https://www.learngraph.online/LearnGraph%201.X/module-6-memory-system/6.2%20Memory%20Store.html)
- [6.3 Memory Schema Profile](https://www.learngraph.online/LearnGraph%201.X/module-6-memory-system/6.3%20Memory%20Schema%20Profile.html)
- [6.4 Memory Schema Collection](https://www.learngraph.online/LearnGraph%201.X/module-6-memory-system/6.4%20Memory%20Schema%20Collection.html)

**生产部署（Ch7）**:

- [7.1 Creating Deployment](https://www.learngraph.online/LearnGraph%201.X/module-7-production-deployment/7.1%20Creating%20Deployment.html)
- [7.2 Connecting to Deployment](https://www.learngraph.online/LearnGraph%201.X/module-7-production-deployment/7.2%20Connecting%20to%20Deployment.html)
- [7.3 Double Texting](https://www.learngraph.online/LearnGraph%201.X/module-7-production-deployment/7.3%20Double%20Texting.html)
- [7.4 Assistants](https://www.learngraph.online/LearnGraph%201.X/module-7-production-deployment/7.4%20Assistants.html)

**经典案例（Ch8）**:

- [8.0.0 架构图集合](https://www.learngraph.online/LearnGraph%201.X/module-8-classic-examples/8.0.0%20All%20Graphs.html)
- [8.0.1 State-node-edge](https://www.learngraph.online/LearnGraph%201.X/module-8-classic-examples/8.0.1%20State-node-edge.html)
- [8.0.2 Routing function](https://www.learngraph.online/LearnGraph%201.X/module-8-classic-examples/8.0.2%20Routing%20function.html)
- [8.0.4 Conditional edges](https://www.learngraph.online/LearnGraph%201.X/module-8-classic-examples/8.0.4%20Conditional%20edges.html)
- [8.1 Agent Simulation Evaluation](https://www.learngraph.online/LearnGraph%201.X/module-8-classic-examples/8.1%20Agent%20Simulation%20Evaluation.html)
- [8.2 Information Gathering Prompting](https://www.learngraph.online/LearnGraph%201.X/module-8-classic-examples/8.2%20Information%20Gathering%20Prompting.html)
- [8.3 Code Assistant RAG+自我纠正](https://www.learngraph.online/LearnGraph%201.X/module-8-classic-examples/8.3%20Code%20Assistant.html)

**Deep Research（Ch9）**:

- [9.3 MCP 集成](https://www.learngraph.online/LearnGraph%201.X/module-9-deep-research/9.3%20MCP.html)
- [9.5 完整系统集成](https://www.learngraph.online/LearnGraph%201.X/module-9-deep-research/9.5%20Whole%20case.html)

**TradingAgent 精华（Ch10）**:

- [10.3 State 状态管理](https://www.learngraph.online/LearnGraph%201.X/module-10-TradingAgent/10.3%20State.html)
- [10.5 研究员辩论](https://www.learngraph.online/LearnGraph%201.X/module-10-TradingAgent/10.5%20Analyst.html)
- [10.6 Graph 编排](https://www.learngraph.online/LearnGraph%201.X/module-10-TradingAgent/10.6%20Graph.html)
- [10.7 端到端执行流程](https://www.learngraph.online/LearnGraph%201.X/module-10-TradingAgent/10.7%20Data%20flow.html)

**进阶主题（Ch11）**:

- [11.0.1 Function→Tool→Node→Agent→SubAgent→DeepAgent](https://www.learngraph.online/LearnGraph%201.X/module-11-subgraph-mermaid-mcp-agent-node-tool/11.0.1%20Function-tool-Node-Agent-SubAgent-Deepagent.html)
- [11.1 Loop Patterns](https://www.learngraph.online/LearnGraph%201.X/module-11-subgraph-mermaid-mcp-agent-node-tool/11.1%20LangGraph%20Loop%20Patterns.html)
- [11.2 Mermaid 可视化](https://www.learngraph.online/LearnGraph%201.X/module-11-subgraph-mermaid-mcp-agent-node-tool/11.2%20Visualizing%20with%20Mermaid.html)
- [11.3 LangGraph MCP Integration](https://www.learngraph.online/LearnGraph%201.X/module-11-subgraph-mermaid-mcp-agent-node-tool/11.3%20LangGraph%20MCP%20Integration.html)
- [11.4 Middleware](https://www.learngraph.online/LearnGraph%201.X/module-11-subgraph-mermaid-mcp-agent-node-tool/11.4%20Middleware.html)
- [11.5 Command 动态路由](https://www.learngraph.online/LearnGraph%201.X/module-11-subgraph-mermaid-mcp-agent-node-tool/11.5%20Command.html)

**多智能体工作流（Ch12）**:

- [12.0 Introduction](https://www.learngraph.online/LearnGraph%201.X/module-12-multi-agent-workflows/12.0%20Introduction.html)
- [12.2 Supervisor Simple Example](https://www.learngraph.online/LearnGraph%201.X/module-12-multi-agent-workflows/12.2%20Supervisor%20Simple%20Example.html)
- [12.3 Supervisor Complex Example](https://www.learngraph.online/LearnGraph%201.X/module-12-multi-agent-workflows/12.3%20Supervisor%20Complex%20Example.html)
- [12.4 Multi-Agent Collaboration](https://www.learngraph.online/LearnGraph%201.X/module-12-multi-agent-workflows/12.4%20Multi-Agent%20Collaboration.html)
- [12.5 Hierarchical Teams](https://www.learngraph.online/LearnGraph%201.X/module-12-multi-agent-workflows/12.5%20Hierarchical%20Teams.html)
- [12.6 Deep-Search-from-Scratch](https://www.learngraph.online/LearnGraph%201.X/module-12-multi-agent-workflows/12.6%20Deep-Search-from-Scratch.html)
- [12.7 create_supervisor()](<https://www.learngraph.online/LearnGraph%201.X/module-12-multi-agent-workflows/12.7%20create_supervisor().html>)
- [12.9 Supervisor Cheatsheet](https://www.learngraph.online/LearnGraph%201.X/module-12-multi-agent-workflows/12.9%20Supervisor%20Cheatsheet.html)

**Agentic RAG（Ch13）**:

- [13.1 Agentic RAG 概述](https://www.learngraph.online/LearnGraph%201.X/module-13-agentic-rag/13.1%20Introduction.html)
- [13.2 Intro of RAG](https://www.learngraph.online/LearnGraph%201.X/module-13-agentic-rag/13.2%20Intro%20of%20RAG.html)
- [13.3 Design Mode](https://www.learngraph.online/LearnGraph%201.X/module-13-agentic-rag/13.3%20Design%20Mode.html)
- [13.5 Agentic RAG Architecture](https://www.learngraph.online/LearnGraph%201.X/module-13-agentic-rag/13.5%20Agentic%20RAG%20Architecture.html)
- [13.7 LangGraph Agentic RAG](https://www.learngraph.online/LearnGraph%201.X/module-13-agentic-rag/13.7%20LangGraph%20Agentic%20RAG.html)
- [13.8 Qdrant Agentic RAG](https://www.learngraph.online/LearnGraph%201.X/module-13-agentic-rag/13.8%20Qdrant%20Agentic%20RAG.html)
- [13.9 Self-Reflective RAG](https://www.learngraph.online/LearnGraph%201.X/module-13-agentic-rag/13.9%20Self-Reflective%20RAG.html)
- [13.10 Corrective RAG](https://www.learngraph.online/LearnGraph%201.X/module-13-agentic-rag/13.10%20Corrective%20RAG.html)
- [13.11 Adaptive RAG](https://www.learngraph.online/LearnGraph%201.X/module-13-agentic-rag/13.11%20Adaptive%20RAG.html)

**Deep Agent（Ch14）**:

- [14.0 Thinking in LangGraph（五步法 + 5种工作流模式）](https://www.learngraph.online/LearnGraph%201.X/module-14-deep-agent/14.0%20Introduction.html)

**可观测（Ch15）**:

- [15.1 LangSmith](https://www.learngraph.online/LearnGraph%201.X/module-15-langsmith-langfuse/15.1%20LangSmith.html)
- [15.2 LangFuse](https://www.learngraph.online/LearnGraph%201.X/module-15-langsmith-langfuse/15.2%20LangFuse.html)

### LearnGraph 1.X 可选扩展（按兴趣自选）

- [Ch16 MetaGPT（角色驱动多Agent）](https://www.learngraph.online/LearnGraph%201.X/module-16-MetaGPT/16.0%20Introduction.html) — 适合 W8 多 Agent 对照
- [Ch17 CrewAI & CAMEL（任务驱动协作）](https://www.learngraph.online/LearnGraph%201.X/module-17-CrewAI-CAMEL.md/17.0%20Introduction.html) — 适合 W8 多 Agent 对照
- [Ch18.1 Customer Support Agent（RAG 智能客服）](https://www.learngraph.online/LearnGraph%201.X/module-18-Claude-quickstarts/18.1%20Customer%20Support%20Agent.html) — 适合 W6-7 RAG 扩展
- [Ch21 PydanticAI（类型安全 Agent 框架）](https://www.learngraph.online/LearnGraph%201.X/module-21-pydanticai/21.1%20introduction.html) — 适合 W3 SK 对照时

---

## 2. D1-D84 逐日计划（每天都给出教程与链接）

说明：

- 工作日 D1-D5：30-60 分钟
- 周末 D6-D7：120 分钟
- 每天固定交付：学习笔记 + 一个可验证产物（优先可运行代码）

### 渐进式项目：我的专利助手（贯穿 12 周）

每周在同一个项目上叠加功能，从"只会说话的 chatbot"进化为"完整的专利分析系统"。
每周末验收时，你应该能演示"我的助手又学会了什么新能力"。

| 周  | 助手能力         | 你能演示什么                            |
| --- | ---------------- | --------------------------------------- |
| W1  | 能对话 + 调工具  | 终端对话，AI 能搜专利（模拟数据）       |
| W2  | 能输出 JSON      | 输入问题 → 结构化 JSON 输出             |
| W3  | LangChain 工程化 | 链路日志 + 错误捕获展示                 |
| W4  | 有状态流转       | 多步骤任务：分析→检索→总结，看到图流转  |
| W5  | 记住偏好         | "我上次问的是什么？" → 正确回忆         |
| W6  | 能检索文档       | "这篇专利说了什么？" → 基于文档内容回答 |
| W7  | 回答可追溯       | 每个结论后附带 [来源1][来源2]           |
| W8  | 多角色协作       | 检索员+分析员+审核员各司其职            |
| W9  | 安全可控         | 注入攻击被拦截，非法参数被拒绝          |
| W10 | 可观测           | LangSmith 看到每步耗时和输入输出        |
| W11 | 高性能           | 缓存命中、并行执行、降级切换            |
| W12 | 完整交付         | 端到端 demo 视频                        |

### 第1周：概念打底与最小 Agent（D1-D7）

- [x] D1 总目标：让 AI 回复你的第一个问题
- [x] D1-速效（10min）：安装 Ollama，跑通第一次对话
  ```bash
  brew install ollama && ollama run llama3.2
  # 在终端里直接提问："什么是 Agent？" → 看到 AI 回复
  ```
- [x] D1-学习：完成教程 [HF Unit0](https://huggingface.co/learn/agents-course/en/unit0/introduction) + [Happy-LLM Chapter1](https://github.com/datawhalechina/happy-llm/tree/main/docs/chapter1)（带着"刚才的对话和 Agent 有什么区别？"这个问题去看）
- [x] D1-实操：写一个 Python 脚本调用 Ollama，对比直接对话 vs 代码调用的差异
  ```python
  from langchain_ollama import ChatOllama
  llm = ChatOllama(model="llama3.2")
  print(llm.invoke("什么是 Agent？").content)
  ```
- [x] D1-产出：`lectures/lecture01/day01_first_chat.py` — 可运行，终端能看到 AI 回复
- [x] D1-验收：终端截图保存到 `screenshots/day01.png`
- [x] D2 总目标：看到 token 逐个生成的过程
- [x] D2-速效（10min）：给 D1 脚本加 streaming，看到文字一个一个出现
  ```python
  for chunk in llm.stream("解释一下 Transformer 架构"):
      print(chunk.content, end="", flush=True)
  ```
- [x] D2-学习：完成教程 [Happy-LLM Chapter3](https://github.com/datawhalechina/happy-llm/tree/main/docs/chapter3)（跳过数学公式，只看文字描述和图示）+ HF Unit1 前5节：[Introduction](https://huggingface.co/learn/agents-course/en/unit1/introduction) → [What is an Agent?](https://huggingface.co/learn/agents-course/en/unit1/what-are-agents) → [Quiz1](https://huggingface.co/learn/agents-course/en/unit1/quiz1) → [What are LLMs?](https://huggingface.co/learn/agents-course/en/unit1/what-are-llms) → [Messages and Special Tokens](https://huggingface.co/learn/agents-course/en/unit1/messages-and-special-tokens)
- [x] D2-实操：在脚本中加入 token 计数，打印"共生成 N 个 token，耗时 X 秒"
- [x] D2-产出：`lectures/lecture02/day02_streaming.py` — 可运行，能看到逐字输出 + token 统计
- [x] D2-验收：终端截图展示 streaming 效果
- [x] D3 总目标：让 AI 学会调用工具（计算器）
- [x] D3-速效（10min）：用 LangChain 给 AI 一个加法工具，让它算 123+456
  ```python
  from langchain_core.tools import tool
  @tool
  def add(a: int, b: int) -> int:
      """两个数相加"""
      return a + b
  # 绑定工具到 LLM，提问"123+456等于多少？"
  ```
- [x] D3-学习：[LangChain Tools](https://docs.langchain.com/oss/python/langchain/tools) + HF Unit1 第6-9节（工具+ReAct）：[What are Tools?](https://huggingface.co/learn/agents-course/en/unit1/tools) → [Quiz2](https://huggingface.co/learn/agents-course/en/unit1/quiz2) → [Agent Steps and Structure](https://huggingface.co/learn/agents-course/en/unit1/agent-steps-and-structure) → [Thoughts (ReAct)](https://huggingface.co/learn/agents-course/en/unit1/thoughts)
- [x] D3-实操：加第二个工具（乘法），让 AI 自主选择正确工具
- [x] D3-产出：`lectures/lecture03/day03_tool_agent.py` — AI 能自主选择加法或乘法工具
- [x] D3-验收：输入"3乘以4再加5" → AI 正确调用两个工具并返回 17
- [x] D4 总目标：让 AI 调用你设计的"专利搜索"工具
- [x] D4-速效（10min）：写一个假的专利搜索工具（返回模拟数据），接入 `lectures/lecture03/` 的 Agent
  ```python
  @tool
  def search_patent(keyword: str) -> str:
      """搜索专利数据库"""
      return f"找到3件关于'{keyword}'的专利：JP2024-001, JP2024-002, JP2024-003"
  ```
- [x] D4-学习：[LangChain MCP](https://docs.langchain.com/oss/python/langchain/mcp) + HF Unit1 第10-11节（Action/Observation）：[Actions](https://huggingface.co/learn/agents-course/en/unit1/actions) → [Observations](https://huggingface.co/learn/agents-course/en/unit1/observations) + [HF Unit2 Introduction](https://huggingface.co/learn/agents-course/en/unit2/introduction)（框架概览）
- [x] D4-实操：给工具加输入校验（keyword 不能为空、长度限制），设计 JSON Schema
- [x] D4-产出：`lectures/lecture04/day04_patent_tool.py` — "专利助手 v0.1"，能接收问题并返回模拟专利
- [x] D4-验收：输入"帮我搜索生物降解塑料的专利" → 返回模拟结果
- [x] D5 总目标：让 Agent 优雅地处理错误
- [x] D5-速效（10min）：故意让工具报错（传入 None），观察 Agent 崩溃
- [x] D5-学习：完成教程 [Happy-LLM Chapter5](https://github.com/datawhalechina/happy-llm/tree/main/docs/chapter5) + [LangChain Overview](https://docs.langchain.com/oss/python/langchain/overview)
- [x] D5-实操：给 `lectures/lecture04/` 的 Agent 加错误处理 — 工具超时/解析失败/空结果都有兜底
- [x] D5-产出：`lectures/lecture05/day05_error_handling.py` — Agent 遇到错误不崩溃，给出友好提示
- [x] D5-验收：故意输入 3 种错误场景，Agent 都能正常回复
- [x] D6 总目标：整合 D1-D5 为"专利助手 v0.2"可演示版（120min）
- [x] D6-速效（10min）：把 lecture03-lecture05 的代码合并为一个脚本，跑通完整对话
- [x] D6-学习：HF Unit1 第12-14节（实操收尾）：[Dummy Agent Library](https://huggingface.co/learn/agents-course/en/unit1/dummy-agent-library) → [Tutorial (smolagents)](https://huggingface.co/learn/agents-course/en/unit1/tutorial) → [Final Quiz](https://huggingface.co/learn/agents-course/en/unit1/final-quiz) + [Conclusion](https://huggingface.co/learn/agents-course/en/unit1/conclusion) + [Happy-LLM Chapter7](https://github.com/datawhalechina/happy-llm/tree/main/docs/chapter7)
- [x] D6-实操：加入对话循环（while True），让助手可以连续对话；加入 streaming 输出
- [x] D6-产出：`lectures/lecture06/patent_assistant_v0.2.py` — 完整的终端对话助手，支持专利搜索+计算+错误处理+streaming
- [x] D6-验收：录制一段 30 秒终端 demo（连续提问 3 个问题，展示工具调用和 streaming）
- [x] D7 总目标：周展示 + 复盘（120min）
- [x] D7-速效（10min）：给 patent_assistant_v0.2.py 加一个 `--version` 参数，打印已有功能列表
- [x] D7-学习：[LangChain Overview](https://docs.langchain.com/oss/python/langchain/overview)（把本周的消息、工具、动作、观察串成统一心智模型）
- [x] D7-实操：整理本周学习笔记到 `lectures/lecture07/README.md` 和 `docs/weekly/week01_summary.md`，回顾 lecture01-lecture06 的代码
- [x] D7-产出：`lectures/lecture07/README.md` + `docs/weekly/week01_summary.md`
- [x] D7-验收：能向别人（或自己）演示"我这周做了一个能对话、能搜专利、能处理错误的 AI 助手"
- [x] D7-里程碑：我的 AI 助手能对话了！

### 第2周：Prompt 与结构化输出（D8-D14）

- [x] D8 总目标：Prompt 基础
- [x] D8-学习：先跑本地官方 notebook `langchain/L7_structuredOutput.ipynb`，再看 [LangChain Essentials Lesson 7: Structured Output](https://academy.langchain.com/courses/langchain-essentials-python)（重点：`with_structured_output` 用法与 JSON Schema）+ [Happy-LLM Chapter2](https://github.com/datawhalechina/happy-llm/tree/main/docs/chapter2)（Prompt 设计原则）
- [x] D8-实操：写3个模板（问答/抽取/改写）
- [x] D8-产出：`lectures/lecture08/prompt_templates.py`
- [x] D8-验收：每个模板都有变量定义
- [x] D9 总目标：约束输出
- [x] D9-学习：先跑本地官方 notebook `langchain/L8_dynamic.ipynb`，再看 [LangChain Essentials Lesson 8: Dynamic Prompt](https://academy.langchain.com/courses/langchain-essentials-python)（动态 Prompt 模板与变量注入）+ [Pydantic 官方文档 - Models](https://docs.pydantic.dev/latest/concepts/models/)（Schema 定义基础）
- [x] D9-实操：定义结构化输出模型
- [x] D9-产出：`lectures/lecture09/schema_v1.py`
- [x] D9-验收：可自动验证通过
- [x] D10 总目标：失败样本构建
- [x] D10-学习：[LangChain Structured Output](https://docs.langchain.com/oss/python/langchain/structured-output)（信息抽取、Schema 约束、失败重试）+ 回放 `langchain/L7_structuredOutput.ipynb` 里的成功/失败样例
- [x] D10-实操：构造5条输出失败样本
- [x] D10-产出：`lectures/lecture10/failure_samples.json`
- [x] D10-验收：覆盖缺字段/类型错/多余字段
- [x] D11 总目标：重试策略
- [x] D11-学习：[LangChain Structured Output](https://docs.langchain.com/oss/python/langchain/structured-output)（结构化输出校验与错误处理）+ 回顾 D10 失败样本 + 对照 `langchain/L7_structuredOutput.ipynb` 的输出约束方式
- [x] D11-实操：设计修复提示+二次解析
- [x] D11-产出：`lectures/lecture11/retry_flow.mmd` + `lectures/lecture11/retry_parser.py`
- [x] D11-验收：两轮内成功率提升可观测
- [x] D12 总目标：Prompt A/B
- [x] D12-学习：回顾 [Prompt Engineering Guide - Few-shot](https://www.promptingguide.ai/techniques/fewshot) + [Prompt Engineering Guide - Chain-of-Thought](https://www.promptingguide.ai/techniques/cot)（重点：Few-shot / Chain-of-Thought 技巧）+ 回顾 `langchain/L7_structuredOutput.ipynb` / `langchain/L8_dynamic.ipynb` 笔记
- [x] D12-实操：比较短提示与强约束提示
- [x] D12-产出：`lectures/lecture12/ab_compare.py`
- [x] D12-验收：短提示更适合低风险开放生成；强约束提示在结构化输出和自动校验场景更稳定
- [x] D13 总目标：专利问题结构化
- [x] D13-学习：综合运用 `langchain/L7_structuredOutput.ipynb` + `langchain/L8_dynamic.ipynb` + D10-D12 的经验，回顾 [HF Unit1: What are Tools?](https://huggingface.co/learn/agents-course/en/unit1/tools)（复习工具定义与 JSON Schema）
- [x] D13-实操：实现"问题->JSON分析"CLI
- [x] D13-产出：`lectures/lecture13/cli_v1.py`
- [x] D13-验收：10条输入稳定输出
- [x] D14 总目标：周复盘 / 缓冲日
- [x] D14-学习：回顾本周所有产出，整理 Prompt 设计与结构化输出的最佳实践，并把 `L7/L8` 里能迁移到专利助手的模式单独记一页
- [x] D14-实操：提炼对你项目最有效提示策略
- [x] D14-产出：`lectures/lecture14/prompt_strategies.json` + `docs/weekly/week02_summary.md`
- [x] D14-验收：每条策略有反例
- [x] D14-里程碑：输入问题 → 输出格式化 JSON，10 条输入稳定输出

### 第3周：LangChain 工程化（D15-D21）

- [ ] D15 总目标：Runnable/Chain 基础
- [ ] D15-学习：先跑本地官方 notebook `langchain/L1_fast_agent.ipynb`，再看 [LangChain Overview](https://docs.langchain.com/oss/python/langchain/overview) + [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents)
- [ ] D15-实操：搭一条最小链
- [ ] D15-产出：`lectures/lecture15/chain_demo.py`
- [ ] D15-验收：链路日志可读
- [ ] D16 总目标：链路加工具调用
- [ ] D16-学习：先跑本地官方 notebook `langchain/L4_tools.ipynb` + `langchain/L5_tools_with_mcp.ipynb`，再看 [LangChain Tools](https://docs.langchain.com/oss/python/langchain/tools) + [LangChain MCP](https://docs.langchain.com/oss/python/langchain/mcp)
- [ ] D16-实操：接入一个检索工具
- [ ] D16-产出：`lectures/lecture16/tool_chain.py`
- [ ] D16-验收：工具错误可捕获
- [ ] D17 总目标：解析与异常层
- [ ] D17-学习：回顾 `langchain/L1_fast_agent.ipynb` 的 agent 执行链路 + [LangChain Overview](https://docs.langchain.com/oss/python/langchain/overview) + [LangChain Guardrails](https://docs.langchain.com/oss/python/langchain/guardrails)（异常处理与边界控制）
- [ ] D17-实操：统一异常处理
- [ ] D17-产出：`lectures/lecture17/error_wrapper.py`
- [ ] D17-验收：错误码分类清晰
- [ ] D18 总目标：上下文拼装
- [ ] D18-学习：先跑本地官方 notebook `langchain/L2_messages.ipynb`，再看 [Happy-LLM Chapter4](https://github.com/datawhalechina/happy-llm/tree/main/docs/chapter4) + [LangChain Context Engineering](https://docs.langchain.com/oss/python/langchain/context-engineering)
- [ ] D18-实操：实现上下文裁剪
- [ ] D18-产出：`lectures/lecture18/context_builder.py`
- [ ] D18-验收：超长输入可自动截断
- [ ] D19 总目标：单测补齐
- [ ] D19-学习：先跑本地官方 notebook `langchain/L3_streaming.ipynb`，再看 [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents)（把 agent loop、tool call、state 输入输出读清楚，为第4周铺路）
- [ ] D19-实操：写5个关键测试
- [ ] D19-产出：`lectures/lecture19/test_cases.py`
- [ ] D19-验收：覆盖正常与异常路径
- [ ] D20 总目标：端到端串联
- [ ] D20-学习：回顾本周 `langchain/L1-L5` notebook 与 [LangChain Overview](https://docs.langchain.com/oss/python/langchain/overview) / [Agents](https://docs.langchain.com/oss/python/langchain/agents) / [Tools](https://docs.langchain.com/oss/python/langchain/tools) / [MCP](https://docs.langchain.com/oss/python/langchain/mcp) / [Guardrails](https://docs.langchain.com/oss/python/langchain/guardrails) 笔记，综合运用
- [ ] D20-实操：把 `lectures/lecture13/cli_v1.py` 迁移到可复用链路
- [ ] D20-产出：`lectures/lecture20/cli_v2.py`
- [ ] D20-验收：功能等价且结构更清晰
- [ ] D21 总目标：周复盘 + Semantic Kernel 对照 + LangGraph Essentials 预习
- [ ] D21-学习：[SK Get Started](https://learn.microsoft.com/en-us/semantic-kernel/get-started/quick-start-guide?pivots=programming-language-python) + 先跑本地官方 notebook `langgraph/L1_nodes.ipynb` / `langgraph/L2_edges.ipynb` / `langgraph/L3-L4_cedges_memory.ipynb` 的前半部分，再看 [LangGraph Essentials L1-L3 预习: Nodes / Edges / Conditional Edges](https://academy.langchain.com/courses/langgraph-essentials-python)
- [ ] D21-LearnGraph 补充：[LG 3.1 State Schema](https://www.learngraph.online/LearnGraph%201.X/module-3/3.1%20State%20Schema.html)（为 W4 LangGraph 做 State 设计预习）
- [ ] D21-实操：列出重构点 + 用 SK 重写 `lectures/lecture15/chain_demo.py` 的最小链路，对比 LangChain 与 SK 的开发体验；**预习 LangGraph Essentials（State/Nodes/Edges 概览），跑通 email workflow 示例，为第 4 周 LangGraph 学习热身**
- [ ] D21-产出：`lectures/lecture21/refactor_priorities.json` + `docs/comparisons/sk_vs_langchain.md` + `lectures/lecture21/langgraph_essentials_preview.md` + `docs/weekly/week03_summary.md`
- [ ] D21-验收：至少3项有收益评估；SK 对比覆盖 API 风格、插件机制、错误处理；能解释 State/Nodes/Edges 三者关系
- [ ] D21-里程碑：链路日志可读 + 工具错误可捕获，`cli v2` 能跑通

### 第4周：LangGraph 入门与状态机（D22-D28）

- [ ] D22 总目标：LangGraph 基础概念（基于 D21 Quickstart 预习深入）
- [ ] D22-学习：先精读本地官方 notebook `langgraph/L1_nodes.ipynb`，再看 [LangGraph Overview](https://docs.langchain.com/oss/python/langgraph/overview) + [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [ ] D22-LearnGraph 补充：[LG 8.0.1 State-node-edge](https://www.learngraph.online/LearnGraph%201.X/module-8-classic-examples/8.0.1%20State-node-edge.html) + [LG 3.2 State Reducers](https://www.learngraph.online/LearnGraph%201.X/module-3/3.2%20State%20Reducers.html)（经典案例 + Reducer 深入）
- [ ] D22-实操：定义状态对象（结合 D21 email workflow 的 State 模式）
- [ ] D22-产出：`lectures/lecture22/state_draft.py`
- [ ] D22-验收：状态字段可解释，能对比 email workflow State 与你的专利分析 State 差异
- [ ] D23 总目标：节点与边
- [ ] D23-学习：先精读本地官方 notebook `langgraph/L2_edges.ipynb`，再看 [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) + [LangGraph Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
- [ ] D23-LearnGraph 补充：[LG 8.0.2 Routing function](https://www.learngraph.online/LearnGraph%201.X/module-8-classic-examples/8.0.2%20Routing%20function.html) + [LG 8.0.4 Conditional edges](https://www.learngraph.online/LearnGraph%201.X/module-8-classic-examples/8.0.4%20Conditional%20edges.html)（路由与条件边案例）
- [ ] D23-实操：实现3节点图
- [ ] D23-产出：`lectures/lecture23/graph_v1.py`
- [ ] D23-验收：执行路径正确
- [ ] D24 总目标：ReAct in Graph
- [ ] D24-学习：先精读本地官方 notebook `langgraph/L3-L4_cedges_memory.ipynb` 的 Conditional Edges 部分，再看 [HF Unit2.3 - LangGraph](https://huggingface.co/learn/agents-course/en/unit2/langgraph/introduction) + [LangGraph Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents) + 回顾 [HF Unit1: Thoughts (ReAct)](https://huggingface.co/learn/agents-course/en/unit1/thoughts)
- [ ] D24-实操：把ReAct迁移到图
- [ ] D24-产出：`lectures/lecture24/react_graph.py`
- [ ] D24-验收：工具调用稳定
- [ ] D25 总目标：反思机制
- [ ] D25-学习：先精读本地官方 notebook `langgraph/L3-L4_cedges_memory.ipynb` 的 Memory 部分，再看 [LangChain Context Engineering](https://docs.langchain.com/oss/python/langchain/context-engineering) + [LangGraph Memory](https://docs.langchain.com/oss/python/langgraph/memory)
- [ ] D25-实操：加一次自检节点
- [ ] D25-产出：`lectures/lecture25/reflection_node.py`
- [ ] D25-验收：错误回答可二次修正
- [ ] D26 总目标：Plan-and-Execute
- [ ] D26-学习：先跑本地官方 notebook `langgraph/L6_EmailAgent.ipynb`，再看 [LangGraph Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents) + [Deep Agents](https://academy.langchain.com/courses/deep-agents-with-langgraph)（规划与执行模式）
- [ ] D26-LearnGraph 补充：[LG 5.4 Research Assistant](https://www.learngraph.online/LearnGraph%201.X/module-5-advanced-patterns/5.4%20Research%20Assistant.html)（Plan-and-Execute 研究助手案例）
- [ ] D26-实操：实现规划节点
- [ ] D26-产出：`lectures/lecture26/plan_execute.py`
- [ ] D26-验收：子任务可执行
- [ ] D27 总目标：ReWOO与效率
- [ ] D27-学习：[LangGraph Functional API](https://docs.langchain.com/oss/python/langgraph/functional-api) + [LangGraph Subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)
- [ ] D27-LearnGraph 补充：[LG 5.2 Sub-Graph](https://www.learngraph.online/LearnGraph%201.X/module-5-advanced-patterns/5.2%20Sub-Graph.html) + [LG 5.3 Map-Reduce](https://www.learngraph.online/LearnGraph%201.X/module-5-advanced-patterns/5.3%20Map-Reduce.html)（子图和 Map-Reduce 深度解读）
- [ ] D27-实操：比较两种规划模式
- [ ] D27-产出：`lectures/lecture27/compare_plan_modes.py`
- [ ] D27-验收：给出成本/质量结论
- [ ] D28 总目标：周集成 / 缓冲日
- [ ] D28-学习：回放本地官方 notebook `langgraph/L6_EmailAgent.ipynb`，再看 [LangGraph Essentials L6: Application](https://academy.langchain.com/courses/langgraph-essentials-python)（整合实战）+ 回顾本周笔记
- [ ] D28-LearnGraph 补充：[LG 8.0.0 架构图集合](https://www.learngraph.online/LearnGraph%201.X/module-8-classic-examples/8.0.0%20All%20Graphs.html)（周集成时参考全部架构图模式）
- [ ] D28-实操：形成Graph v2
- [ ] D28-产出：`lectures/lecture28/patent_graph_v2.py` + `docs/weekly/week04_summary.md`
- [ ] D28-验收：能跑通完整示例
- [ ] D28-里程碑：LangGraph 多步骤任务流转，打印 Mermaid 图 + 执行路径

### 第5周：Memory 体系（D29-D35）

- [ ] D29 总目标：Session与历史
- [ ] D29-学习：先跑本地官方 notebook `langchain/L6_memory.ipynb`，再看 [Intro to LangGraph M5 L1: Short vs Long-Term Memory](https://academy.langchain.com/courses/intro-to-langgraph) + [LangChain Essentials L6: Memory](https://academy.langchain.com/courses/langchain-essentials-python)
- [ ] D29-LearnGraph 补充：[LG 6.1 Memory Agent](https://www.learngraph.online/LearnGraph%201.X/module-6-memory-system/6.1%20Memory%20Agent.html)（Memory Agent 完整解读）
- [ ] D29-实操：理清会话边界
- [ ] D29-产出：`lectures/lecture29/test_session_rules.py`
- [ ] D29-验收：跨会话不串数据
- [ ] D30 总目标：ChatBot短期记忆
- [ ] D30-学习：回看本地官方 notebook `langgraph/L3-L4_cedges_memory.ipynb` 的 Memory 实验，再看 [LangGraph Memory](https://docs.langchain.com/oss/python/langgraph/memory) + [LangGraph Add Memory Guide](https://docs.langchain.com/oss/python/langgraph/add-memory)
- [ ] D30-LearnGraph 补充：[LG 3.4 Trim & Filter Messages](https://www.learngraph.online/LearnGraph%201.X/module-3/3.4%20Trim%20Filter%20Messages.html) + [LG 3.5 Chatbot Summarization](https://www.learngraph.online/LearnGraph%201.X/module-3/3.5%20Chatbot%20Summarization.html)（消息裁剪与摘要记忆工程实现）
- [ ] D30-实操：摘要记忆接入
- [ ] D30-产出：`lectures/lecture30/summary_memory.py`
- [ ] D30-验收：多轮问答一致性提升
- [ ] D31 总目标：Agent记忆
- [ ] D31-学习：对比 `langchain/L6_memory.ipynb` 与 `langgraph/L3-L4_cedges_memory.ipynb` 的记忆方式，再看 [LangGraph Add Memory Guide](https://docs.langchain.com/oss/python/langgraph/add-memory) + [Introduction to LangGraph](https://academy.langchain.com/courses/intro-to-langgraph)（Memory 模块）
- [ ] D31-LearnGraph 补充：[LG 6.2 Memory Store](https://www.learngraph.online/LearnGraph%201.X/module-6-memory-system/6.2%20Memory%20Store.html) + [LG 3.6 External Memory](https://www.learngraph.online/LearnGraph%201.X/module-3/3.6%20Chatbot%20External%20Memory.html)（长期记忆存储+外部记忆）
- [ ] D31-实操：长期记忆接口
- [ ] D31-产出：`lectures/lecture31/long_term_store.py`
- [ ] D31-验收：可检索历史偏好
- [ ] D32 总目标：持久化
- [ ] D32-学习：[LangGraph Memory](https://docs.langchain.com/oss/python/langgraph/memory) + [LangGraph Overview](https://docs.langchain.com/oss/python/langgraph/overview)（durable execution / persistence 视角）
- [ ] D32-实操：多会话持久化
- [ ] D32-产出：`lectures/lecture32/session_store.py`
- [ ] D32-验收：重启后可恢复
- [ ] D33 总目标：存储机制比较
- [ ] D33-学习：回顾 `langchain/L6_memory.ipynb` / `langgraph/L3-L4_cedges_memory.ipynb`，再看 [LangGraph Memory](https://docs.langchain.com/oss/python/langgraph/memory) + [LangGraph Overview](https://docs.langchain.com/oss/python/langgraph/overview)（回顾图级记忆与运行时持久化）
- [ ] D33-LearnGraph 补充：[LG 3.3 Multiple Schemas](https://www.learngraph.online/LearnGraph%201.X/module-3/3.3%20Multiple%20Schemas.html)（多 Schema 设计，辅助存储策略选择）
- [ ] D33-实操：选择你的记忆存储策略
- [ ] D33-产出：`lectures/lecture33/storage_selection.py`
- [ ] D33-验收：有吞吐与复杂度权衡
- [ ] D34 总目标：用户画像
- [ ] D34-学习：[Intro to LangGraph M5 L5: Build Agent with Long-Term Memory](https://academy.langchain.com/courses/intro-to-langgraph)
- [ ] D34-LearnGraph 补充：[LG 6.3 Memory Schema Profile](https://www.learngraph.online/LearnGraph%201.X/module-6-memory-system/6.3%20Memory%20Schema%20Profile.html) + [LG 6.4 Memory Schema Collection](https://www.learngraph.online/LearnGraph%201.X/module-6-memory-system/6.4%20Memory%20Schema%20Collection.html)（用户画像 Schema 设计）
- [ ] D34-实操：定义画像字段与更新策略
- [ ] D34-产出：`lectures/lecture34/profile_schema.py`
- [ ] D34-验收：含冲突与过期规则
- [ ] D35 总目标：周评测
- [ ] D35-学习：[Introduction to Agent Observability & Evaluations](https://academy.langchain.com/courses/intro-to-langsmith)（预习 playground / tracing / eval）+ 回顾本周笔记
- [ ] D35-实操：做记忆效果评测
- [ ] D35-产出：`lectures/lecture35/memory_eval_v1.py` + `docs/weekly/week05_summary.md`
- [ ] D35-验收：至少20条样本
- [ ] D35-里程碑：重启 Agent 后仍能记住上次对话内容

### 第6周：RAG 基础（D36-D42）

- [ ] D36 总目标：RAG概念与流程
- [ ] D36-学习：[LangChain Retrieval](https://docs.langchain.com/oss/python/langchain/retrieval) + [Build a RAG agent with LangChain](https://docs.langchain.com/oss/python/langchain/rag)
- [ ] D36-LearnGraph 补充：[LG 13.1 Agentic RAG 概述](https://www.learngraph.online/LearnGraph%201.X/module-13-agentic-rag/13.1%20Introduction.html) + [LG 13.2 Intro of RAG](https://www.learngraph.online/LearnGraph%201.X/module-13-agentic-rag/13.2%20Intro%20of%20RAG.html) + [LG 13.3 Design Mode](https://www.learngraph.online/LearnGraph%201.X/module-13-agentic-rag/13.3%20Design%20Mode.html)（RAG 概念+设计模式）
- [ ] D36-实操：画RAG流程
- [ ] D36-产出：`lectures/lecture36/rag_flow.mmd`
- [ ] D36-验收：包含切分检索生成评估
- [ ] D37 总目标：Naive RAG
- [ ] D37-学习：[Build a semantic search engine with LangChain](https://docs.langchain.com/oss/python/langchain/knowledge-base) + [LangChain Retrieval](https://docs.langchain.com/oss/python/langchain/retrieval)
- [ ] D37-实操：实现基础检索问答
- [ ] D37-产出：`lectures/lecture37/rag_v1.py`
- [ ] D37-验收：返回Top-k证据
- [ ] D38 总目标：Agentic RAG
- [ ] D38-学习：[Build a custom RAG agent with LangGraph](https://docs.langchain.com/oss/python/langgraph/agentic-rag) + HF Unit3 前2节：[Introduction](https://huggingface.co/learn/agents-course/en/unit3/agentic-rag/introduction) → [Agentic RAG](https://huggingface.co/learn/agents-course/en/unit3/agentic-rag/agentic-rag)
- [ ] D38-LearnGraph 补充：[LG 13.5 Agentic RAG Architecture](https://www.learngraph.online/LearnGraph%201.X/module-13-agentic-rag/13.5%20Agentic%20RAG%20Architecture.html) + [LG 13.7 LangGraph Agentic RAG](https://www.learngraph.online/LearnGraph%201.X/module-13-agentic-rag/13.7%20LangGraph%20Agentic%20RAG.html)（Agentic RAG 架构与 LangGraph 实现）
- [ ] D38-实操：引入"是否检索"决策
- [ ] D38-产出：`lectures/lecture38/agentic_rag_v1.py`
- [ ] D38-验收：可拒绝不必要检索
- [ ] D39 总目标：切分策略对比
- [ ] D39-学习：完成教程 [LangChain Retrieval](https://docs.langchain.com/oss/python/langchain/retrieval) + [Happy-LLM Chapter8](https://github.com/datawhalechina/happy-llm/tree/main/docs/chapter8)
- [ ] D39-实操：固定窗口 vs 语义分段
- [ ] D39-产出：`lectures/lecture39/chunking_compare.py`
- [ ] D39-验收：有召回差异数据
- [ ] D40 总目标：查询改写
- [ ] D40-学习：[Deep Research with LangGraph](https://academy.langchain.com/courses/deep-research-with-langgraph)（查询改写 / 搜索策略部分）+ HF Unit3 第3节：[Creating a RAG Tool for Guest Stories](https://huggingface.co/learn/agents-course/en/unit3/agentic-rag/invitees)
- [ ] D40-实操：实现query rewrite
- [ ] D40-产出：`lectures/lecture40/rewrite_module.py`
- [ ] D40-验收：长尾问题召回提升
- [ ] D41 总目标：引用输出
- [ ] D41-学习：[LlamaIndex Citation](https://docs.llamaindex.ai/en/stable/examples/query_engine/citation_query_engine/)（引用输出格式设计）
- [ ] D41-实操：答案中输出证据编号
- [ ] D41-产出：`lectures/lecture41/citation_format.py`
- [ ] D41-验收：每个结论可追溯
- [ ] D42 总目标：周集成 / 缓冲日
- [ ] D42-学习：HF Unit3 第4-6节（收尾）：[Building and Integrating Tools](https://huggingface.co/learn/agents-course/en/unit3/agentic-rag/tools) → [Creating Your Gala Agent](https://huggingface.co/learn/agents-course/en/unit3/agentic-rag/agent) → [Conclusion](https://huggingface.co/learn/agents-course/en/unit3/agentic-rag/conclusion) + [LangChain Retrieval](https://docs.langchain.com/oss/python/langchain/retrieval)
- [ ] D42-LearnGraph 补充：[LG 8.3 Code Assistant RAG+自我纠正](https://www.learngraph.online/LearnGraph%201.X/module-8-classic-examples/8.3%20Code%20Assistant.html)（RAG + 自我纠正案例）
- [ ] D42-实操：形成RAG v2
- [ ] D42-产出：`lectures/lecture42/patent_rag_demo.py` + `docs/weekly/week06_summary.md`
- [ ] D42-验收：20问人工评测完成
- [ ] D42-里程碑：输入专利问题 → 基于文档内容回答，返回文档片段 + 答案

### 第7周：RAG 进阶（重排与一致性）（D43-D49）

- [ ] D43 总目标：学习重排机制
- [ ] D43-学习：完成教程 [LlamaIndex Rerank](https://docs.llamaindex.ai/en/stable/module_guides/querying/node_postprocessors/node_postprocessors/) + [LangChain Retrieval](https://docs.langchain.com/oss/python/langchain/retrieval)
- [ ] D43-LearnGraph 补充：[LG 13.9 Self-Reflective RAG](https://www.learngraph.online/LearnGraph%201.X/module-13-agentic-rag/13.9%20Self-Reflective%20RAG.html)（自反思 RAG，补充重排后的质量自检机制）
- [ ] D43-实操：接入重排层
- [ ] D43-产出：`lectures/lecture43/rerank_v1.py`
- [ ] D43-验收：Top-3质量提升
- [ ] D44 总目标：引用一致性检查
- [ ] D44-学习：[LlamaIndex Citation](https://docs.llamaindex.ai/en/stable/examples/query_engine/citation_query_engine/) + [Introduction to Agent Observability & Evaluations](https://academy.langchain.com/courses/intro-to-langsmith)（用 tracing 验证引用）
- [ ] D44-实操：实现答案-证据对齐检查
- [ ] D44-产出：`lectures/lecture44/citation_checker.py`
- [ ] D44-验收：能发现错引案例
- [ ] D45 总目标：无证据拒答
- [ ] D45-学习：[LangChain Guardrails](https://docs.langchain.com/oss/python/langchain/guardrails) + [Deep Research with LangGraph](https://academy.langchain.com/courses/deep-research-with-langgraph)（用 scoping 思维设定拒答边界）
- [ ] D45-实操：加入拒答门槛
- [ ] D45-产出：`lectures/lecture45/refusal_policy.py`
- [ ] D45-验收：低证据回答显著下降
- [ ] D46 总目标：多跳问题
- [ ] D46-学习：[Deep Research with LangGraph](https://academy.langchain.com/courses/deep-research-with-langgraph)（多跳研究策略）+ 回顾 [HF Unit3: Agentic RAG](https://huggingface.co/learn/agents-course/en/unit3/agentic-rag/agentic-rag)（多跳场景复习）
- [ ] D46-LearnGraph 补充：[LG 13.10 Corrective RAG](https://www.learngraph.online/LearnGraph%201.X/module-13-agentic-rag/13.10%20Corrective%20RAG.html) + [LG 13.11 Adaptive RAG](https://www.learngraph.online/LearnGraph%201.X/module-13-agentic-rag/13.11%20Adaptive%20RAG.html)（纠正式+自适应 RAG）
- [ ] D46-实操：多跳检索流程
- [ ] D46-产出：`lectures/lecture46/multi_hop_rag.py`
- [ ] D46-验收：复杂问题可分步求解
- [ ] D47 总目标：错误归因
- [ ] D47-学习：[Introduction to Agent Observability & Evaluations](https://academy.langchain.com/courses/intro-to-langsmith)（用 run 类型分析错误归因）
- [ ] D47-实操：区分召回错/生成错
- [ ] D47-产出：`lectures/lecture47/error_taxonomy_v2.json`
- [ ] D47-验收：每类有改进动作
- [ ] D48 总目标：周集成优化
- [ ] D48-学习：回顾本周所有产出，整合重排和拒答
- [ ] D48-LearnGraph 补充：[LG 13.8 Qdrant Agentic RAG](https://www.learngraph.online/LearnGraph%201.X/module-13-agentic-rag/13.8%20Qdrant%20Agentic%20RAG.html)（向量数据库实战 RAG）
- [ ] D48-实操：整合重排和拒答
- [ ] D48-产出：`lectures/lecture48/rag_v3.py`
- [ ] D48-验收：准确率与可追溯率提升
- [ ] D49 总目标：周复盘
- [ ] D49-学习：[Introduction to Agent Observability & Evaluations](https://academy.langchain.com/courses/intro-to-langsmith)（datasets / evaluators）+ 回顾本周评测笔记
- [ ] D49-实操：跑一轮对比评测
- [ ] D49-产出：`lectures/lecture49/weekly_report.py` + `docs/weekly/week07_summary.md`
- [ ] D49-验收：给出下周迭代目标
- [ ] D49-里程碑：答案中每句话都有 [来源X] 引用标注

### 第8周：多 Agent 编排（D50-D56）

- [ ] D50 总目标：模式入门
- [ ] D50-学习：[LangChain Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent) + [Deep Agents](https://academy.langchain.com/courses/deep-agents-with-langgraph)
- [ ] D50-LearnGraph 补充：[LG 12.0 Multi-Agent 介绍](https://www.learngraph.online/LearnGraph%201.X/module-12-multi-agent-workflows/12.0%20Introduction.html)（Tool Calling vs Handoffs 两种核心模式）
- [ ] D50-实操：定义3角色
- [ ] D50-产出：`lectures/lecture50/role_contracts.json`
- [ ] D50-验收：输入输出职责清晰
- [ ] D51 总目标：Supervisor 模式
- [ ] D51-学习：[Build a personal assistant with subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents-personal-assistant) + [LangChain Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)
- [ ] D51-LearnGraph 补充：[LG 12.2 Supervisor Simple](https://www.learngraph.online/LearnGraph%201.X/module-12-multi-agent-workflows/12.2%20Supervisor%20Simple%20Example.html) + [LG 12.7 create_supervisor()](<https://www.learngraph.online/LearnGraph%201.X/module-12-multi-agent-workflows/12.7%20create_supervisor().html>) + [LG 12.9 Cheatsheet](https://www.learngraph.online/LearnGraph%201.X/module-12-multi-agent-workflows/12.9%20Supervisor%20Cheatsheet.html)
- [ ] D51-实操：实现调度Agent
- [ ] D51-产出：`lectures/lecture51/supervisor_v1.py`
- [ ] D51-验收：可按任务分发
- [ ] D52 总目标：Swarm 模式
- [ ] D52-学习：[LangChain Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent) + [LangGraph Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
- [ ] D52-LearnGraph 补充：[LG 12.3 Supervisor Complex](https://www.learngraph.online/LearnGraph%201.X/module-12-multi-agent-workflows/12.3%20Supervisor%20Complex%20Example.html) + [LG 12.4 Multi-Agent Collaboration](https://www.learngraph.online/LearnGraph%201.X/module-12-multi-agent-workflows/12.4%20Multi-Agent%20Collaboration.html)（复杂 Supervisor + 协作模式）
- [ ] D52-实操：实现并行协作
- [ ] D52-产出：`lectures/lecture52/swarm_demo.py`
- [ ] D52-验收：并行结果可汇总
- [ ] D53 总目标：Planner-Worker
- [ ] D53-学习：[Deep Research with LangGraph](https://academy.langchain.com/courses/deep-research-with-langgraph)（research supervisor / planner-worker）
- [ ] D53-LearnGraph 补充：[LG 12.5 Hierarchical Teams](https://www.learngraph.online/LearnGraph%201.X/module-12-multi-agent-workflows/12.5%20Hierarchical%20Teams.html) + [LG 12.6 Deep-Search-from-Scratch](https://www.learngraph.online/LearnGraph%201.X/module-12-multi-agent-workflows/12.6%20Deep-Search-from-Scratch.html)（层级团队+从零搭 Deep Search）
- [ ] D53-实操：搭建规划执行图
- [ ] D53-产出：`lectures/lecture53/planner_worker.py`
- [ ] D53-验收：计划可追踪
- [ ] D54 总目标：人工介入
- [ ] D54-学习：先跑本地官方 notebook `langchain/L9_HITL.ipynb` + `langgraph/L5_interrupt.ipynb`，再看 [LangGraph Interrupts](https://docs.langchain.com/oss/python/langgraph/human-in-the-loop) + [LangChain Human-in-the-loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop) + [Introduction to LangGraph](https://academy.langchain.com/courses/intro-to-langgraph)（HITL 模块）
- [ ] D54-LearnGraph 补充：[LG 4.1-4.5 HITL 全系列](https://www.learngraph.online/LearnGraph%201.X/module-4-human-in-the-loop/4.1%20Breakpoints.html)（Breakpoints/Dynamic/State Editing/Streaming Interruption/Time Travel）
- [ ] D54-实操：实现人工审批节点
- [ ] D54-产出：`lectures/lecture54/hitl_node.py`
- [ ] D54-验收：关键步骤可人工确认
- [ ] D55 总目标：多Agent整合 + Semantic Kernel Agent 对比 + LangGraph.js（TypeScript）对照
- [ ] D55-学习：[Deep Research with LangGraph](https://academy.langchain.com/courses/deep-research-with-langgraph) + [SK Agents](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/) + [LangGraph Essentials - TypeScript](https://academy.langchain.com/courses/quickstart-langgraph-essentials-typescript)
- [ ] D55-LearnGraph 补充：[LG 10.3 TradingAgent State](https://www.learngraph.online/LearnGraph%201.X/module-10-TradingAgent/10.3%20State.html) + [LG 10.5 研究员辩论](https://www.learngraph.online/LearnGraph%201.X/module-10-TradingAgent/10.5%20Analyst.html) + [LG 10.6 Graph 编排](https://www.learngraph.online/LearnGraph%201.X/module-10-TradingAgent/10.6%20Graph.html)（多角色辩论+Graph 编排，可迁移到专利多视角分析）
- [ ] D55-实操：整合3角色流程 + 用 SK Agent Framework 实现同等功能的最小原型，对比编排方式；**用 LangGraph.js（TypeScript）实现 Supervisor 模式（参考 [langgraph-101-ts Agent 03-05](https://github.com/langchain-ai/langgraph-101-ts)），对比 Python 版 LangGraph 的开发体验**
- [ ] D55-产出：`lectures/lecture55/multi_agent_v1.py` + `docs/comparisons/sk_agent_compare.md` + `docs/comparisons/langgraph_py_vs_ts.md`
- [ ] D55-验收：端到端可跑；SK 对比覆盖角色定义、调度机制、状态管理；**LangGraph.js 对比覆盖 State 定义（Zod vs Python TypedDict）、工具注册、Supervisor 路由**
- [ ] D56 总目标：鲁棒性加固 / 缓冲日
- [ ] D56-学习：[Deep Agents](https://academy.langchain.com/courses/deep-agents-with-langgraph)（完整 Agent 鲁棒性参考）+ [Introduction to Agent Observability & Evaluations](https://academy.langchain.com/courses/intro-to-langsmith)（tracing 变体）
- [ ] D56-实操：加超时/重试/降级
- [ ] D56-产出：`lectures/lecture56/robust_policy.py` + `docs/weekly/week08_summary.md`
- [ ] D56-验收：异常场景不中断
- [ ] D56-里程碑：Supervisor 分发任务给子 Agent，多角色协作可演示

### 第9周：工具生态与安全（D57-D63）

- [ ] D57 总目标：工具协议设计
- [ ] D57-学习：回看本地官方 notebook `langchain/L5_tools_with_mcp.ipynb`，再看 [LangChain MCP](https://docs.langchain.com/oss/python/langchain/mcp) + [Deep Research with LangGraph](https://academy.langchain.com/courses/deep-research-with-langgraph)（MCP 工具协议实战）
- [ ] D57-LearnGraph 补充：[LG 11.3 LangGraph MCP Integration](https://www.learngraph.online/LearnGraph%201.X/module-11-subgraph-mermaid-mcp-agent-node-tool/11.3%20LangGraph%20MCP%20Integration.html)（MCP 集成详细教程）
- [ ] D57-实操：设计专利检索工具契约
- [ ] D57-产出：`lectures/lecture57/tool_schema_v1.json`
- [ ] D57-验收：参数边界完整
- [ ] D58 总目标：参数校验与白名单
- [ ] D58-学习：回看本地官方 notebook `langgraph/L5_interrupt.ipynb`，再看 [LangGraph Interrupts](https://docs.langchain.com/oss/python/langgraph/human-in-the-loop) + [LangChain Guardrails](https://docs.langchain.com/oss/python/langchain/guardrails)（安全中断 / 校验思维）
- [ ] D58-LearnGraph 补充：[LG 11.4 Middleware](https://www.learngraph.online/LearnGraph%201.X/module-11-subgraph-mermaid-mcp-agent-node-tool/11.4%20Middleware.html) + [LG 11.5 Command](https://www.learngraph.online/LearnGraph%201.X/module-11-subgraph-mermaid-mcp-agent-node-tool/11.5%20Command.html)（中间件+动态路由，适合参数校验层）
- [ ] D58-实操：实现参数验证层
- [ ] D58-产出：`lectures/lecture58/validator.py`
- [ ] D58-验收：非法输入被拒绝
- [ ] D59 总目标：提示注入防护
- [ ] D59-学习：[OWASP LLM Security Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)（Prompt Injection 权威参考）
- [ ] D59-实操：构造10条攻击样本
- [ ] D59-产出：`lectures/lecture59/prompt_injection_set.json`
- [ ] D59-验收：防护策略可拦截
- [ ] D60 总目标：幂等与重入
- [ ] D60-学习：[LangGraph Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)（并行任务与状态收敛）+ [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [ ] D60-实操：设计任务ID与幂等策略
- [ ] D60-产出：`lectures/lecture60/idempotency_spec.py`
- [ ] D60-验收：重复请求结果一致
- [ ] D61 总目标：失败重试策略
- [ ] D61-学习：回看本地官方 notebook `langchain/L9_HITL.ipynb` + `langgraph/L5_interrupt.ipynb`，再看 [LangGraph Interrupts](https://docs.langchain.com/oss/python/langgraph/human-in-the-loop)（动态中断 / 重试策略参考）+ [LangChain Guardrails](https://docs.langchain.com/oss/python/langchain/guardrails)
- [ ] D61-实操：细化重试与熔断
- [ ] D61-产出：`lectures/lecture61/retry_policy.py`
- [ ] D61-验收：失败恢复时间缩短
- [ ] D62 总目标：周整合
- [ ] D62-学习：[HF Bonus Unit1](https://huggingface.co/learn/agents-course/en/bonus-unit1/introduction) + [Deep Agents](https://academy.langchain.com/courses/deep-agents-with-langgraph)（工具管理参考）
- [ ] D62-LearnGraph 补充：[LG 9.3 Deep Research MCP](https://www.learngraph.online/LearnGraph%201.X/module-9-deep-research/9.3%20MCP.html) + [LG 9.5 完整系统集成](https://www.learngraph.online/LearnGraph%201.X/module-9-deep-research/9.5%20Whole%20case.html)（Deep Research 完整案例）
- [ ] D62-实操：工具层接入主流程
- [ ] D62-产出：`lectures/lecture62/toolhub_v1.py`
- [ ] D62-验收：至少2个工具稳定运行
- [ ] D63 总目标：周复盘
- [ ] D63-学习：[Introduction to Agent Observability & Evaluations](https://academy.langchain.com/courses/intro-to-langsmith)（追踪对话故障）
- [ ] D63-实操：回看追踪与故障样例
- [ ] D63-产出：`lectures/lecture63/weekly_report.py` + `docs/weekly/week09_summary.md`
- [ ] D63-验收：列出3个高优先修复点
- [ ] D63-里程碑：注入攻击被拦截，非法参数被拒绝的终端输出

### 第10周：可观测与评测（D64-D70）

- [ ] D64 总目标：Trace 基础
- [ ] D64-学习：[Introduction to Agent Observability & Evaluations](https://academy.langchain.com/courses/intro-to-langsmith)（Tracing Basics + Types of Runs）
- [ ] D64-LearnGraph 补充：[LG 15.1 LangSmith](https://www.learngraph.online/LearnGraph%201.X/module-15-langsmith-langfuse/15.1%20LangSmith.html) + [LG 15.2 LangFuse](https://www.learngraph.online/LearnGraph%201.X/module-15-langsmith-langfuse/15.2%20LangFuse.html)（LangSmith/LangFuse 对比与实操）
- [ ] D64-实操：接入基础追踪
- [ ] D64-产出：`lectures/lecture64/trace_v1.py`
- [ ] D64-验收：每步输入输出可见
- [ ] D65 总目标：评测集构建
- [ ] D65-学习：[Introduction to Agent Observability & Evaluations](https://academy.langchain.com/courses/intro-to-langsmith)（Datasets）
- [ ] D65-实操：构建30条专利问题集
- [ ] D65-产出：`lectures/lecture65/eval_dataset_v1.json`
- [ ] D65-验收：覆盖简单/复杂/异常问题
- [ ] D66 总目标：指标定义
- [ ] D66-学习：[Introduction to Agent Observability & Evaluations](https://academy.langchain.com/courses/intro-to-langsmith)（Evaluators）
- [ ] D66-实操：定义准确率、引用率、延迟、成本
- [ ] D66-产出：`lectures/lecture66/metrics_spec.py`
- [ ] D66-验收：指标可自动计算
- [ ] D67 总目标：自动评测
- [ ] D67-学习：[Introduction to Agent Observability & Evaluations](https://academy.langchain.com/courses/intro-to-langsmith)（Experiments + Analyzing Results）
- [ ] D67-实操：写评测脚本
- [ ] D67-产出：`lectures/lecture67/eval_runner.py`
- [ ] D67-验收：一键产出报告
- [ ] D68 总目标：回归基线
- [ ] D68-学习：[Introduction to Agent Observability & Evaluations](https://academy.langchain.com/courses/intro-to-langsmith)（Pairwise Experiments / 基线对比）
- [ ] D68-LearnGraph 补充：[LG 8.1 Agent Simulation Evaluation](https://www.learngraph.online/LearnGraph%201.X/module-8-classic-examples/8.1%20Agent%20Simulation%20Evaluation.html) + [LG 8.2 Information Gathering Prompting](https://www.learngraph.online/LearnGraph%201.X/module-8-classic-examples/8.2%20Information%20Gathering%20Prompting.html)（Agent 仿真评测+信息收集案例）
- [ ] D68-实操：建立基线版本
- [ ] D68-产出：`lectures/lecture68/baseline_report.py`
- [ ] D68-验收：后续可对比
- [ ] D69 总目标：问题修复
- [ ] D69-学习：[Introduction to Agent Observability & Evaluations](https://academy.langchain.com/courses/intro-to-langsmith)（根据评测修 prompt）
- [ ] D69-实操：修复前2个关键问题
- [ ] D69-产出：`lectures/lecture69/fix_log.md`
- [ ] D69-验收：指标提升可见
- [ ] D70 总目标：周复盘 / 缓冲日
- [ ] D70-学习：[Introduction to Agent Observability & Evaluations](https://academy.langchain.com/courses/intro-to-langsmith)（Summary Evaluators）+ 回顾本周笔记
- [ ] D70-实操：整理评测结论
- [ ] D70-产出：`lectures/lecture70/weekly_report.py` + `docs/weekly/week10_summary.md`
- [ ] D70-验收：明确下周优化优先级
- [ ] D70-里程碑：30 条问题的自动评测报告，一键生成

### 第11周：性能优化与部署意识（D71-D77）

- [ ] D71 总目标：性能预算
- [ ] D71-学习：[Introduction to Agent Observability & Evaluations](https://academy.langchain.com/courses/intro-to-langsmith)（Monitoring / 性能预算）
- [ ] D71-实操：定义延迟与成本预算
- [ ] D71-产出：`lectures/lecture71/budget.json`
- [ ] D71-验收：每步有配额
- [ ] D72 总目标：缓存策略
- [ ] D72-学习：[Introduction to Agent Observability & Evaluations](https://academy.langchain.com/courses/intro-to-langsmith)（Filtering / 缓存思维）
- [ ] D72-实操：加查询级缓存
- [ ] D72-产出：`lectures/lecture72/cache_policy.py`
- [ ] D72-验收：命中率可统计
- [ ] D73 总目标：并行化
- [ ] D73-学习：[LangGraph Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents) + [LangGraph Subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)
- [ ] D73-LearnGraph 补充：[LG 5.1 Parallelization](https://www.learngraph.online/LearnGraph%201.X/module-5-advanced-patterns/5.1%20Parallelization.html)（并行化深度解读）
- [ ] D73-实操：并行可并发节点
- [ ] D73-产出：`lectures/lecture73/parallel_graph.py`
- [ ] D73-验收：总耗时下降
- [ ] D74 总目标：模型降级
- [ ] D74-学习：[LangGraph Subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)（子图隔离 / 降级策略）+ [LangGraph Functional API](https://docs.langchain.com/oss/python/langgraph/functional-api)
- [ ] D74-LearnGraph 补充：[LG 11.0.1 Function→DeepAgent 抽象层次](https://www.learngraph.online/LearnGraph%201.X/module-11-subgraph-mermaid-mcp-agent-node-tool/11.0.1%20Function-tool-Node-Agent-SubAgent-Deepagent.html) + [LG 11.1 Loop Patterns](https://www.learngraph.online/LearnGraph%201.X/module-11-subgraph-mermaid-mcp-agent-node-tool/11.1%20LangGraph%20Loop%20Patterns.html)（辅助降级策略设计）
- [ ] D74-实操：设计fallback模型
- [ ] D74-产出：`lectures/lecture74/fallback_spec.py`
- [ ] D74-验收：主模型失败可自动切换
- [ ] D75 总目标：调试工具
- [ ] D75-学习：[LangGraph Studio](https://docs.langchain.com/oss/python/langgraph/studio) + [Introduction to Agent Observability & Evaluations](https://academy.langchain.com/courses/intro-to-langsmith)（Dashboards）
- [ ] D75-LearnGraph 补充：[LG 11.2 Mermaid 可视化](https://www.learngraph.online/LearnGraph%201.X/module-11-subgraph-mermaid-mcp-agent-node-tool/11.2%20Visualizing%20with%20Mermaid.html)（Mermaid 图可视化调试）
- [ ] D75-实操：梳理图调试流程
- [ ] D75-产出：`lectures/lecture75/debug_checklist.json`
- [ ] D75-验收：可定位失败节点
- [ ] D76 总目标：部署认知
- [ ] D76-学习：[LangChain Deploy](https://docs.langchain.com/oss/python/langchain/deploy) + [Introduction to LangGraph](https://academy.langchain.com/courses/intro-to-langgraph)（deployment 模块）
- [ ] D76-LearnGraph 补充：[LG 7.1-7.4 生产部署](https://www.learngraph.online/LearnGraph%201.X/module-7-production-deployment/7.1%20Creating%20Deployment.html)（Creating/Connecting/Double-texting/Assistants）
- [ ] D76-实操：写部署要点
- [ ] D76-产出：`lectures/lecture76/deploy_note.md`
- [ ] D76-验收：明确日志、扩缩容、健康检查
- [ ] D77 总目标：周集成
- [ ] D77-学习：[Introduction to Agent Observability & Evaluations](https://academy.langchain.com/courses/intro-to-langsmith)（Online Evaluation + Automations）
- [ ] D77-实操：优化后回归评测
- [ ] D77-产出：`lectures/lecture77/optimization_compare.py` + `docs/weekly/week11_summary.md`
- [ ] D77-验收：至少两项指标改善
- [ ] D77-里程碑：优化前后延迟/成本对比表，至少两项指标改善

### 第12周：Capstone 收尾（D78-D84）

- [ ] D78 总目标：定义最终项目验收
- [ ] D78-学习：[HF Unit4 - Final Project](https://huggingface.co/learn/agents-course/en/unit4/introduction) + [Deep Agents](https://academy.langchain.com/courses/deep-agents-with-langgraph)（完整 Agent 参考）
- [ ] D78-LearnGraph 补充：[LG 14.0 Thinking in LangGraph](https://www.learngraph.online/LearnGraph%201.X/module-14-deep-agent/14.0%20Introduction.html)（五步法 + 5 种工作流模式总结，系统回顾架构反思）
- [ ] D78-实操：写Capstone验收清单
- [ ] D78-产出：`lectures/lecture78/acceptance_checklist.json`
- [ ] D78-验收：包含功能、质量、性能、安全
- [ ] D79 总目标：修复高优先问题1
- [ ] D79-学习：回顾 W10 评测报告，针对性修复
- [ ] D79-实操：修复并回归
- [ ] D79-产出：`lectures/lecture79/fix_01.py`
- [ ] D79-验收：对应指标恢复
- [ ] D80 总目标：修复高优先问题2
- [ ] D80-学习：[Introduction to Agent Observability & Evaluations](https://academy.langchain.com/courses/intro-to-langsmith)（User Feedback）
- [ ] D80-实操：修复并回归
- [ ] D80-产出：`lectures/lecture80/fix_02.py`
- [ ] D80-验收：错误率下降
- [ ] D81 总目标：修复高优先问题3
- [ ] D81-学习：[Introduction to Agent Observability & Evaluations](https://academy.langchain.com/courses/intro-to-langsmith)（Annotation Queues）
- [ ] D81-实操：修复并回归
- [ ] D81-产出：`lectures/lecture81/fix_03.py`
- [ ] D81-验收：复杂任务成功率提升
- [ ] D82 总目标：文档化与交付
- [ ] D82-学习：[HF Unit4 - Final Project](https://huggingface.co/learn/agents-course/en/unit4/introduction) + [Introduction to LangGraph](https://academy.langchain.com/courses/intro-to-langgraph)（deployment / assistants 收尾）
- [ ] D82-实操：整理架构、流程、评测文档
- [ ] D82-产出：`lectures/lecture82/project_doc_v1.md`
- [ ] D82-验收：新人可按文档复现
- [ ] D83 总目标：全链路彩排
- [ ] D83-学习：[Deep Agents](https://academy.langchain.com/courses/deep-agents-with-langgraph) + [LangGraph Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)（完整示例回顾）
- [ ] D83-LearnGraph 补充：[LG 9.5 Deep Research 完整系统](https://www.learngraph.online/LearnGraph%201.X/module-9-deep-research/9.5%20Whole%20case.html) + [LG 10.7 TradingAgent 端到端](https://www.learngraph.online/LearnGraph%201.X/module-10-TradingAgent/10.7%20Data%20flow.html)（参考两个完整端到端案例）
- [ ] D83-实操：全流程演练
- [ ] D83-产出：`lectures/lecture83/rehearsal_report.md`
- [ ] D83-验收：端到端稳定
- [ ] D84 总目标：最终复盘与下一阶段规划 / 缓冲日
- [ ] D84-学习：[HF Unit4 - Final Project](https://huggingface.co/learn/agents-course/en/unit4/introduction) + 回顾所有周笔记
- [ ] D84-实操：总结3个月收获与下一步
- [ ] D84-产出：`lectures/lecture84/roadmap_v2.md` + `docs/weekly/week12_summary.md`
- [ ] D84-验收：给出后续90天目标与优先级
- [ ] D84-里程碑：端到端 demo 录屏，完整专利助手可演示

---

## 3. 每周固定复盘模板（周日）

- 本周完成：
  - 哪些天按计划完成
  - 哪些任务延期
- 指标变化：
  - 准确率
  - 引用可追溯率
  - 平均延迟
  - 成本
- 问题清单：
  - P0（必须修）
  - P1（应该修）
  - P2（可优化）
- 下周目标：
  - 只保留 3 个最关键目标

---

## 4. 执行建议

### 代码先行原则

**核心理念：先跑代码看到结果，再回头看教程。**

每天推荐执行顺序：

1. **速效开局（5-10 分钟）**：先跑一段代码，看到输出。哪怕只是改一个参数重新跑。
2. **带着问题看教程（15-30 分钟）**：刚才代码里不懂的地方，现在看教程会"啊原来如此"。
3. **扩展实操（15-30 分钟）**：把速效代码扩展为当天产出。
4. **验收截图**：终端输出截图保存到 `screenshots/`。

**学不进去的时候怎么办：**

- 只有 10 分钟 → 只做"速效开局"，跑一段代码就算完成
- 遇到数学公式 → 跳过公式，只看文字描述和图示
- 某天完全不想学 → 打开昨天的脚本，改一个参数重新跑，看看输出变化
- 关键是不断链，连续性比强度重要得多

### 产出升级规则

将抽象产出转为可运行产出，按以下规则转换：

| 原产出类型    | 转换方式                                                       | 示例                                                       |
| ------------- | -------------------------------------------------------------- | ---------------------------------------------------------- |
| XX清单/XX表   | 改为 Python dict/JSON 文件 + 打印脚本                          | "错误分类表" → `lectures/lecture47/error_taxonomy_v2.json` |
| XX流程图      | 改为 Mermaid 图 + 用 CLI 渲染为 PNG                            | "重试流程图" → `lectures/lecture11/retry_flow.mmd`         |
| XX规范/XX规则 | 改为 pytest 断言                                               | "session规则" → `lectures/lecture29/test_session_rules.py` |
| XX对比笔记    | 改为对比脚本（同一输入跑两个实现，打印对比表）                 | "对比笔记" → `lectures/lecture27/compare_plan_modes.py`    |
| XX草案/XX设计 | 改为可运行的 skeleton 代码（函数签名 + TODO + 1个能跑的用例）  | "state草案" → `lectures/lecture22/state_draft.py`          |
| 周报          | 改为自动生成周报的脚本（统计本周代码行数、文件数、测试通过数） | "周报" → `lectures/lecture49/weekly_report.py`             |

### 时间弹性

- 如果某天时间只有30分钟：优先"速效开局+实操"，把教程阅读挪到周末。
- 如果某周延期：不要跳周，先补齐关键产物再进入下一周。
- 每4周做一次"减法重构"：删除无效流程和重复实验。

### 缓冲天策略

- 偶数周的最后一天（D14、D28、D42、D56、D70、D84）标注为「缓冲日」。
- 如果该双周内有延期任务，优先用缓冲日补齐，而非跳过。
- 如果没有延期，缓冲日正常执行原计划内容。
- 总共 6 个缓冲日，足以应对 1-2 周级别的突发延期。

### 练习环境方案

**原则：所有学习代码在本仓库内管理，依赖由根目录 `pyproject.toml` 统一管理（uv），每天的产出放在对应的 `lectures/lectureXX/` 目录。**

#### 目录结构

```
agent-learning/                       # 本仓库根目录（git repo）
├── pyproject.toml                    # uv 管理的全局依赖
├── .env                              # API Key
├── .gitignore
├── main.py                           # 项目入口
├── AGENT_LEARNING.md                 # 本学习计划
├── README.md
│
├── lectures/                         # 所有学习产出
│   ├── lecture01/                    # D1: 第一次对话
│   │   └── day01_first_chat.py
│   ├── lecture02/                    # D2: Streaming
│   │   └── day02_streaming.py
│   ├── ...
│   └── lecture84/                    # D84: 最终复盘
│       └── roadmap_v2.md
│
├── screenshots/                      # 验收截图
│   ├── day01.png
│   └── ...
│
├── shared/                           # 跨 lecture 共享代码/数据
│   ├── utils.py                      # 通用工具函数
│   ├── config.py                     # 共享配置（模型选择等）
│   └── test_data/                    # 共享测试数据
│       └── sample_patents.json       # 模拟专利数据
│
└── docs/                             # 学习笔记与周报
    ├── weekly/                       # 周总结
    │   ├── week01_summary.md
    │   └── ...
    └── comparisons/                  # 框架对比文档
        ├── sk_vs_langchain.md
        └── langgraph_py_vs_ts.md
```

#### lecture 目录规范

每个 `lectures/lectureXX/` 目录至少包含：

- 主产出文件（`.py` / `.json` / `.mmd` / `.md`）
- `README.md`（可选，记录当天学习要点和运行说明）

命名规则：

- 代码文件：snake_case，与产出名一致
- 笔记文件：`README.md` 或 `notes.md`
- 测试文件：`test_` 前缀

#### 运行方式

```bash
# 运行某个 lecture 的脚本（优先 day01_first_chat.py，其次目录中的首个 .py）
./run lecture01

# 运行某个 lecture 的测试（优先 test_cases.py，其次 test_*.py）
./test lecture19

# 可选：通过 make 调用
make run lecture01
make test lecture19
# 或
make run L=lecture01
make test L=lecture19
```

#### 阶段工具选择

| 阶段                     | 推荐工具                     | 理由                                   |
| ------------------------ | ---------------------------- | -------------------------------------- |
| 第 1-2 周（概念打底）    | **Ollama（本地模型）**       | 不需要 API Key，完全免费，跑通概念即可 |
| 第 3-4 周（工程化）      | **Ollama + Gemini 免费 API** | LangChain/SK 对接 Ollama 很简单        |
| 第 5-7 周（Memory/RAG）  | **Gemini 免费 API / Groq**   | RAG 需要稍强模型                       |
| 第 8-9 周（多 Agent）    | **Gemini / Groq**            | 多 Agent 需要稳定的工具调用能力        |
| 第 10-12 周（评测/优化） | **Gemini / Groq**            | 评测需要可重复的 API 调用              |

#### Ollama 快速上手

```bash
# 安装（macOS）
brew install ollama

# 启动并下载模型
ollama run llama3.2        # Meta Llama 3.2（推荐入门）
ollama run qwen2.5         # 通义千问 2.5（中文更好）
ollama run mistral         # Mistral（轻量快速）

# LangChain 对接（已在 pyproject.toml 中配置）
uv add langchain-ollama
```

```python
from langchain_ollama import ChatOllama
llm = ChatOllama(model="llama3.2")
response = llm.invoke("什么是 ReAct Agent？")
```

#### 免费 API 注册

| 服务              | 免费额度                  | 注册链接                               |
| ----------------- | ------------------------- | -------------------------------------- |
| **Google Gemini** | 每分钟 15 次（免费 tier） | https://aistudio.google.com/           |
| **Groq**          | 慷慨免费额度，速度极快    | https://console.groq.com/              |
| **HuggingFace**   | 免费推理 API              | https://huggingface.co/settings/tokens |

```python
# LangChain + Gemini（免费）
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
```

#### Semantic Kernel + Ollama

```python
# SK 也可以对接本地 Ollama（通过 OpenAI 兼容接口）
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion

kernel = sk.Kernel()
kernel.add_service(OpenAIChatCompletion(
    ai_model_id="llama3.2",
    async_client=None,  # 使用 Ollama 的 OpenAI 兼容端点
))
```

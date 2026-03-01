"""
LangGraph 邮件处理 Agent 完整实现

来源：LangGraph 官方文档 "Thinking in LangGraph"
https://langchain-ai.github.io/langgraph/concepts/thinking-in-langgraph/

功能概述:
  1. 读取邮件 → 2. LLM 分类意图 → 3. 根据分类路由到不同节点:
     - billing/critical → 人工审核
     - question/feature → 搜索知识库 → 起草回复
     - bug → 创建工单 → 起草回复
     - 其他 → 直接起草回复
  4. 根据紧急程度判断是否需要人工审核
  5. 发送邮件回复
"""

from typing import Literal, TypedDict

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, RetryPolicy, interrupt

# ============================================================
# 第一部分：State 定义（共享状态）
# ============================================================


class EmailClassification(TypedDict):
    """邮件分类结果的结构化定义"""

    intent: Literal["question", "bug", "billing", "feature", "complex"]
    urgency: Literal["low", "medium", "high", "critical"]
    topic: str
    summary: str


class EmailAgentState(TypedDict):
    """邮件 Agent 的共享状态

    设计原则：只存储原始数据，不存储格式化后的文本。
    Prompt 的格式化在节点内部按需完成。
    """

    # 原始邮件数据
    email_content: str
    sender_email: str
    email_id: str

    # 分类结果
    classification: EmailClassification | None

    # 搜索/API 的原始结果
    search_results: list[str] | None  # 原始文档片段列表
    customer_history: dict | None  # 来自 CRM 的原始客户数据

    # 生成的内容
    draft_response: str | None
    messages: list[str] | None


# ============================================================
# 第二部分：初始化 LLM
# ============================================================

# 使用本地 Ollama 模型（项目 pyproject.toml 中配置的 langchain-ollama）
# 请确保本地已运行: ollama run qwen2.5:7b
llm = ChatOllama(model="qwen2.5:7b", temperature=0)


# ============================================================
# 第三部分：节点函数实现
# ============================================================


# --- 读取邮件节点 ---
def read_email(state: EmailAgentState) -> dict:
    """提取并解析邮件内容

    在生产环境中，这里应连接到实际的邮件服务（如 Gmail API、IMAP 等）。
    """
    return {"messages": [HumanMessage(content=f"Processing email: {state['email_content']}")]}


# --- 意图分类节点 ---
def classify_intent(
    state: EmailAgentState,
) -> Command[Literal["search_documentation", "human_review", "draft_response", "bug_tracking"]]:
    """使用 LLM 对邮件进行意图和紧急程度分类，然后路由到对应节点

    路由规则：
      - billing 或 critical → human_review（需要人工审核）
      - question / feature → search_documentation（先搜索知识库）
      - bug → bug_tracking（创建工单）
      - 其他 → draft_response（直接起草回复）
    """
    # 创建返回 EmailClassification 结构化输出的 LLM
    structured_llm = llm.with_structured_output(EmailClassification)

    # 按需格式化 prompt，不存储在 state 中
    classification_prompt = f"""
    Analyze this customer email and classify it:

    Email: {state["email_content"]}
    From: {state["sender_email"]}

    Provide classification including intent, urgency, topic, and summary.
    """

    # 获取结构化响应（直接返回 dict）
    classification = structured_llm.invoke(classification_prompt)
    print(f"🏷️  分类结果: intent={classification['intent']}, urgency={classification['urgency']}")
    print(
        f"   topic={classification.get('topic', '')}, summary={classification.get('summary', '')}"
    )

    # 根据分类结果决定下一个节点
    if classification["intent"] == "billing" or classification["urgency"] == "critical":
        goto = "human_review"
    elif classification["intent"] in ["question", "feature"]:
        goto = "search_documentation"
    elif classification["intent"] == "bug":
        goto = "bug_tracking"
    else:
        goto = "draft_response"

    print(f"🔀 路由 → {goto}")

    # 将分类结果存入 state
    return Command(update={"classification": classification}, goto=goto)


# --- 知识库搜索节点 ---
def search_documentation(state: EmailAgentState) -> Command[Literal["draft_response"]]:
    """搜索知识库获取相关信息

    在生产环境中，这里应连接到实际的向量数据库或搜索 API。
    """
    print("🔍 进入 search_documentation 节点")
    # 从分类结果构建搜索查询
    classification = state.get("classification", {})
    query = f"{classification.get('intent', '')} {classification.get('topic', '')}"
    print(f"   搜索关键词: {query}")

    try:
        # 这里实现你的搜索逻辑
        # 存储原始搜索结果，而非格式化后的文本
        search_results = [
            "Reset password via Settings > Security > Change Password",
            "Password must be at least 12 characters",
            "Include uppercase, lowercase, numbers, and symbols",
        ]
    except Exception as e:
        # 对于可恢复的搜索错误，存储错误信息并继续
        search_results = [f"Search temporarily unavailable: {str(e)}"]

    return Command(
        update={"search_results": search_results},  # 存储原始结果或错误信息
        goto="draft_response",
    )


# --- Bug 追踪节点 ---
def bug_tracking(state: EmailAgentState) -> Command[Literal["draft_response"]]:
    """创建或更新 Bug 跟踪工单

    在生产环境中，这里应连接到 JIRA、Linear 等工单系统的 API。
    """
    print("🐛 进入 bug_tracking 节点")
    # 通过 API 创建工单
    ticket_id = "BUG-12345"  # 实际应通过 API 创建
    print(f"   创建工单: {ticket_id}")

    return Command(
        update={
            "search_results": [f"Bug ticket {ticket_id} created"],
        },
        goto="draft_response",
    )


# --- 起草回复节点 ---
def draft_response(
    state: EmailAgentState,
) -> Command[Literal["human_review", "send_reply"]]:
    """使用上下文信息生成回复草稿，并根据质量/紧急程度决定是否需要人工审核"""

    classification = state.get("classification", {})

    # 按需从原始 state 数据格式化上下文
    context_sections = []

    if state.get("search_results"):
        # 将搜索结果格式化到 prompt 中
        formatted_docs = "\n".join([f"- {doc}" for doc in state["search_results"]])
        context_sections.append(f"Relevant documentation:\n{formatted_docs}")

    if state.get("customer_history"):
        # 将客户数据格式化到 prompt 中
        context_sections.append(
            f"Customer tier: {state['customer_history'].get('tier', 'standard')}"
        )

    # 构建包含格式化上下文的 prompt
    draft_prompt = f"""
    Draft a response to this customer email:
    {state["email_content"]}

    Email intent: {classification.get("intent", "unknown")}
    Urgency level: {classification.get("urgency", "medium")}

    {chr(10).join(context_sections)}

    Guidelines:
    - Be professional and helpful
    - Address their specific concern
    - Use the provided documentation when relevant
    """

    response = llm.invoke(draft_prompt)

    # 根据紧急程度和意图判断是否需要人工审核
    needs_review = (
        classification.get("urgency") in ["high", "critical"]
        or classification.get("intent") == "complex"
    )

    # 路由到对应的下一个节点
    goto = "human_review" if needs_review else "send_reply"

    return Command(
        update={"draft_response": response.content},  # 只存储原始响应内容
        goto=goto,
    )


# --- 人工审核节点 ---
def human_review(state: EmailAgentState) -> Command[Literal["send_reply", END]]:
    """使用 interrupt 暂停执行，等待人工审核后根据决策路由

    interrupt() 会暂停图的执行，保存当前状态到 checkpointer，
    直到外部提供 Command(resume=...) 来恢复执行。
    """
    classification = state.get("classification", {})

    # interrupt() 必须放在最前面 —— 恢复执行时，它之前的代码会被重新执行
    human_decision = interrupt(
        {
            "email_id": state.get("email_id", ""),
            "original_email": state.get("email_content", ""),
            "draft_response": state.get("draft_response", ""),
            "urgency": classification.get("urgency"),
            "intent": classification.get("intent"),
            "action": "Please review and approve/edit this response",
        }
    )

    # 处理人工审核结果
    if human_decision.get("approved"):
        return Command(
            update={
                "draft_response": human_decision.get(
                    "edited_response", state.get("draft_response", "")
                )
            },
            goto="send_reply",
        )
    else:
        # 拒绝意味着人工将直接处理
        return Command(update={}, goto=END)


# --- 发送回复节点 ---
def send_reply(state: EmailAgentState) -> dict:
    """发送邮件回复

    在生产环境中，这里应连接到实际的邮件发送服务。
    """
    print(f"📨 发送回复:\n{state['draft_response']}")
    return {}


# ============================================================
# 第四部分：构建图（Graph）
# ============================================================


def build_email_agent():
    """构建并编译邮件处理 Agent 图

    返回编译后的可执行应用实例。
    """
    # 创建状态图
    workflow = StateGraph(EmailAgentState)

    # 添加节点
    workflow.add_node("read_email", read_email)
    workflow.add_node("classify_intent", classify_intent)

    # 为可能出现瞬时故障的节点添加重试策略
    workflow.add_node(
        "search_documentation", search_documentation, retry_policy=RetryPolicy(max_attempts=3)
    )
    workflow.add_node("bug_tracking", bug_tracking)
    workflow.add_node("draft_response", draft_response)
    workflow.add_node("human_review", human_review)
    workflow.add_node("send_reply", send_reply)

    # 添加基本边（只需少量边，因为路由逻辑在节点内部通过 Command 完成）
    workflow.add_edge(START, "read_email")
    workflow.add_edge("read_email", "classify_intent")
    workflow.add_edge("send_reply", END)

    # 使用 MemorySaver 作为 checkpointer（支持 interrupt 和状态持久化）
    # 生产环境建议使用 PostgresSaver 等持久化存储
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    return app


# ============================================================
# 第五部分：运行测试
# ============================================================

if __name__ == "__main__":
    # 构建 Agent
    app = build_email_agent()

    # 准备测试数据 —— 一个紧急的账单问题
    initial_state = {
        "email_content": "I was charged twice for my subscription! This is urgent!",
        # "email_content": "Bug report. The login page crashes on Safari! This is urgent!",
        # "email_content": "Can you add dark mode to the app",
        "sender_email": "customer@example.com",
        "email_id": "email_123",
        "messages": [],
    }

    # 使用 thread_id 进行持久化（同一个 thread_id 的所有状态会保存在一起）
    config = {"configurable": {"thread_id": "customer_123"}}

    print("=" * 60)
    print("🚀 启动邮件处理 Agent")
    print("=" * 60)
    print(f"📧 邮件内容: {initial_state['email_content']}")
    print(f"👤 发件人: {initial_state['sender_email']}")
    print("-" * 60)

    # 第一次调用 —— 根据邮件内容，可能在 human_review 处暂停，也可能直接发送
    result = app.invoke(initial_state, config)

    # 检查是否被打断（需要人工审核）
    if "__interrupt__" in result:
        # 路径 A：紧急/复杂邮件 → 经过了 human_review → interrupt() 暂停
        print(f"\n⏸️  人工审核中断: {result['__interrupt__']}")

        # 模拟人工审核 —— 批准并编辑回复内容
        print("\n" + "-" * 60)
        print("✅ 人工审核：批准并修改回复内容")
        print("-" * 60)

        human_response = Command(
            resume={
                "approved": True,
                "edited_response": (
                    "We sincerely apologize for the double charge. "
                    "I've initiated an immediate refund that will appear "
                    "in your account within 3-5 business days."
                ),
            }
        )

        # 恢复执行 —— 从 interrupt 暂停的地方继续
        final_result = app.invoke(human_response, config)
        print("\n✉️  邮件发送成功！")
    else:
        # 路径 B：普通邮件 → 没有经过 human_review → 全自动发送完毕
        print("\n✅ 邮件为普通问题，已全自动处理并发送，无需人工审核。")

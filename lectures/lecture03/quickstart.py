# Step 1: 定义工具和模型

from langchain.tools import tool
from langchain_ollama import ChatOllama

# 使用本地 Ollama 模型（请确保已运行 ollama run qwen2.5:7b）
model = ChatOllama(model="qwen2.5:7b", temperature=0)


# Define tools
@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a * b


@tool
def add(a: int, b: int) -> int:
    """Adds `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a + b


@tool
def divide(a: int, b: int) -> float:
    """Divide `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a / b


# Augment the LLM with tools
tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)

# Step 2: 定义状态

import operator
from typing import Annotated

from langchain.messages import AnyMessage
from typing_extensions import TypedDict


class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int


# Step 3: 定义模型节点
from langchain.messages import SystemMessage


def llm_call(state: dict):
    """LLM 决定是否调用工具"""

    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content="You are a helpful assistant tasked with performing arithmetic on a set of inputs."
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# Step 4: 定义工具节点

from langchain.messages import ToolMessage


def tool_node(state: dict):
    """执行工具调用"""

    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}


# Step 5: 定义是否继续的判断逻辑

from typing import Literal

from langgraph.graph import END, START, StateGraph


# 条件边函数：根据 LLM 是否发起工具调用来决定路由方向
def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """判断是否继续循环：LLM 发起了工具调用则继续，否则结束"""

    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return "tool_node"

    # Otherwise, we stop (reply to the user)
    return END


# Step 6: 构建 Agent

# 构建工作流
agent_builder = StateGraph(MessagesState)

# 添加节点
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

# 添加边连接节点
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
agent_builder.add_edge("tool_node", "llm_call")

# 编译 Agent
agent = agent_builder.compile()


# 保存 Agent 状态图
try:
    png_data = agent.get_graph(xray=True).draw_mermaid_png()
    with open("quickstart_graph.png", "wb") as f:
        f.write(png_data)
    print("状态图已保存为 quickstart_graph.png")
except Exception as e:
    print(f"保存图片失败: {e}")

# 调用 Agent
from langchain.messages import HumanMessage

messages = [HumanMessage(content="3乘以4再加5")]
messages = agent.invoke({"messages": messages})
for m in messages["messages"]:
    m.pretty_print()

from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent


@tool
def add(a: int, b: int) -> int:
    """两个数相加"""
    return a + b


@tool
def multiply(a: int, b: int) -> int:
    """两个数相乘"""
    return a * b


def main():
    print("初始化 qwen2.5:7b 模型...")
    # 请确保您本地已经运行 ollama run qwen2.5:7b
    llm = ChatOllama(model="qwen2.5:7b", temperature=0)

    # 将工具列表提供给 Agent
    tools = [add, multiply]

    # 使用 LangGraph 提供的预构建 ReAct Agent (Tool Calling Agent)
    print("构建 Tool Calling Agent...")
    agent_executor = create_react_agent(llm, tools)

    try:
        print("\n正在保存 Agent 的状态图至 agent_graph.png...")
        png_data = agent_executor.get_graph().draw_mermaid_png()
        with open("agent_graph.png", "wb") as f:
            f.write(png_data)
        print("状态图已成功保存为 agent_graph.png")
    except Exception as e:
        print(f"保存图片失败: {e}")

    query = "3乘以4再加5等于多少？"
    print(f"\n用户提问: {query}\n")
    print("思考与执行过程:\n" + "-" * 40)

    # 运行Agent
    response = agent_executor.invoke({"messages": [("user", query)]})

    # 打印消息记录
    for msg in response["messages"]:
        msg.pretty_print()


if __name__ == "__main__":
    main()

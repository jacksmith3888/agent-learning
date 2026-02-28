"""
Day 4 — 专利助手 v0.1
====================
目标：让 AI 调用你设计的「专利搜索」工具，并具备输入校验能力。

核心能力：
  1. 专利关键词搜索（模拟数据）
  2. 参数校验：关键词不能为空、长度限制（2-50字符）
  3. 保留 D3 的加法和乘法工具，展示多工具自主选择

验收：输入"帮我搜索生物降解塑料的专利" → 返回模拟专利结果
"""

import json
from pathlib import Path

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

# ---------------------------------------------------------------------------
# 0. 加载模拟专利数据
# ---------------------------------------------------------------------------

# 定位到 shared/test_data/sample_patents.json
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_PATENT_DATA_PATH = _PROJECT_ROOT / "shared" / "test_data" / "sample_patents.json"


def _load_patents() -> list[dict]:
    """从 JSON 文件加载模拟专利数据"""
    if not _PATENT_DATA_PATH.exists():
        print(f"⚠️  专利数据文件不存在: {_PATENT_DATA_PATH}")
        return []
    with open(_PATENT_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


# 预加载数据，避免每次工具调用都读文件
_PATENTS: list[dict] = _load_patents()

# ---------------------------------------------------------------------------
# 1. 定义工具
# ---------------------------------------------------------------------------


@tool
def search_patent(keyword: str) -> str:
    """根据关键词搜索专利数据库。

    Args:
        keyword: 搜索关键词，长度必须在 2-50 个字符之间。
    """
    # ---- 输入校验 ----
    if not keyword or not keyword.strip():
        return "❌ 搜索失败：关键词不能为空，请提供有效的搜索关键词。"

    keyword = keyword.strip()

    if len(keyword) < 2:
        return f"❌ 搜索失败：关键词「{keyword}」太短（{len(keyword)}字符），至少需要 2 个字符。"

    if len(keyword) > 50:
        return (
            f"❌ 搜索失败：关键词「{keyword[:20]}...」太长（{len(keyword)}字符），最多 50 个字符。"
        )

    # ---- 模糊匹配检索 ----
    results = []
    for patent in _PATENTS:
        # 在标题（日文 + 中文）、摘要中搜索关键词
        searchable = (
            patent.get("title", "") + patent.get("title_cn", "") + patent.get("abstract", "")
        )
        if keyword.lower() in searchable.lower():
            results.append(patent)

    # ---- 格式化输出 ----
    if not results:
        return f"未找到与「{keyword}」相关的专利。请尝试更换关键词。"

    output_lines = [f"🔍 找到 {len(results)} 件与「{keyword}」相关的专利：\n"]
    for i, p in enumerate(results, 1):
        output_lines.append(
            f"  [{i}] {p['patent_id']} — {p['title_cn']}\n"
            f"      申请人: {p['applicant']}\n"
            f"      申请日: {p['filing_date']}  |  状态: {p['status']}\n"
            f"      IPC分类: {', '.join(p['ipc_codes'])}\n"
            f"      摘要: {p['abstract'][:80]}...\n"
        )

    return "\n".join(output_lines)


@tool
def get_patent_detail(patent_id: str) -> str:
    """根据专利编号获取专利的完整详情。

    Args:
        patent_id: 专利编号，例如 JP2024-001。
    """
    if not patent_id or not patent_id.strip():
        return "❌ 查询失败：专利编号不能为空。"

    patent_id = patent_id.strip().upper()

    for patent in _PATENTS:
        if patent["patent_id"].upper() == patent_id:
            return (
                f"📄 专利详情 — {patent['patent_id']}\n"
                f"{'=' * 50}\n"
                f"标题(日): {patent['title']}\n"
                f"标题(中): {patent['title_cn']}\n"
                f"申请人:   {patent['applicant']}\n"
                f"申请日:   {patent['filing_date']}\n"
                f"状态:     {patent['status']}\n"
                f"IPC分类:  {', '.join(patent['ipc_codes'])}\n"
                f"摘要:\n  {patent['abstract']}\n"
            )

    return f"❌ 未找到编号为「{patent_id}」的专利。请确认编号是否正确（格式: JP2024-XXX）。"


@tool
def add(a: int, b: int) -> int:
    """两个数相加。

    Args:
        a: 第一个整数
        b: 第二个整数
    """
    return a + b


@tool
def multiply(a: int, b: int) -> int:
    """两个数相乘。

    Args:
        a: 第一个整数
        b: 第二个整数
    """
    return a * b


# ---------------------------------------------------------------------------
# 2. 打印工具的 JSON Schema（D4 实操要求）
# ---------------------------------------------------------------------------


def print_tool_schemas(tools_list: list):
    """打印每个工具的输入参数 JSON Schema，便于理解 LLM 如何识别工具"""
    print("\n📋 工具 JSON Schema 一览")
    print("=" * 60)
    for t in tools_list:
        schema = t.get_input_schema().model_json_schema()
        print(f"\n🔧 {t.name}")
        print(f"   描述: {t.description}")
        print(f"   Schema: {json.dumps(schema, indent=4, ensure_ascii=False)}")
    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# 3. 构建 Agent 并运行
# ---------------------------------------------------------------------------


def main():
    print("🚀 专利助手 v0.1 启动中...")
    print("-" * 50)

    # 初始化模型
    llm = ChatOllama(model="qwen2.5:7b", temperature=0)

    # 注册工具（专利搜索 + 专利详情 + 计算器）
    tools = [search_patent, get_patent_detail, add, multiply]

    # 打印工具 Schema
    print_tool_schemas(tools)

    # 构建 ReAct Agent
    agent = create_agent(llm, tools)

    # 保存 Agent 状态图
    try:
        png_data = agent.get_graph().draw_mermaid_png()
        output_path = Path(__file__).parent / "patent_agent_graph.png"
        with open(output_path, "wb") as f:
            f.write(png_data)
        print(f"✅ Agent 状态图已保存: {output_path.name}\n")
    except Exception as e:
        print(f"⚠️  保存状态图失败: {e}\n")

    # ---- 测试用例 ----
    test_queries = [
        "搜索生物降解塑料的专利",  # 正常专利搜索
        "查看专利 JP2024-002 的详细信息",  # 专利详情查询
        "3乘以4再加5等于多少？",  # 计算器（验证多工具选择）
    ]

    for query in test_queries:
        print(f"\n{'=' * 60}")
        print(f"👤 用户提问: {query}")
        print(f"{'=' * 60}\n")

        # 使用流式输出，实时显示 AI 回复
        print("🤔 思考中...", end="", flush=True)
        is_streaming_text = False
        first_output = True  # 标记是否是第一次输出（用于清除"思考中"）

        for event in agent.stream(
            {"messages": [("user", query)]},
            stream_mode="messages",
        ):
            msg, metadata = event
            node = metadata.get("langgraph_node", "")

            # 第一次有实质输出时，清除"思考中..."
            has_output = (
                (node == "tools" and msg.content)
                or (node == "model" and msg.content)
                or (node == "model" and hasattr(msg, "tool_calls") and msg.tool_calls)
            )
            if has_output and first_output:
                print("\r" + " " * 20 + "\r", end="", flush=True)  # 清除"思考中"
                first_output = False

            # AI 发起工具调用时打印提示
            if node == "model" and hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    print(f"⚙️  调用工具: {tc['name']}({tc['args']})")

            # 工具返回结果
            if node == "tools" and msg.content:
                print(f"🔧 [{msg.name}] → {msg.content}")

            # AI 回复：逐 token 流式输出
            if node == "model" and msg.content:
                if not is_streaming_text:
                    print("🤖 ", end="")
                    is_streaming_text = True
                print(msg.content, end="", flush=True)

        if is_streaming_text:
            print()  # 换行
        print()


if __name__ == "__main__":
    main()

"""
Day 5 — 让 Agent 优雅地处理错误
================================
目标：基于 Day4 的专利助手，给 Agent 加错误处理机制。
      工具超时 / 解析失败 / 空结果都有兜底，Agent 遇到错误不崩溃。

核心能力：
  1. safe_tool_wrapper —— 通用工具安全包装器（超时 + 异常捕获 + 日志）
  2. unreliable_search_patent —— 模拟不稳定 API（随机超时/异常）
  3. broken_tool —— 故意始终报错，验证 Agent 错误恢复

验收：故意输入 3 种错误场景，Agent 都能正常回复
"""

import json
import random
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from functools import wraps
from pathlib import Path

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

# ---------------------------------------------------------------------------
# 0. 加载模拟专利数据
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_PATENT_DATA_PATH = _PROJECT_ROOT / "shared" / "test_data" / "sample_patents.json"


def _load_patents() -> list[dict]:
    """从 JSON 文件加载模拟专利数据"""
    if not _PATENT_DATA_PATH.exists():
        print(f"⚠️  专利数据文件不存在: {_PATENT_DATA_PATH}")
        return []
    with open(_PATENT_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


_PATENTS: list[dict] = _load_patents()


# ===========================================================================
# 1. 核心：safe_tool_wrapper — 通用工具安全包装器
# ===========================================================================


def safe_tool_wrapper(func, timeout_sec: int = 10):
    """对工具函数施加超时控制和异常捕获的安全包装器。

    Args:
        func: 原始工具函数
        timeout_sec: 超时秒数，默认 10 秒

    Returns:
        包装后的安全版本函数，异常时返回友好错误消息而非抛出异常。

    设计思路：
        - 使用 concurrent.futures.ThreadPoolExecutor 进行超时控制
          （兼容主线程和子线程，不依赖 signal）
        - 所有异常统一捕获，转为字符串返回给 LLM
        - 记录调用耗时，便于后续性能分析
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        tool_name = getattr(func, "name", func.__name__)
        start_time = time.time()

        try:
            # 使用线程池实现超时控制（兼容非主线程环境）
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                result = future.result(timeout=timeout_sec)

            elapsed = time.time() - start_time
            print(f"    ⏱️  [{tool_name}] 执行耗时: {elapsed:.2f}s — 成功")
            return result

        except FuturesTimeoutError:
            elapsed = time.time() - start_time
            print(f"    ⏱️  [{tool_name}] 执行耗时: {elapsed:.2f}s — ⏰ 超时")
            return (
                f"⚠️ 工具「{tool_name}」调用超时（超过 {timeout_sec} 秒）。"
                "可能是外部服务暂时不可用，请稍后重试或更换关键词。"
            )

        except json.JSONDecodeError as e:
            elapsed = time.time() - start_time
            print(f"    ⏱️  [{tool_name}] 执行耗时: {elapsed:.2f}s — ❌ JSON 解析失败")
            return f"⚠️ 工具「{tool_name}」数据解析失败：{e}。数据格式异常，请联系管理员。"

        except Exception as e:
            elapsed = time.time() - start_time
            error_type = type(e).__name__
            print(f"    ⏱️  [{tool_name}] 执行耗时: {elapsed:.2f}s — ❌ {error_type}: {e}")
            return (
                f"⚠️ 工具「{tool_name}」执行出错（{error_type}）：{e}。"
                "请尝试更换输入参数或稍后重试。"
            )

    return wrapper


# ===========================================================================
# 2. 定义工具
# ===========================================================================


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
        searchable = (
            patent.get("title", "") + patent.get("title_cn", "") + patent.get("abstract", "")
        )
        if keyword.lower() in searchable.lower():
            results.append(patent)

    # ---- 空结果兜底 ----
    if not results:
        return f"未找到与「{keyword}」相关的专利。请尝试更换关键词，或缩短关键词范围。"

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
def unreliable_search_patent(keyword: str) -> str:
    """（不稳定版）搜索专利数据库 —— 可能会超时或出错，用于演示错误处理。

    Args:
        keyword: 搜索关键词。
    """
    # 30% 概率模拟超时（睡眠超过 safe_tool_wrapper 的超时阈值）
    if random.random() < 0.3:
        print("    💤 [unreliable_search_patent] 模拟超时中...")
        time.sleep(15)  # 故意超过 timeout_sec

    # 20% 概率模拟数据损坏异常
    if random.random() < 0.2:
        raise json.JSONDecodeError("模拟的 JSON 解析错误", doc="", pos=0)

    # 正常路径：复用 search_patent 的逻辑
    return search_patent.invoke({"keyword": keyword})


@tool
def broken_tool(query: str) -> str:
    """（故障工具）始终会报错，用于测试 Agent 的错误恢复能力。

    Args:
        query: 任意查询内容。
    """
    raise RuntimeError(
        "数据库连接失败：Connection refused (errno=111)。后端服务不可用，请联系系统管理员。"
    )


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


# ===========================================================================
# 3. 对工具施加安全包装
# ===========================================================================


def wrap_tools_with_safety(tools_list: list, timeout_sec: int = 10) -> list:
    """批量对工具列表施加 safe_tool_wrapper。

    包装方式：替换工具内部的 _run 方法，保留 LangChain Tool 的元信息。
    这样 LLM 仍然能看到正确的工具名、描述和 Schema。

    Args:
        tools_list: LangChain Tool 对象列表
        timeout_sec: 超时秒数

    Returns:
        施加安全包装后的工具列表（就地修改并返回）
    """
    for t in tools_list:
        original_func = t.func
        t.func = safe_tool_wrapper(original_func, timeout_sec=timeout_sec)
    return tools_list


# ===========================================================================
# 4. 工具 Schema 打印
# ===========================================================================


def print_tool_schemas(tools_list: list):
    """打印每个工具的输入参数 JSON Schema"""
    print("\n📋 工具 JSON Schema 一览")
    print("=" * 60)
    for t in tools_list:
        schema = t.get_input_schema().model_json_schema()
        print(f"\n🔧 {t.name}")
        print(f"   描述: {t.description}")
        print(f"   Schema: {json.dumps(schema, indent=4, ensure_ascii=False)}")
    print("=" * 60 + "\n")


# ===========================================================================
# 5. 流式运行并展示结果
# ===========================================================================


def stream_agent_response(agent, query: str):
    """用流式模式运行 Agent，实时展示工具调用和 AI 回复。

    包含顶层异常捕获：即使 Agent 运行过程中出现未预期的错误，
    也不会导致整个程序崩溃。
    """
    print(f"\n{'=' * 60}")
    print(f"👤 用户提问: {query}")
    print(f"{'=' * 60}\n")

    try:
        print("🤔 思考中...", end="", flush=True)
        is_streaming_text = False
        first_output = True

        for event in agent.stream(
            {"messages": [("user", query)]},
            stream_mode="messages",
        ):
            msg, metadata = event
            node = metadata.get("langgraph_node", "")

            # 判断是否有实质输出
            has_output = (
                (node == "tools" and msg.content)
                or (node == "model" and msg.content)
                or (node == "model" and hasattr(msg, "tool_calls") and msg.tool_calls)
            )
            if has_output and first_output:
                print("\r" + " " * 20 + "\r", end="", flush=True)
                first_output = False

            # AI 发起工具调用
            if node == "model" and hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    print(f"⚙️  调用工具: {tc['name']}({tc['args']})")

            # 工具返回结果
            if node == "tools" and msg.content:
                # 截断过长的工具输出，避免刷屏
                content_preview = msg.content[:200]
                if len(msg.content) > 200:
                    content_preview += "..."
                print(f"🔧 [{msg.name}] → {content_preview}")

            # AI 回复：逐 token 流式输出
            if node == "model" and msg.content:
                if not is_streaming_text:
                    print("🤖 ", end="")
                    is_streaming_text = True
                print(msg.content, end="", flush=True)

        if is_streaming_text:
            print()  # 换行

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断了操作。")

    except Exception as e:
        # 顶层兜底：Agent 运行期间的任何未预期异常都不导致崩溃
        error_type = type(e).__name__
        print(f"\n\n❌ Agent 运行出错（{error_type}）：{e}")
        print("💡 建议：请检查模型服务是否正常运行，或尝试更换问题再试。")

    print()


# ===========================================================================
# 6. 主函数
# ===========================================================================


def main():
    print("🚀 专利助手 v0.1 — Day5 错误处理版")
    print("=" * 50)
    print("本次演示重点：Agent 在 3 种错误场景下不崩溃、给出友好提示\n")

    # 初始化模型
    llm = ChatOllama(model="qwen2.5:7b", temperature=0)

    # 注册工具（包含不稳定工具和故障工具，用于错误场景演示）
    tools = [
        search_patent,
        get_patent_detail,
        unreliable_search_patent,
        broken_tool,
        add,
        multiply,
    ]

    # 施加安全包装：超时 5 秒（演示用，实际可调大）
    wrap_tools_with_safety(tools, timeout_sec=5)

    # 打印工具 Schema
    print_tool_schemas(tools)

    # 构建 ReAct Agent
    agent = create_agent(llm, tools)

    # 保存 Agent 状态图
    try:
        png_data = agent.get_graph().draw_mermaid_png()
        output_path = Path(__file__).parent / "error_handling_agent_graph.png"
        with open(output_path, "wb") as f:
            f.write(png_data)
        print(f"✅ Agent 状态图已保存: {output_path.name}\n")
    except Exception as e:
        print(f"⚠️  保存状态图失败: {e}\n")

    # ------------------------------------------------------------------
    # 错误场景测试
    # ------------------------------------------------------------------

    print("\n" + "🔥" * 30)
    print("   错误处理测试 — 3 种错误场景")
    print("🔥" * 30)

    test_queries = [
        # 场景 1：空关键词 / 输入校验
        "用空关键词搜索专利，关键词为空字符串",
        # 场景 2：调用故障工具 — Agent 应捕获错误并给出友好提示
        '用 broken_tool 工具查询一下"量子计算"的信息',
        # 场景 3：搜索不存在的关键词 — 空结果兜底
        '搜索关于"反物质推进引擎"的专利',
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'─' * 60}")
        print(f"📌 错误场景 {i}/3")
        print(f"{'─' * 60}")
        stream_agent_response(agent, query)

    # ------------------------------------------------------------------
    # 正常场景对照（确认错误处理不影响正常功能）
    # ------------------------------------------------------------------

    print("\n" + "✅" * 30)
    print("   正常场景对照 — 确认核心功能不受影响")
    print("✅" * 30)

    normal_queries = [
        "搜索生物降解塑料的专利",
        "3乘以4再加5等于多少？",
    ]

    for query in normal_queries:
        stream_agent_response(agent, query)

    print("\n🏁 Day5 错误处理演示完毕！")
    print("总结：Agent 在所有错误场景下均未崩溃，并给出了友好提示。")


if __name__ == "__main__":
    main()

"""
Day 6 — 专利助手 v0.2（可演示版）
==================================
目标：整合 D1-D5 所有能力，构建一个完整的终端对话助手。

整合能力清单：
  ┌─────────┬────────────────────────────────────┐
  │ D1      │ Ollama 模型调用                     │
  │ D2      │ Streaming 逐 token 输出             │
  │ D3      │ 工具自主选择（加法 / 乘法）         │
  │ D4      │ 专利搜索 + 详情查询 + 输入校验      │
  │ D5      │ safe_tool_wrapper + 顶层异常捕获     │
  └─────────┴────────────────────────────────────┘

新增能力：
  - while True 对话循环（连续对话）
  - 系统提示词（角色设定）
  - 帮助 / 退出 / 版本 等快捷命令
  - 专利对比工具（compare_patents）
  - --version 命令行参数

验收：录制一段 30 秒终端 demo（连续提问 3 个问题，展示工具调用和 streaming）
"""

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from functools import wraps
from pathlib import Path

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

# ---------------------------------------------------------------------------
# 版本信息
# ---------------------------------------------------------------------------

VERSION = "0.2.0"

# 功能清单（供 --version 打印）
FEATURES = [
    "🗣️  自然语言对话（Ollama / qwen2.5:7b）",
    "⚡  逐 token 流式输出（Streaming）",
    "🔍  专利关键词搜索（模拟数据）",
    "📄  专利详情查询",
    "🔀  专利对比分析",
    "🧮  数学计算（加法 / 乘法）",
    "🛡️  错误处理（超时 / 异常 / 空结果兜底）",
    "💬  连续对话循环（REPL）",
]

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
# 1. safe_tool_wrapper — 通用工具安全包装器（复用 D5）
# ===========================================================================


def safe_tool_wrapper(func, timeout_sec: int = 10):
    """对工具函数施加超时控制和异常捕获的安全包装器。

    Args:
        func: 原始工具函数
        timeout_sec: 超时秒数，默认 10 秒

    Returns:
        包装后的安全版本函数，异常时返回友好错误消息而非抛出异常。
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


def wrap_tools_with_safety(tools_list: list, timeout_sec: int = 10) -> list:
    """批量对工具列表施加 safe_tool_wrapper。

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
def compare_patents(patent_id_1: str, patent_id_2: str) -> str:
    """对比两件专利的关键信息（标题、申请人、IPC分类、状态）。

    Args:
        patent_id_1: 第一件专利的编号，例如 JP2024-001。
        patent_id_2: 第二件专利的编号，例如 JP2024-002。
    """
    # 查找两件专利
    p1 = None
    p2 = None
    for patent in _PATENTS:
        pid = patent["patent_id"].upper()
        if pid == patent_id_1.strip().upper():
            p1 = patent
        if pid == patent_id_2.strip().upper():
            p2 = patent

    if not p1:
        return f"❌ 未找到编号为「{patent_id_1}」的专利。"
    if not p2:
        return f"❌ 未找到编号为「{patent_id_2}」的专利。"

    # 构造对比表
    divider = "─" * 60
    return (
        f"📊 专利对比\n"
        f"{divider}\n"
        f"{'项目':<10} │ {'专利 A':^22} │ {'专利 B':^22}\n"
        f"{divider}\n"
        f"{'编号':<10} │ {p1['patent_id']:^22} │ {p2['patent_id']:^22}\n"
        f"{'标题(中)':<8} │ {p1['title_cn']:^22} │ {p2['title_cn']:^22}\n"
        f"{'申请人':<9} │ {p1['applicant']:^22} │ {p2['applicant']:^22}\n"
        f"{'申请日':<9} │ {p1['filing_date']:^22} │ {p2['filing_date']:^22}\n"
        f"{'状态':<10} │ {p1['status']:^22} │ {p2['status']:^22}\n"
        f"{'IPC分类':<8} │ {', '.join(p1['ipc_codes']):^22} │ {', '.join(p2['ipc_codes']):^22}\n"
        f"{divider}\n"
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
# 3. 系统提示词
# ===========================================================================

SYSTEM_PROMPT = """你是"专利助手 v0.2"，一个专注于化学专利分析的 AI 助手。

你的核心能力：
1. 搜索专利：根据关键词搜索专利数据库（search_patent）
2. 查看详情：根据专利编号获取完整信息（get_patent_detail）
3. 对比专利：对比两件专利的关键信息（compare_patents）
4. 数学计算：支持加法（add）和乘法（multiply）

行为准则：
- 回答时使用中文
- 专利相关问题优先使用工具获取数据，不要编造专利信息
- 如果工具返回错误或空结果，如实告知用户并给出建议
- 回答要简洁明了，避免冗长
"""


# ===========================================================================
# 4. 流式响应输出（复用 D5 + 优化）
# ===========================================================================


def stream_agent_response(agent, query: str):
    """用流式模式运行 Agent，实时展示工具调用和 AI 回复。

    包含顶层异常捕获：即使 Agent 运行过程中出现未预期的错误，
    也不会导致整个程序崩溃。

    Args:
        agent: LangGraph Agent 实例
        query: 用户输入的问题
    """
    try:
        print("\n🤔 思考中...", end="", flush=True)
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
                content_preview = msg.content[:300]
                if len(msg.content) > 300:
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
        print("\n\n⚠️ 用户中断了当前回答。")

    except Exception as e:
        # 顶层兜底：Agent 运行期间的任何未预期异常都不导致崩溃
        error_type = type(e).__name__
        print(f"\n\n❌ Agent 运行出错（{error_type}）：{e}")
        print("💡 建议：请检查模型服务是否正常运行，或尝试更换问题再试。")


# ===========================================================================
# 5. 用户界面 — 欢迎、帮助、快捷命令
# ===========================================================================

WELCOME_BANNER = f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🧪  专利助手 v{VERSION}  —  化学专利分析 AI 助手            ║
║                                                              ║
║   功能：专利搜索 · 详情查询 · 专利对比 · 数学计算            ║
║   输入 "帮助" 查看可用命令，输入 "退出" 离开                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
📋 可用命令：
  帮助 / help      — 显示此帮助信息
  退出 / exit / quit — 退出对话
  工具 / tools      — 查看已注册的工具列表
  版本 / version    — 显示版本信息

💡 使用示例：
  • 搜索生物降解塑料的专利
  • 查看专利 JP2024-002 的详细信息
  • 对比 JP2024-001 和 JP2024-002 这两件专利
  • 3乘以4再加5等于多少？
"""


def print_tool_list(tools_list: list):
    """打印已注册的工具列表（简洁模式）"""
    print("\n🔧 已注册工具：")
    for t in tools_list:
        # 取描述的第一行作为简短说明
        desc = t.description.split("\n")[0]
        print(f"  • {t.name} — {desc}")
    print()


def print_version():
    """打印版本和功能列表"""
    print(f"\n🧪 专利助手 v{VERSION}")
    print("─" * 40)
    print("已有功能：")
    for feat in FEATURES:
        print(f"  {feat}")
    print()


# ===========================================================================
# 6. 主函数 — 对话循环
# ===========================================================================


def main():
    # ---- 命令行参数 ----
    parser = argparse.ArgumentParser(description="专利助手 v0.2 — 化学专利分析 AI 助手")
    parser.add_argument("--version", action="store_true", help="打印版本和已有功能列表")
    args = parser.parse_args()

    if args.version:
        print_version()
        sys.exit(0)

    # ---- 启动 ----
    print(WELCOME_BANNER)
    print("⏳ 正在初始化模型和工具...")

    # 初始化模型
    llm = ChatOllama(model="qwen2.5:7b", temperature=0)

    # 注册生产级工具（不含 D5 的故障演示工具）
    tools = [search_patent, get_patent_detail, compare_patents, add, multiply]

    # 施加安全包装：超时 10 秒
    wrap_tools_with_safety(tools, timeout_sec=10)

    # 构建 ReAct Agent（带系统提示词）
    agent = create_agent(llm, tools, system_prompt=SYSTEM_PROMPT)

    # 保存 Agent 状态图
    try:
        png_data = agent.get_graph().draw_mermaid_png()
        output_path = Path(__file__).parent / "patent_assistant_v0.2_graph.png"
        with open(output_path, "wb") as f:
            f.write(png_data)
        print(f"✅ Agent 状态图已保存: {output_path.name}")
    except Exception as e:
        print(f"⚠️  保存状态图失败: {e}")

    print("✅ 初始化完成！开始对话吧 🎉\n")

    # ---- 对话循环 ----
    turn_count = 0  # 对话轮次计数

    while True:
        try:
            user_input = input("👤 你: ").strip()
        except (KeyboardInterrupt, EOFError):
            # Ctrl+C 或 Ctrl+D 退出
            print("\n\n👋 再见！感谢使用专利助手。")
            break

        # 空输入跳过
        if not user_input:
            continue

        # ---- 快捷命令处理 ----
        cmd = user_input.lower()

        if cmd in ("退出", "exit", "quit", "q"):
            print("\n👋 再见！感谢使用专利助手。")
            break

        if cmd in ("帮助", "help", "h", "?"):
            print(HELP_TEXT)
            continue

        if cmd in ("工具", "tools"):
            print_tool_list(tools)
            continue

        if cmd in ("版本", "version"):
            print_version()
            continue

        # ---- 调用 Agent 处理用户问题 ----
        turn_count += 1
        print(f"\n{'─' * 50}")
        print(f"  对话轮次 #{turn_count}")
        print(f"{'─' * 50}")

        stream_agent_response(agent, user_input)
        print()


if __name__ == "__main__":
    main()

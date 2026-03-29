"""
D16 — 链路加工具调用：在 LCEL Chain 基础上接入检索工具，工具错误可捕获
====================================================================

学习要点（基于 L4_tools.ipynb + L5_tools_with_mcp.ipynb + LangChain Tools 文档）：
  1. @tool 装饰器 —— 定义工具函数，LangChain 自动推断 JSON Schema
  2. create_agent() —— 创建带工具调用能力的 ReAct Agent
  3. middleware（wrap_tool_call）—— LangChain 最新的工具错误拦截机制
  4. ToolNode(handle_tool_errors=True) —— LangGraph 原生的工具错误捕获
  5. 链路日志回调 —— 继承 D15 的 ChainLogger 思路，追踪工具调用全链路

什么是"链路加工具调用"？
  D15 的链路是一条直线：Prompt → LLM → Parser
  D16 升级为带工具的闭环：LLM → (决定调用工具) → 工具执行 → (结果返回 LLM) → 最终回复
  这个闭环就是 ReAct 模式在工程化链路中的体现。

什么是"工具错误可捕获"？
  - 工具执行失败时（异常、超时、返回异常数据），Agent 不崩溃
  - 错误信息被转化为 ToolMessage 返回给 LLM，LLM 可以理解错误并调整策略
  - 链路日志中能清晰看到哪个工具出错、错误类型、耗时

运行方式：
  # 运行全部演示（正常 + 错误场景）
  ./run lecture16
  make run lecture16

  # 指定问题
  ./run lecture16 --query "搜索锂电池材料的专利"

  # 只运行错误场景测试
  ./run lecture16 --test-errors

  # 打印工具 Schema 信息
  ./run lecture16 --show-schema

  # 打印 Agent 状态图（Mermaid）
  ./run lecture16 --graph

验收标准：工具错误可捕获 —— 工具异常不崩溃，链路日志中能定位出错工具
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Callable

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

# ===========================================================================
# 第一部分：加载模拟专利数据
# ===========================================================================

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_PATENT_DATA_PATH = _PROJECT_ROOT / "shared" / "test_data" / "sample_patents.json"


def _load_patents() -> list[dict]:
    """从 JSON 文件加载模拟专利数据"""
    if not _PATENT_DATA_PATH.exists():
        print(f"⚠️  专利数据文件不存在: {_PATENT_DATA_PATH}")
        return []
    with open(_PATENT_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


# 预加载数据
_PATENTS: list[dict] = _load_patents()


# ===========================================================================
# 第二部分：定义工具（检索工具 + 故障工具 + 计算工具）
# ===========================================================================


@tool(
    "patent_search",
    parse_docstring=True,
    description=(
        "根据关键词搜索专利数据库，返回匹配的专利列表。"
        "支持中日英关键词模糊匹配。"
    ),
)
def patent_search(keyword: str) -> str:
    """根据关键词搜索专利数据库。

    Args:
        keyword: 搜索关键词，长度必须在 2-50 个字符之间。
            支持中文、日文、英文关键词。

    Returns:
        str: 匹配的专利列表，包含专利编号、标题、申请人等信息。

    Raises:
        ValueError: 关键词为空或长度不符合要求时。
    """
    # 输入校验
    if not keyword or not keyword.strip():
        raise ValueError("搜索关键词不能为空，请提供有效的关键词。")

    keyword = keyword.strip()

    if len(keyword) < 2:
        raise ValueError(
            f"关键词「{keyword}」太短（{len(keyword)}字符），至少需要 2 个字符。"
        )

    if len(keyword) > 50:
        raise ValueError(
            f"关键词太长（{len(keyword)}字符），最多 50 个字符。"
        )

    # 模糊匹配检索
    results = []
    for patent in _PATENTS:
        searchable = (
            patent.get("title", "")
            + patent.get("title_cn", "")
            + patent.get("abstract", "")
        )
        if keyword.lower() in searchable.lower():
            results.append(patent)

    # 格式化输出
    if not results:
        return f"未找到与「{keyword}」相关的专利。请尝试更换关键词。"

    lines = [f"🔍 找到 {len(results)} 件与「{keyword}」相关的专利：\n"]
    for i, p in enumerate(results, 1):
        lines.append(
            f"  [{i}] {p['patent_id']} — {p['title_cn']}\n"
            f"      申请人: {p['applicant']}\n"
            f"      申请日: {p['filing_date']}  |  状态: {p['status']}\n"
            f"      IPC分类: {', '.join(p['ipc_codes'])}\n"
            f"      摘要: {p['abstract'][:80]}...\n"
        )

    return "\n".join(lines)


@tool(
    "patent_detail",
    parse_docstring=True,
    description="根据专利编号获取专利的完整详情信息。",
)
def patent_detail(patent_id: str) -> str:
    """根据专利编号获取专利的完整详情。

    Args:
        patent_id: 专利编号，例如 JP2024-001。

    Returns:
        str: 专利的完整详情信息。

    Raises:
        ValueError: 专利编号为空时。
    """
    if not patent_id or not patent_id.strip():
        raise ValueError("专利编号不能为空。")

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

    return f"未找到编号为「{patent_id}」的专利。请确认编号格式（如 JP2024-001）。"


@tool(
    "unreliable_api",
    description="（不稳定 API）查询外部专利数据库 —— 可能会出错，用于演示工具错误处理。",
)
def unreliable_api(query: str) -> str:
    """调用不稳定的外部 API —— 始终抛出异常，用于演示错误捕获。

    Args:
        query: 查询内容。
    """
    # 模拟外部服务不可用
    raise ConnectionError(
        "外部专利数据库连接失败：Connection refused (errno=111)。"
        "服务暂时不可用，请稍后重试。"
    )


@tool(
    "calculator",
    parse_docstring=True,
    description=(
        "执行基本的数学运算。支持加、减、乘、除运算。"
        "任何涉及数字计算的问题都可以使用这个工具。"
    ),
)
def calculator(a: float, b: float, operation: str) -> str:
    """执行两个数的基本算术运算。

    Args:
        a: 第一个数字。
        b: 第二个数字。
        operation: 运算类型，可选 "add"（加）、"subtract"（减）、
            "multiply"（乘）、"divide"（除）。

    Returns:
        str: 计算结果的描述。

    Raises:
        ValueError: 运算类型无效或除以零时。
    """
    op = operation.lower().strip()

    if op == "add":
        result = a + b
    elif op == "subtract":
        result = a - b
    elif op == "multiply":
        result = a * b
    elif op == "divide":
        if b == 0:
            raise ValueError("除数不能为零。")
        result = a / b
    else:
        raise ValueError(
            f"无效的运算类型「{operation}」。"
            "支持的运算：add, subtract, multiply, divide。"
        )

    return f"{a} {op} {b} = {result}"


# ===========================================================================
# 第三部分：链路日志回调（继承 D15 ChainLogger 思路，增加工具调用追踪）
# ===========================================================================


class ToolChainLogger(BaseCallbackHandler):
    """链路 + 工具调用日志处理器。

    相比 D15 的 ChainLogger，增加了：
      - on_tool_start: 追踪工具调用开始（含参数）
      - on_tool_end:   追踪工具调用结束（含结果摘要）
      - on_tool_error: 追踪工具调用出错（含错误详情）
    """

    def __init__(self, verbose: bool = False) -> None:
        super().__init__()
        self.verbose = verbose
        self._step_count = 0
        self._timers: dict[str, float] = {}
        self._depth = 0
        self._tool_calls: list[dict] = []  # 记录所有工具调用

    # --- 辅助方法 ---

    def _indent(self) -> str:
        return "  " * self._depth

    @staticmethod
    def _truncate(text: str, max_len: int = 120) -> str:
        text = text.replace("\n", "↵ ")
        return text[:max_len] + "..." if len(text) > max_len else text

    @staticmethod
    def _format_duration(seconds: float) -> str:
        if seconds < 0.001:
            return f"{seconds * 1_000_000:.0f}μs"
        if seconds < 1:
            return f"{seconds * 1000:.1f}ms"
        return f"{seconds:.2f}s"

    @staticmethod
    def _extract_name(serialized: dict[str, Any] | None) -> str:
        if not serialized:
            return "Unknown"
        name = serialized.get("name", "")
        if name:
            return name
        id_list = serialized.get("id", [])
        return id_list[-1] if id_list else "Unknown"

    def _summarize(self, data: Any) -> str:
        if isinstance(data, str):
            return self._truncate(data)
        if isinstance(data, dict):
            parts = [f"{k}={self._truncate(str(v), 60)}" for k, v in data.items()]
            return "{" + ", ".join(parts) + "}"
        if isinstance(data, list):
            if data and isinstance(data[0], BaseMessage):
                return f"[{len(data)} messages]"
            return f"[{len(data)} items]"
        return self._truncate(str(data), 80)

    # --- Chain 回调 ---

    def on_chain_start(self, serialized: dict, inputs: Any, **kwargs) -> None:
        self._step_count += 1
        # LangGraph 回调中 serialized 通常为 None，节点名称通过 kwargs['name'] 传递
        name = kwargs.get("name") or self._extract_name(serialized)
        run_id = str(kwargs.get("run_id", ""))[:8]
        self._timers[run_id] = time.perf_counter()
        indent = self._indent()
        print(f"{indent}┌─[步骤 {self._step_count}] {name}")
        if self.verbose:
            print(f"{indent}│  输入: {self._summarize(inputs)}")
        self._depth += 1

    def on_chain_end(self, outputs: Any, **kwargs) -> None:
        self._depth = max(0, self._depth - 1)
        run_id = str(kwargs.get("run_id", ""))[:8]
        elapsed = time.perf_counter() - self._timers.pop(run_id, time.perf_counter())
        indent = self._indent()
        print(f"{indent}└─ ✅ 完成 ({self._format_duration(elapsed)})")

    def on_chain_error(self, error: BaseException, **kwargs) -> None:
        self._depth = max(0, self._depth - 1)
        run_id = str(kwargs.get("run_id", ""))[:8]
        elapsed = time.perf_counter() - self._timers.pop(run_id, time.perf_counter())
        indent = self._indent()
        print(f"{indent}└─ ❌ 链路错误 ({self._format_duration(elapsed)}): {error}")

    # --- LLM 回调 ---

    def on_chat_model_start(self, serialized: dict, messages: list, **kwargs) -> None:
        run_id = str(kwargs.get("run_id", ""))[:8]
        self._timers[run_id] = time.perf_counter()
        indent = self._indent()
        model_name = self._extract_name(serialized)
        msg_count = sum(len(m) for m in messages)
        print(f"{indent}🤖 ChatModel 调用: {model_name} ({msg_count} 条消息)")

    def on_llm_end(self, response: Any, **kwargs) -> None:
        run_id = str(kwargs.get("run_id", ""))[:8]
        elapsed = time.perf_counter() - self._timers.pop(run_id, time.perf_counter())
        indent = self._indent()
        print(f"{indent}✅ LLM 返回 ({self._format_duration(elapsed)})")

    # --- 工具回调（D16 新增） ---

    def on_tool_start(
        self, serialized: dict, input_str: str, **kwargs
    ) -> None:
        """工具调用开始 —— D16 核心：追踪工具被调用的时机和参数"""
        run_id = str(kwargs.get("run_id", ""))[:8]
        self._timers[run_id] = time.perf_counter()
        tool_name = self._extract_name(serialized)
        indent = self._indent()

        print(f"{indent}🔧 工具调用: {tool_name}")
        if self.verbose:
            print(f"{indent}   参数: {self._truncate(input_str, 100)}")

        # 记录工具调用
        self._tool_calls.append({
            "name": tool_name,
            "input": input_str,
            "start_time": time.perf_counter(),
            "status": "running",
        })

    def on_tool_end(self, output: str, **kwargs) -> None:
        """工具调用结束 —— 记录成功结果"""
        run_id = str(kwargs.get("run_id", ""))[:8]
        elapsed = time.perf_counter() - self._timers.pop(run_id, time.perf_counter())
        indent = self._indent()

        print(f"{indent}✅ 工具返回 ({self._format_duration(elapsed)})")
        if self.verbose:
            print(f"{indent}   结果: {self._truncate(str(output), 100)}")

        # 更新记录
        if self._tool_calls:
            self._tool_calls[-1].update({
                "status": "success",
                "elapsed": elapsed,
            })

    def on_tool_error(self, error: BaseException, **kwargs) -> None:
        """工具调用出错 —— D16 核心：追踪工具错误的具体信息"""
        run_id = str(kwargs.get("run_id", ""))[:8]
        elapsed = time.perf_counter() - self._timers.pop(run_id, time.perf_counter())
        indent = self._indent()
        error_type = type(error).__name__

        print(f"{indent}❌ 工具错误 ({self._format_duration(elapsed)})")
        print(f"{indent}   类型: {error_type}")
        print(f"{indent}   详情: {self._truncate(str(error), 100)}")

        # 更新记录
        if self._tool_calls:
            self._tool_calls[-1].update({
                "status": "error",
                "error_type": error_type,
                "error_msg": str(error),
                "elapsed": elapsed,
            })

    # --- 汇总报告 ---

    def print_summary(self) -> None:
        """打印工具调用汇总 —— 方便回顾本次运行中所有工具的执行情况"""
        if not self._tool_calls:
            print("  （本次运行无工具调用）")
            return

        print(f"\n📊 工具调用汇总（共 {len(self._tool_calls)} 次）：")
        print("─" * 60)
        for i, tc in enumerate(self._tool_calls, 1):
            status_icon = "✅" if tc["status"] == "success" else "❌"
            elapsed_str = self._format_duration(tc.get("elapsed", 0))
            print(f"  {i}. {status_icon} {tc['name']} — {elapsed_str}")
            if tc["status"] == "error":
                print(f"     └─ {tc.get('error_type', '?')}: {tc.get('error_msg', '?')[:60]}")


# ===========================================================================
# 第四部分：Middleware 工具错误拦截器（LangChain 最新 API）
# ===========================================================================
#
# LangChain 的 middleware 机制（wrap_tool_call）允许我们在工具执行的"外层"
# 插入拦截逻辑，类似于 Web 框架的中间件。
#
# 这比 D5 的 safe_tool_wrapper 更优雅：
#   - D5：在工具函数内部 try/except，修改了工具本身
#   - D16：在链路层面拦截，工具代码保持纯净，错误处理逻辑独立
#


@wrap_tool_call
def error_catcher_middleware(request, handler):
    """工具错误捕获中间件 —— 将异常转化为对 LLM 友好的错误消息。

    当工具抛出异常时：
      1. 不让异常传播到 Agent 主循环（防止崩溃）
      2. 将异常信息包装为 ToolMessage 返回给 LLM
      3. LLM 可以根据错误信息调整策略（换工具、换参数、或直接回复用户）
    """
    tool_name = request.tool_call.get("name", "unknown")
    tool_args = request.tool_call.get("args", {})
    start_time = time.perf_counter()

    try:
        result = handler(request)
        elapsed = time.perf_counter() - start_time
        print(f"  📎 [middleware] {tool_name} 执行成功 ({elapsed:.2f}s)")
        return result

    except Exception as e:
        elapsed = time.perf_counter() - start_time
        error_type = type(e).__name__
        print(
            f"  📎 [middleware] {tool_name} 执行失败 ({elapsed:.2f}s) — "
            f"{error_type}: {e}"
        )

        # 将错误转化为 ToolMessage，返回给 LLM
        error_msg = (
            f"⚠️ 工具「{tool_name}」执行出错（{error_type}）：{e}\n"
            f"输入参数：{json.dumps(tool_args, ensure_ascii=False)}\n"
            "请检查参数是否正确，或尝试使用其他工具。"
        )

        return ToolMessage(
            content=error_msg,
            tool_call_id=request.tool_call["id"],
        )


# ===========================================================================
# 第五部分：构建 Agent 并运行
# ===========================================================================


def build_agent(model_name: str = "qwen2.5:7b"):
    """构建带工具调用 + 错误捕获的 Agent。

    链路结构：
      用户输入 → LLM（判断是否需要工具）
                    ↓ 是 → 工具执行（middleware 拦截错误）→ 结果返回 LLM
                    ↓ 否 → 直接回复用户
    """
    # 创建 Agent，绑定所有工具 + 错误捕获中间件
    agent = create_agent(
        model=ChatOllama(model=model_name, temperature=0),
        tools=[patent_search, patent_detail, unreliable_api, calculator],
        system_prompt=(
            "你是一名专利分析助手。你可以帮助用户搜索专利、查看专利详情、"
            "进行简单计算。请用中文回复。\n"
            "注意：\n"
            "- 搜索专利时使用 patent_search 工具\n"
            "- 查看专利详情时使用 patent_detail 工具\n"
            "- 数学计算使用 calculator 工具\n"
            "- 如果工具返回错误信息，请向用户解释情况并建议替代方案"
        ),
        middleware=[error_catcher_middleware],
    )

    return agent


def run_agent(
    agent,
    query: str,
    verbose: bool = False,
    show_summary: bool = True,
) -> None:
    """运行 Agent 并用链路日志展示全过程。"""
    # 初始化日志回调
    logger = ToolChainLogger(verbose=verbose)

    print("=" * 68)
    print("📋 D16 链路 + 工具调用日志")
    print(f"   问题: {query}")
    print(f"   日志: {'详细' if verbose else '简要'}")
    print("=" * 68)

    start_time = time.perf_counter()
    is_streaming_text = False
    first_output = True

    try:
        for event in agent.stream(
            {"messages": [("user", query)]},
            stream_mode="messages",
            config={"callbacks": [logger]},
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
                first_output = False

            # AI 发起工具调用
            if node == "model" and hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    args_str = json.dumps(tc["args"], ensure_ascii=False)
                    print(f"⚙️  LLM 决定调用: {tc['name']}({args_str})")

            # 工具返回结果
            if node == "tools" and msg.content:
                preview = msg.content[:200]
                if len(msg.content) > 200:
                    preview += "..."
                print(f"🔧 [{msg.name}] → {preview}")

            # AI 最终回复：逐 token 流式输出
            if node == "model" and msg.content:
                if not is_streaming_text:
                    print("\n🤖 AI 回复: ", end="")
                    is_streaming_text = True
                print(msg.content, end="", flush=True)

        if is_streaming_text:
            print()  # 换行

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断了操作。")

    except Exception as e:
        error_type = type(e).__name__
        print(f"\n\n❌ Agent 运行出错（{error_type}）：{e}")
        print("💡 建议：请检查模型服务是否正常运行。")

    elapsed = time.perf_counter() - start_time

    print("\n" + "─" * 68)
    print(f"⏱️  总耗时: {elapsed:.2f}s")

    # 打印工具调用汇总
    if show_summary:
        logger.print_summary()

    print("=" * 68)


# ===========================================================================
# 第六部分：工具 Schema 展示
# ===========================================================================


def print_tool_schemas() -> None:
    """打印每个工具的 JSON Schema —— 理解 LLM 如何"看到"工具"""
    tools = [patent_search, patent_detail, unreliable_api, calculator]
    print("\n📋 工具 JSON Schema 一览")
    print("=" * 60)
    for t in tools:
        schema = t.get_input_schema().model_json_schema()
        print(f"\n🔧 {t.name}")
        print(f"   描述: {t.description}")
        print(f"   Schema: {json.dumps(schema, indent=4, ensure_ascii=False)}")
    print("=" * 60 + "\n")


# ===========================================================================
# 第七部分：Agent 状态图可视化
# ===========================================================================


def print_agent_graph(model_name: str = "qwen2.5:7b") -> None:
    """打印 Agent 的 Mermaid 状态图"""
    agent = build_agent(model_name=model_name)
    graph = agent.get_graph()

    print("=" * 68)
    print("🔗 Agent 状态图（带工具调用）")
    print("=" * 68)

    # 尝试打印 ASCII 图
    try:
        print(graph.draw_ascii())
    except ImportError:
        print("（ASCII 图需要 grandalf 依赖，跳过）")

    # 打印 Mermaid 图
    print("─" * 68)
    print("📊 Mermaid 图（可粘贴到 https://mermaid.live 查看）:")
    print("─" * 68)
    print(graph.draw_mermaid())

    # 尝试保存 PNG
    try:
        png_data = graph.draw_mermaid_png()
        output_path = Path(__file__).parent / "tool_chain_graph.png"
        with open(output_path, "wb") as f:
            f.write(png_data)
        print(f"\n✅ Agent 状态图已保存: {output_path}")
    except Exception as e:
        print(f"\n⚠️  保存 PNG 失败: {e}")

    print("=" * 68)


# ===========================================================================
# CLI 入口
# ===========================================================================


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="D16: 链路加工具调用 — 接入检索工具 + 工具错误可捕获"
    )
    parser.add_argument("--query", "-q", help="要分析的问题")
    parser.add_argument(
        "--test-errors",
        action="store_true",
        help="只运行错误场景测试",
    )
    parser.add_argument(
        "--show-schema",
        action="store_true",
        help="打印工具 JSON Schema",
    )
    parser.add_argument(
        "--graph",
        "-g",
        action="store_true",
        help="打印 Agent 状态图（Mermaid）",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="详细日志（显示工具输入/输出内容）",
    )
    parser.add_argument(
        "--model",
        default="qwen2.5:7b",
        help="Ollama 模型名称（默认 qwen2.5:7b）",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # 打印工具 Schema
    if args.show_schema:
        print_tool_schemas()
        return 0

    # 打印状态图
    if args.graph:
        print_agent_graph(model_name=args.model)
        return 0

    # 构建 Agent
    print("🚀 D16 — 链路加工具调用 + 工具错误捕获")
    print("=" * 50)
    agent = build_agent(model_name=args.model)

    # 指定问题模式
    if args.query:
        run_agent(agent, args.query, verbose=args.verbose)
        return 0

    # 错误场景测试
    if args.test_errors:
        print("\n" + "🔥" * 30)
        print("   工具错误捕获测试 — 3 种错误场景")
        print("🔥" * 30)

        error_queries = [
            # 场景 1：工具参数校验错误（关键词为空/太短）
            "用关键词 'X' 搜索专利",  # 单字符，触发长度校验
            # 场景 2：调用不稳定 API（始终报 ConnectionError）
            '使用 unreliable_api 工具查询"量子计算"',
            # 场景 3：除以零（数学工具异常）
            "用 calculator 计算 100 除以 0",
        ]

        for i, query in enumerate(error_queries, 1):
            print(f"\n{'─' * 60}")
            print(f"📌 错误场景 {i}/{len(error_queries)}")
            print(f"{'─' * 60}")
            run_agent(agent, query, verbose=args.verbose)

        return 0

    # 默认模式：运行正常 + 错误场景的完整演示
    print("\n" + "✅" * 30)
    print("   正常场景 — 工具调用演示")
    print("✅" * 30)

    normal_queries = [
        "搜索有关锂电池材料的专利",
        "查看专利 JP2024-002 的详细信息",
        "计算 3.14 乘以 2.72",
    ]

    for query in normal_queries:
        run_agent(agent, query, verbose=args.verbose)

    print("\n" + "🔥" * 30)
    print("   错误场景 — 工具错误捕获演示")
    print("🔥" * 30)

    error_queries = [
        '使用 unreliable_api 查询"新能源"相关专利',
        "用 calculator 计算 100 除以 0",
    ]

    for query in error_queries:
        run_agent(agent, query, verbose=args.verbose)

    print("\n🏁 D16 演示完毕！")
    print("关键收获：")
    print("  1. 工具通过 @tool + 详细 docstring 让 LLM 理解如何调用")
    print("  2. middleware（wrap_tool_call）在链路层面拦截工具错误")
    print("  3. 错误被转化为 ToolMessage 返回 LLM，Agent 不崩溃")
    print("  4. 日志回调追踪完整的 工具调用→错误→恢复 链路")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

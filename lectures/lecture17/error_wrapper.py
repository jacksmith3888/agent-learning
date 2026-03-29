"""
D17 — 解析与异常层：统一异常处理
================================

学习要点（基于 L1_fast_agent.ipynb + LangChain Guardrails + 中间件文档）：
  1. ErrorCode 枚举 —— 定义标准化错误码体系（工具/模型/解析/系统）
  2. AgentError 异常类 —— 带错误码、严重级别、建议动作的统一异常
  3. 三层错误防线：
      - 第一层：工具层 error_shield 装饰器（工具级别 try/except）
      - 第二层：中间件层 error_handler_middleware（链路级别拦截）
      - 第三层：Agent 顶层 safe_invoke（运行时兜底）
  4. ModelRetryMiddleware —— LangChain 内置的模型调用重试中间件
  5. ErrorReporter —— 错误日志收集与汇总报告

什么是"统一异常处理"？
  D5 的 safe_tool_wrapper 只在工具函数内部 try/except，粒度粗、无分类
  D16 的 middleware 在链路层面拦截，但只做了简单的 catch-all
  D17 升级为系统化的三层异常体系：
    ① 每个错误有标准化错误码（E1001-E4xxx），便于日志检索和监控告警
    ② 错误按严重级别分类（INFO/WARNING/ERROR/CRITICAL），指导处理策略
    ③ 每个错误附带建议动作（重试/换参/降级/人工介入），LLM 和运维都能用

D5 → D16 → D17 的演进路线：
  D5:  工具内部 try/except → 返回友好字符串（临时方案）
  D16: middleware 拦截     → 错误转 ToolMessage（工程化方案）
  D17: 三层统一异常       → 错误码 + 级别 + 动作（生产级方案）

运行方式：
  # 运行全部演示（正常 + 所有错误场景）
  ./run lecture17

  # 指定问题
  ./run lecture17 --query "搜索锂电池材料的专利"

  # 只运行错误场景测试
  ./run lecture17 --test-errors

  # 打印错误码定义表
  ./run lecture17 --show-codes

  # 详细模式（显示完整错误堆栈）
  ./run lecture17 -v

验收标准：错误码分类清晰 —— 每种错误有唯一编码、严重级别、建议动作
"""

from __future__ import annotations

import argparse
import enum
import json
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRetryMiddleware, wrap_tool_call
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

# ===========================================================================
# 第一部分：标准化错误码体系
# ===========================================================================
#
# 错误码设计原则：
#   - 分4大类：E1xxx（工具）、E2xxx（模型）、E3xxx（解析）、E4xxx（系统）
#   - 每个码有唯一含义，便于日志检索（grep "E1001" logs.txt）
#   - 参考 HTTP 状态码的分类思路，但更符合 Agent 场景
#


class ErrorCode(enum.Enum):
    """Agent 标准化错误码。

    命名规则：E{大类}{序号}
      E1xxx — 工具层错误（外部依赖、输入校验、业务逻辑）
      E2xxx — 模型层错误（LLM 调用、Token 超限）
      E3xxx — 解析层错误（输出格式、Schema 校验）
      E4xxx — 系统层错误（配置、网络、基础设施）
    """

    # --- 工具层 E1xxx ---
    E1001 = "工具输入校验失败"
    E1002 = "工具执行超时"
    E1003 = "工具外部服务不可用"
    E1004 = "工具返回空结果"
    E1005 = "工具返回数据格式异常"
    E1006 = "工具权限不足"
    E1099 = "工具未知错误"

    # --- 模型层 E2xxx ---
    E2001 = "模型调用失败"
    E2002 = "模型响应超时"
    E2003 = "Token 超出上下文窗口"
    E2004 = "模型拒绝生成（安全策略）"
    E2005 = "模型服务不可用"
    E2099 = "模型未知错误"

    # --- 解析层 E3xxx ---
    E3001 = "输出 JSON 解析失败"
    E3002 = "输出 Schema 校验失败"
    E3003 = "输出字段缺失"
    E3004 = "输出字段类型错误"
    E3005 = "输出内容为空"
    E3099 = "解析未知错误"

    # --- 系统层 E4xxx ---
    E4001 = "配置缺失或无效"
    E4002 = "网络连接失败"
    E4003 = "文件读写失败"
    E4004 = "内存不足"
    E4099 = "系统未知错误"


class Severity(enum.Enum):
    """错误严重级别 —— 对应不同的处理策略。

    INFO:     记录日志，流程继续
    WARNING:  记录日志，尝试自动恢复（重试/降级）
    ERROR:    记录日志，中断当前任务，返回友好提示
    CRITICAL: 记录日志 + 告警，可能需要人工介入
    """

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SuggestedAction(enum.Enum):
    """建议的错误恢复动作 —— 指导 LLM 或运维如何处理。"""

    RETRY = "重试当前操作"
    CHANGE_PARAMS = "更换输入参数"
    FALLBACK_TOOL = "降级到备选工具"
    FALLBACK_MODEL = "降级到备选模型"
    SKIP = "跳过当前步骤"
    MANUAL = "需要人工介入"
    ABORT = "终止当前任务"


# ===========================================================================
# 第二部分：统一异常类
# ===========================================================================


@dataclass
class AgentError(Exception):
    """Agent 统一异常 —— 所有异常最终都包装为此类型。

    与普通 Exception 的区别：
      - code:     标准错误码，便于检索和分类
      - severity: 严重级别，决定处理策略
      - action:   建议动作，指导恢复方式
      - context:  附带上下文（工具名、参数等）
      - original: 保留原始异常，不丢失堆栈信息
    """

    code: ErrorCode
    message: str
    severity: Severity = Severity.ERROR
    action: SuggestedAction = SuggestedAction.RETRY
    context: dict[str, Any] = field(default_factory=dict)
    original: BaseException | None = None

    def __str__(self) -> str:
        return (
            f"[{self.code.name}] {self.message} "
            f"(级别={self.severity.value}, 建议={self.action.value})"
        )

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典 —— 便于日志记录和 JSON 输出"""
        return {
            "code": self.code.name,
            "code_desc": self.code.value,
            "message": self.message,
            "severity": self.severity.value,
            "action": self.action.value,
            "context": self.context,
            "original_type": (
                type(self.original).__name__ if self.original else None
            ),
        }

    def to_friendly_message(self) -> str:
        """生成对 LLM / 用户友好的错误消息"""
        parts = [
            f"⚠️ 错误 [{self.code.name}] — {self.message}",
            f"   严重级别: {self.severity.value}",
            f"   建议操作: {self.action.value}",
        ]
        if self.context:
            ctx_str = ", ".join(
                f"{k}={v}" for k, v in self.context.items()
            )
            parts.append(f"   上下文: {ctx_str}")
        return "\n".join(parts)


# ===========================================================================
# 第三部分：异常分类器 —— 将原始异常映射为 AgentError
# ===========================================================================


# 默认错误码映射表：原始异常类型 → (ErrorCode, Severity, SuggestedAction)
_ERROR_CLASSIFICATION: dict[
    type, tuple[ErrorCode, Severity, SuggestedAction]
] = {
    ValueError: (ErrorCode.E1001, Severity.WARNING, SuggestedAction.CHANGE_PARAMS),
    TypeError: (ErrorCode.E1001, Severity.WARNING, SuggestedAction.CHANGE_PARAMS),
    TimeoutError: (ErrorCode.E1002, Severity.WARNING, SuggestedAction.RETRY),
    ConnectionError: (ErrorCode.E1003, Severity.ERROR, SuggestedAction.RETRY),
    ConnectionRefusedError: (ErrorCode.E1003, Severity.ERROR, SuggestedAction.RETRY),
    ConnectionResetError: (ErrorCode.E1003, Severity.ERROR, SuggestedAction.RETRY),
    json.JSONDecodeError: (ErrorCode.E3001, Severity.ERROR, SuggestedAction.RETRY),
    FileNotFoundError: (ErrorCode.E4003, Severity.ERROR, SuggestedAction.MANUAL),
    PermissionError: (ErrorCode.E1006, Severity.CRITICAL, SuggestedAction.MANUAL),
    MemoryError: (ErrorCode.E4004, Severity.CRITICAL, SuggestedAction.ABORT),
    KeyboardInterrupt: (ErrorCode.E4099, Severity.INFO, SuggestedAction.ABORT),
}


def classify_error(
    error: BaseException,
    tool_name: str | None = None,
    tool_args: dict | None = None,
) -> AgentError:
    """将任意异常分类为 AgentError。

    优先匹配精确类型，然后尝试父类匹配，最后兜底为未知错误。
    """
    # 如果已经是 AgentError，直接返回
    if isinstance(error, AgentError):
        return error

    # 查找匹配的错误分类
    error_type = type(error)
    classification = _ERROR_CLASSIFICATION.get(error_type)

    # 如果精确类型无匹配，尝试 MRO（父类链）匹配
    if classification is None:
        for base_type in error_type.__mro__[1:]:
            classification = _ERROR_CLASSIFICATION.get(base_type)
            if classification:
                break

    # 兜底：未知错误
    if classification is None:
        classification = (
            ErrorCode.E1099,
            Severity.ERROR,
            SuggestedAction.RETRY,
        )

    code, severity, action = classification

    # 构建上下文
    context: dict[str, Any] = {}
    if tool_name:
        context["tool_name"] = tool_name
    if tool_args:
        context["tool_args"] = tool_args

    return AgentError(
        code=code,
        message=str(error),
        severity=severity,
        action=action,
        context=context,
        original=error,
    )


# ===========================================================================
# 第四部分：第一层防线 —— 工具级 error_shield 装饰器
# ===========================================================================
#
# 与 D5 的 safe_tool_wrapper 对比：
#   D5:  返回普通字符串，无错误码、无分类
#   D17: 返回 AgentError 包装的结构化信息
#


def error_shield(func: Callable) -> Callable:
    """工具安全防护装饰器 —— 第一层防线。

    将工具函数内部抛出的所有异常转化为 AgentError，
    然后以友好消息形式返回（不抛出），保证 Agent 不崩溃。

    用法：
        @tool
        @error_shield
        def my_tool(query: str) -> str:
            ...
    """
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tool_name = getattr(func, "name", func.__name__)
        start_time = time.perf_counter()

        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start_time
            print(
                f"  🛡️ [error_shield] {tool_name} — "
                f"✅ 成功 ({elapsed:.2f}s)"
            )
            return result

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            agent_error = classify_error(
                e, tool_name=tool_name, tool_args=kwargs or {}
            )
            print(
                f"  🛡️ [error_shield] {tool_name} — "
                f"❌ {agent_error.code.name} ({elapsed:.2f}s)"
            )
            return agent_error.to_friendly_message()

    return wrapper


# ===========================================================================
# 第五部分：第二层防线 —— 中间件层错误拦截
# ===========================================================================
#
# 与 D16 的 error_catcher_middleware 对比：
#   D16: 简单的 catch-all，错误信息不规范
#   D17: 用 AgentError 标准化，附带错误码和建议动作
#


@wrap_tool_call
def error_handler_middleware(request, handler):
    """工具错误处理中间件 —— 第二层防线。

    在 Agent 链路层面拦截工具执行错误：
      1. 分类异常，生成标准化 AgentError
      2. 将结构化错误信息转为 ToolMessage 返回 LLM
      3. LLM 可根据错误码和建议动作调整策略
    """
    tool_name = request.tool_call.get("name", "unknown")
    tool_args = request.tool_call.get("args", {})
    start_time = time.perf_counter()

    try:
        result = handler(request)
        elapsed = time.perf_counter() - start_time
        print(
            f"  📎 [middleware] {tool_name} — "
            f"✅ 成功 ({elapsed:.2f}s)"
        )
        return result

    except Exception as e:
        elapsed = time.perf_counter() - start_time

        # 用分类器生成标准化错误
        agent_error = classify_error(
            e, tool_name=tool_name, tool_args=tool_args
        )

        print(
            f"  📎 [middleware] {tool_name} — "
            f"❌ {agent_error.code.name}: {agent_error.message[:80]} "
            f"({elapsed:.2f}s)"
        )

        # 结构化错误信息返回给 LLM
        error_msg = (
            f"⚠️ 工具「{tool_name}」执行出错\n"
            f"错误码: {agent_error.code.name} — {agent_error.code.value}\n"
            f"详情:   {agent_error.message}\n"
            f"级别:   {agent_error.severity.value}\n"
            f"建议:   {agent_error.action.value}\n"
            f"参数:   {json.dumps(tool_args, ensure_ascii=False)}"
        )

        return ToolMessage(
            content=error_msg,
            tool_call_id=request.tool_call["id"],
        )


# ===========================================================================
# 第六部分：第三层防线 —— Agent 顶层安全执行器
# ===========================================================================


class ErrorReporter:
    """错误日志收集与汇总 —— 配合链路回调使用。

    收集整次 Agent 执行过程中的所有错误，最后生成汇总报告。
    在生产环境中可接入日志系统/告警系统。
    """

    def __init__(self) -> None:
        self._errors: list[AgentError] = []
        self._start_time: float = 0

    def record(self, error: AgentError) -> None:
        """记录一条错误"""
        self._errors.append(error)

    @property
    def error_count(self) -> int:
        return len(self._errors)

    @property
    def has_critical(self) -> bool:
        return any(e.severity == Severity.CRITICAL for e in self._errors)

    def print_report(self) -> None:
        """打印错误汇总报告"""
        if not self._errors:
            print("  ✅ 本次运行无异常记录")
            return

        print(f"\n📊 异常汇总（共 {len(self._errors)} 条）：")
        print("─" * 68)

        # 按严重级别分组统计
        severity_counts: dict[str, int] = {}
        code_counts: dict[str, int] = {}

        for err in self._errors:
            sev = err.severity.value
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            code = err.code.name
            code_counts[code] = code_counts.get(code, 0) + 1

        # 级别统计
        print("  按级别统计:")
        for sev in ["CRITICAL", "ERROR", "WARNING", "INFO"]:
            count = severity_counts.get(sev, 0)
            if count > 0:
                icon = {"CRITICAL": "🔴", "ERROR": "🟠", "WARNING": "🟡", "INFO": "🔵"}
                print(f"    {icon.get(sev, '⚪')} {sev}: {count} 条")

        # 错误码统计
        print("  按错误码统计:")
        for code, count in sorted(code_counts.items()):
            desc = ErrorCode[code].value
            print(f"    {code} ({desc}): {count} 条")

        # 详细列表
        print("\n  详细列表:")
        for i, err in enumerate(self._errors, 1):
            ctx_tool = err.context.get("tool_name", "—")
            print(
                f"    {i}. [{err.code.name}] {err.severity.value} "
                f"| 工具: {ctx_tool} | {err.message[:60]}"
            )

        print("─" * 68)


class ErrorAwareLogger(BaseCallbackHandler):
    """带异常感知的链路日志处理器。

    继承 D15/D16 的日志思路，增加：
      - 用 classify_error 对工具错误进行标准化分类
      - 将分类后的 AgentError 记录到 ErrorReporter
    """

    def __init__(
        self,
        reporter: ErrorReporter,
        verbose: bool = False,
    ) -> None:
        super().__init__()
        self.reporter = reporter
        self.verbose = verbose
        self._step_count = 0
        self._timers: dict[str, float] = {}
        self._depth = 0

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

    # --- Chain 回调 ---

    def on_chain_start(self, serialized: dict, inputs: Any, **kwargs) -> None:
        self._step_count += 1
        name = kwargs.get("name") or "Chain"
        run_id = str(kwargs.get("run_id", ""))[:8]
        self._timers[run_id] = time.perf_counter()
        indent = self._indent()
        print(f"{indent}┌─[步骤 {self._step_count}] {name}")
        self._depth += 1

    def on_chain_end(self, outputs: Any, **kwargs) -> None:
        self._depth = max(0, self._depth - 1)
        run_id = str(kwargs.get("run_id", ""))[:8]
        elapsed = time.perf_counter() - self._timers.pop(
            run_id, time.perf_counter()
        )
        indent = self._indent()
        print(f"{indent}└─ ✅ 完成 ({self._format_duration(elapsed)})")

    def on_chain_error(self, error: BaseException, **kwargs) -> None:
        self._depth = max(0, self._depth - 1)
        run_id = str(kwargs.get("run_id", ""))[:8]
        elapsed = time.perf_counter() - self._timers.pop(
            run_id, time.perf_counter()
        )
        indent = self._indent()

        # 分类并记录
        agent_error = classify_error(error)
        self.reporter.record(agent_error)

        print(
            f"{indent}└─ ❌ [{agent_error.code.name}] "
            f"{self._truncate(str(error), 80)} "
            f"({self._format_duration(elapsed)})"
        )

    # --- LLM 回调 ---

    def on_chat_model_start(
        self, serialized: dict, messages: list, **kwargs
    ) -> None:
        run_id = str(kwargs.get("run_id", ""))[:8]
        self._timers[run_id] = time.perf_counter()
        indent = self._indent()
        msg_count = sum(len(m) for m in messages)
        print(f"{indent}🤖 ChatModel 调用 ({msg_count} 条消息)")

    def on_llm_end(self, response: Any, **kwargs) -> None:
        run_id = str(kwargs.get("run_id", ""))[:8]
        elapsed = time.perf_counter() - self._timers.pop(
            run_id, time.perf_counter()
        )
        indent = self._indent()
        print(f"{indent}✅ LLM 返回 ({self._format_duration(elapsed)})")

    # --- 工具回调 ---

    def on_tool_start(
        self, serialized: dict, input_str: str, **kwargs
    ) -> None:
        run_id = str(kwargs.get("run_id", ""))[:8]
        self._timers[run_id] = time.perf_counter()
        name = (serialized or {}).get("name", "Unknown")
        indent = self._indent()
        print(f"{indent}🔧 工具调用: {name}")
        if self.verbose:
            print(
                f"{indent}   参数: {self._truncate(input_str, 100)}"
            )

    def on_tool_end(self, output: str, **kwargs) -> None:
        run_id = str(kwargs.get("run_id", ""))[:8]
        elapsed = time.perf_counter() - self._timers.pop(
            run_id, time.perf_counter()
        )
        indent = self._indent()
        print(f"{indent}✅ 工具返回 ({self._format_duration(elapsed)})")

    def on_tool_error(self, error: BaseException, **kwargs) -> None:
        run_id = str(kwargs.get("run_id", ""))[:8]
        elapsed = time.perf_counter() - self._timers.pop(
            run_id, time.perf_counter()
        )
        indent = self._indent()

        # 分类并记录到 reporter
        agent_error = classify_error(error)
        self.reporter.record(agent_error)

        print(
            f"{indent}❌ 工具错误 [{agent_error.code.name}] "
            f"{self._truncate(str(error), 80)} "
            f"({self._format_duration(elapsed)})"
        )
        if self.verbose:
            print(
                f"{indent}   建议: {agent_error.action.value}"
            )


# ===========================================================================
# 第七部分：工具定义
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


_PATENTS: list[dict] = _load_patents()


@tool(
    "patent_search",
    description="根据关键词搜索专利数据库，返回匹配的专利列表。",
)
def patent_search(keyword: str) -> str:
    """根据关键词搜索专利数据库。

    Args:
        keyword: 搜索关键词，长度必须在 2-50 个字符之间。
    """
    if not keyword or not keyword.strip():
        raise ValueError("搜索关键词不能为空，请提供有效的关键词。")

    keyword = keyword.strip()
    if len(keyword) < 2:
        raise ValueError(
            f"关键词「{keyword}」太短（{len(keyword)}字符），至少需要2个字符。"
        )
    if len(keyword) > 50:
        raise ValueError(
            f"关键词太长（{len(keyword)}字符），最多50个字符。"
        )

    results = []
    for patent in _PATENTS:
        searchable = (
            patent.get("title", "")
            + patent.get("title_cn", "")
            + patent.get("abstract", "")
        )
        if keyword.lower() in searchable.lower():
            results.append(patent)

    if not results:
        return f"未找到与「{keyword}」相关的专利。请尝试更换关键词。"

    lines = [f"🔍 找到 {len(results)} 件与「{keyword}」相关的专利：\n"]
    for i, p in enumerate(results, 1):
        lines.append(
            f"  [{i}] {p['patent_id']} — {p['title_cn']}\n"
            f"      申请人: {p['applicant']}\n"
            f"      申请日: {p['filing_date']}  |  状态: {p['status']}\n"
        )
    return "\n".join(lines)


@tool(
    "unstable_external_api",
    description="（不稳定 API）查询外部专利数据库，可能会出错。",
)
def unstable_external_api(query: str) -> str:
    """调用不稳定的外部 API —— 始终抛出连接错误。

    Args:
        query: 查询内容。
    """
    raise ConnectionError(
        "外部专利数据库连接失败：Connection refused (errno=111)。"
    )


@tool(
    "malformed_json_api",
    description="（故障 API）返回损坏的 JSON 数据。",
)
def malformed_json_api(query: str) -> str:
    """模拟返回格式损坏的数据。

    Args:
        query: 查询内容。
    """
    # 模拟 JSON 解析失败
    raise json.JSONDecodeError(
        "Expecting property name enclosed in double quotes",
        doc="{invalid_json:",
        pos=15,
    )


@tool(
    "calculator",
    description="执行基本数学运算。支持加、减、乘、除。",
)
def calculator(a: float, b: float, operation: str) -> str:
    """执行两个数的基本算术运算。

    Args:
        a: 第一个数字。
        b: 第二个数字。
        operation: 运算类型，可选 add/subtract/multiply/divide。
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
            "支持: add, subtract, multiply, divide。"
        )
    return f"{a} {op} {b} = {result}"


# ===========================================================================
# 第八部分：构建 Agent + 安全执行
# ===========================================================================


def build_agent(model_name: str = "qwen2.5:7b"):
    """构建带三层错误防护的 Agent。

    防护层次：
      第一层: error_handler_middleware — 工具级错误拦截
      第二层: ModelRetryMiddleware     — 模型调用自动重试
      第三层: safe_invoke              — 顶层 try/except 兜底
    """
    agent = create_agent(
        model=ChatOllama(model=model_name, temperature=0),
        tools=[
            patent_search,
            unstable_external_api,
            malformed_json_api,
            calculator,
        ],
        system_prompt=(
            "你是一名专利分析助手。你可以搜索专利、进行计算。请用中文回复。\n"
            "注意：\n"
            "- 搜索专利使用 patent_search 工具\n"
            "- 数学计算使用 calculator 工具\n"
            "- 如果工具返回错误信息，请仔细阅读错误码和建议操作，\n"
            "  向用户解释情况并采取建议的恢复动作\n"
            "- 错误码格式为 [E1001]，级别有 INFO/WARNING/ERROR/CRITICAL"
        ),
        middleware=[
            error_handler_middleware,
            # 模型调用自动重试（第二层防线的一部分）
            ModelRetryMiddleware(
                max_retries=2,
                on_failure="continue",
                backoff_factor=1.5,
                initial_delay=0.5,
            ),
        ],
    )
    return agent


def safe_invoke(
    agent,
    query: str,
    verbose: bool = False,
) -> None:
    """第三层防线 —— Agent 顶层安全执行器。

    即使前两层防线都未能拦截的异常（如 Agent 框架自身 bug），
    也在这里被兜底捕获，绝不崩溃。
    """
    reporter = ErrorReporter()
    logger = ErrorAwareLogger(reporter=reporter, verbose=verbose)

    print("=" * 68)
    print("📋 D17 统一异常处理演示")
    print(f"   问题: {query}")
    print(f"   模式: {'详细' if verbose else '简要'}")
    print("=" * 68)

    start_time = time.perf_counter()
    is_streaming_text = False

    try:
        for event in agent.stream(
            {"messages": [("user", query)]},
            stream_mode="messages",
            config={"callbacks": [logger]},
        ):
            msg, metadata = event
            node = metadata.get("langgraph_node", "")

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
                # 检测是否包含错误码，标记为错误
                is_error = "⚠️" in msg.content or "[E" in msg.content
                icon = "⚠️" if is_error else "🔧"
                print(f"{icon} [{msg.name}] → {preview}")

            # AI 最终回复
            if node == "model" and msg.content:
                if not is_streaming_text:
                    print("\n🤖 AI 回复: ", end="")
                    is_streaming_text = True
                print(msg.content, end="", flush=True)

        if is_streaming_text:
            print()

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断了操作。")
        reporter.record(
            AgentError(
                code=ErrorCode.E4099,
                message="用户主动中断",
                severity=Severity.INFO,
                action=SuggestedAction.ABORT,
            )
        )

    except Exception as e:
        # 第三层兜底：前两层都没拦住的异常
        agent_error = classify_error(e)
        reporter.record(agent_error)

        print(f"\n\n❌ Agent 运行出错 [{agent_error.code.name}]")
        print(f"   类型: {type(e).__name__}")
        print(f"   详情: {e}")
        print(f"   级别: {agent_error.severity.value}")
        print(f"   建议: {agent_error.action.value}")

        if verbose:
            print("\n📋 完整堆栈:")
            traceback.print_exc()

    elapsed = time.perf_counter() - start_time

    print("\n" + "─" * 68)
    print(f"⏱️  总耗时: {elapsed:.2f}s")

    # 打印异常汇总
    reporter.print_report()

    print("=" * 68)


# ===========================================================================
# 第九部分：错误码定义表输出
# ===========================================================================


def print_error_codes() -> None:
    """打印完整的错误码定义表"""
    print("\n📋 Agent 错误码定义表")
    print("=" * 72)
    print(f"{'错误码':<8} {'分类':<12} {'描述':<25} {'默认级别':<10} {'默认动作'}")
    print("─" * 72)

    # 按类别分组
    current_category = ""
    for code in ErrorCode:
        # 根据编码前缀分类
        prefix = code.name[1]  # E1xxx → "1"
        category = {
            "1": "🔧 工具层",
            "2": "🤖 模型层",
            "3": "📄 解析层",
            "4": "⚙️  系统层",
        }.get(prefix, "❓ 未知")

        if category != current_category:
            current_category = category
            print(f"\n  {category}")

        # 查找默认的严重级别和建议动作
        default_sev = "ERROR"
        default_act = "重试"
        for _exc_type, (ec, sev, act) in _ERROR_CLASSIFICATION.items():
            if ec == code:
                default_sev = sev.value
                default_act = act.value
                break

        print(f"  {code.name:<8} {category:<12} {code.value:<25} {default_sev:<10} {default_act}")

    print("=" * 72)


# ===========================================================================
# 第十部分：CLI 入口
# ===========================================================================


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="D17: 解析与异常层 — 统一异常处理 + 错误码分类"
    )
    parser.add_argument("--query", "-q", help="要分析的问题")
    parser.add_argument(
        "--test-errors",
        action="store_true",
        help="只运行错误场景测试",
    )
    parser.add_argument(
        "--show-codes",
        action="store_true",
        help="打印错误码定义表",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细模式（显示完整错误堆栈）",
    )
    parser.add_argument(
        "--model",
        default="qwen2.5:7b",
        help="Ollama 模型名称（默认 qwen2.5:7b）",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # 打印错误码定义表
    if args.show_codes:
        print_error_codes()
        return 0

    # 构建 Agent
    print("🚀 D17 — 统一异常处理（三层防线 + 标准化错误码）")
    print("=" * 50)
    agent = build_agent(model_name=args.model)

    # 指定问题模式
    if args.query:
        safe_invoke(agent, args.query, verbose=args.verbose)
        return 0

    # 错误场景测试
    if args.test_errors:
        print("\n" + "🔥" * 30)
        print("   统一异常处理测试 — 6 种错误场景")
        print("🔥" * 30)

        error_queries = [
            # E1001: 输入校验 — 关键词太短
            ("E1001 输入校验", "用关键词 'X' 搜索专利"),
            # E1003: 外部服务不可用 — ConnectionError
            ("E1003 服务不可用", '使用 unstable_external_api 查询"量子计算"'),
            # E3001: JSON 解析 — JSONDecodeError
            ("E3001 JSON解析", '使用 malformed_json_api 查询"纳米材料"'),
            # E1001: 参数错误 — 除以零
            ("E1001 参数错误", "用 calculator 计算 100 除以 0"),
            # E1004: 空结果 — 搜索无匹配
            ("E1004 空结果", '搜索关于"反物质推进引擎"的专利'),
            # E1001: 参数类型错误 — 无效运算
            ("E1001 无效运算", "用 calculator 对 5 和 3 执行 power 运算"),
        ]

        for i, (scenario, query) in enumerate(error_queries, 1):
            print(f"\n{'─' * 60}")
            print(f"📌 错误场景 {i}/{len(error_queries)}: {scenario}")
            print(f"{'─' * 60}")
            safe_invoke(agent, query, verbose=args.verbose)

        return 0

    # 默认模式：完整演示
    print("\n" + "✅" * 30)
    print("   正常场景 — 验证错误处理不影响正常功能")
    print("✅" * 30)

    normal_queries = [
        "搜索有关锂电池材料的专利",
        "计算 3.14 乘以 2.72",
    ]
    for query in normal_queries:
        safe_invoke(agent, query, verbose=args.verbose)

    print("\n" + "🔥" * 30)
    print("   错误场景 — 三层防线演示")
    print("🔥" * 30)

    error_queries = [
        '使用 unstable_external_api 查询"新能源"相关专利',
        '使用 malformed_json_api 查询"人工智能"',
        "用 calculator 计算 100 除以 0",
    ]
    for query in error_queries:
        safe_invoke(agent, query, verbose=args.verbose)

    # 打印错误码速查表
    print_error_codes()

    print("\n🏁 D17 演示完毕！")
    print("关键收获：")
    print("  1. ErrorCode 枚举为每种错误分配唯一编码（E1001-E4099）")
    print("  2. AgentError 统一异常类携带 错误码/级别/建议动作")
    print("  3. classify_error 自动将任意异常映射为标准化 AgentError")
    print("  4. 三层防线：工具装饰器 → 中间件 → 顶层兜底")
    print("  5. ErrorReporter 汇总报告便于定位和改进")
    print("\n  D5 → D16 → D17 演进路线：")
    print("    D5:  工具内 try/except → 返回字符串（临时方案）")
    print("    D16: middleware 拦截   → ToolMessage（工程化方案）")
    print("    D17: 三层统一异常     → 错误码+级别+动作（生产级方案）")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
D20 — 端到端串联：把 cli_v1 迁移到可复用链路
=============================================

学习要点（综合运用 D15-D18 + 回顾 D13 cli_v1）：
  1. LCEL 管道 — 将 D13 单体脚本拆解为可组合的 Runnable 步骤
  2. 工具集成 — D16 的 @tool 装饰器 + middleware 错误拦截
  3. 异常体系 — D17 的 ErrorCode + AgentError 统一异常
  4. 上下文管理 — D18 的 ContextBuilder 管理多轮对话
  5. 可复用架构 — 各模块独立，可单独测试和替换

D13 → D20 的演进：
  D13: 单体脚本（分析逻辑 + CLI + 规则 + LLM 混在一起）
  D20: 可复用链路架构（清晰分层 + 统一入口 + 错误处理 + 上下文管理）

架构对比：
  D13 cli_v1.py:
    └─ 所有逻辑在一个文件里（~1000行），职责混合
       ├─ Schema 定义
       ├─ 规则分析 + LLM 分析（两套独立逻辑）
       ├─ CLI 入口
       └─ 验收用例

  D20 cli_v2.py:
    └─ 分层架构，各层可复用
       ├─ 分析管道 AnalysisPipeline（统一入口，策略模式切换规则/LLM）
       ├─ 工具注册表 ToolRegistry（集中管理，自动发现）
       ├─ 异常防护层 SafeAnalyzer（D17 的 classify_error 集成）
       ├─ 上下文管理 ContextManager（D18 的 ContextBuilder 集成）
       └─ CLI 入口（薄壳，只做参数解析和格式化输出）

运行方式：
  # 默认模式（规则分析）
  ./run lecture20
  ./run lecture20 --query "搜索锂电池相关专利"

  # LLM 模式
  ./run lecture20 --query "搜索锂电池相关专利" --llm

  # 多轮对话模式（交互式）
  ./run lecture20 --chat

  # 验收测试（10 条用例）
  ./run lecture20 --check

  # 打印工具注册表
  ./run lecture20 --tools

验收标准：功能等价且结构更清晰
  - D13 cli_v1 的 10 条验收用例全部通过
  - 代码分层清晰，各层职责明确
  - 异常不崩溃，错误信息包含标准化错误码
  - 多轮对话中上下文自动裁剪
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# 将项目根目录加入 sys.path
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT))

# 复用 D13 的 Schema 与规则分析逻辑
from lectures.lecture13.cli_v1 import (  # noqa: E402
    AcceptanceCase,
    Intent,
    PatentQuestionAnalysis,
    ToolName,
    analyze_question,
    analyze_with_llm,
)

# 复用 D17 的异常分类
from lectures.lecture17.error_wrapper import (  # noqa: E402
    ErrorReporter,
    classify_error,
)

# 复用 D18 的上下文管理
from lectures.lecture18.context_builder import ContextBuilder  # noqa: E402

# ===========================================================================
# 第一部分：工具注册表（集中管理，可复用）
# ===========================================================================


@dataclass
class ToolInfo:
    """工具注册信息"""

    name: str
    description: str
    required_params: list[str]
    optional_params: list[str] = field(default_factory=list)


class ToolRegistry:
    """工具注册表 — 集中管理所有可用工具的元信息。

    与 D13 的区别：
      D13: 工具 Schema 散落在代码各处
      D20: 集中注册，可遍历、可检索、可动态扩展
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolInfo] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """注册默认工具集"""
        self.register(
            ToolInfo(
                name="search_patent",
                description="根据关键词搜索专利数据库",
                required_params=["keyword"],
            )
        )
        self.register(
            ToolInfo(
                name="get_patent_detail",
                description="根据专利编号获取详情",
                required_params=["patent_id"],
            )
        )
        self.register(
            ToolInfo(
                name="compare_patents",
                description="对比两件专利",
                required_params=["patent_id_1", "patent_id_2"],
                optional_params=["comparison_focus"],
            )
        )

    def register(self, tool: ToolInfo) -> None:
        """注册一个工具"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolInfo | None:
        """按名称获取工具"""
        return self._tools.get(name)

    def list_all(self) -> list[ToolInfo]:
        """列出所有注册工具"""
        return list(self._tools.values())

    def print_registry(self) -> None:
        """打印工具注册表"""
        print("📋 工具注册表")
        print("=" * 60)
        for tool in self._tools.values():
            print(f"\n  🔧 {tool.name}")
            print(f"     描述: {tool.description}")
            print(f"     必填: {', '.join(tool.required_params)}")
            if tool.optional_params:
                print(f"     可选: {', '.join(tool.optional_params)}")
        print("\n" + "=" * 60)


# ===========================================================================
# 第二部分：异常防护层（D17 集成）
# ===========================================================================


class SafeAnalyzer:
    """带异常防护的分析器 — 整合 D17 的 classify_error。

    与 D13 的区别：
      D13: 异常用 try/except + print 处理，不规范
      D20: 异常统一分类为 AgentError，附带错误码和建议动作
    """

    def __init__(self, reporter: ErrorReporter | None = None) -> None:
        self._reporter = reporter or ErrorReporter()

    @property
    def reporter(self) -> ErrorReporter:
        return self._reporter

    def analyze_safe(
        self,
        question: str,
        use_llm: bool = False,
    ) -> PatentQuestionAnalysis | None:
        """安全分析 — 任何异常都不会崩溃。

        返回：
          成功时返回 PatentQuestionAnalysis
          失败时返回 None，错误记录到 reporter
        """
        start = time.perf_counter()

        try:
            if use_llm:
                result = analyze_with_llm(question, max_retries=1)
            else:
                result = analyze_question(question)
            elapsed = time.perf_counter() - start
            print(f"  ✅ 分析完成 ({elapsed:.2f}s)")
            return result

        except Exception as e:
            elapsed = time.perf_counter() - start
            agent_error = classify_error(
                e,
                tool_name="analyze_question" if not use_llm else "analyze_with_llm",
                tool_args={"question": question[:100]},
            )
            self._reporter.record(agent_error)
            print(
                f"  ❌ [{agent_error.code.name}] 分析失败 ({elapsed:.2f}s): "
                f"{agent_error.message[:80]}"
            )
            print(f"     建议: {agent_error.action.value}")
            return None


# ===========================================================================
# 第三部分：上下文管理器（D18 集成）
# ===========================================================================


class ContextManager:
    """多轮对话上下文管理器 — 整合 D18 的 ContextBuilder。

    与 D13 的区别：
      D13: 单轮分析，没有多轮上下文管理
      D20: 支持多轮对话，自动裁剪超长上下文
    """

    def __init__(self, max_tokens: int = 2000) -> None:
        self._builder = ContextBuilder(
            system_prompt=(
                "你是一名专利问题分析路由器。根据用户的自然语言问题，识别意图并路由到合适的工具。"
            ),
            max_tokens=max_tokens,
            strategy="hybrid",
        )
        self._history: list[dict[str, Any]] = []

    def add_question(self, question: str) -> None:
        """记录用户问题"""
        self._builder.add_human(question)
        self._history.append(
            {
                "role": "user",
                "content": question,
                "timestamp": time.time(),
            }
        )

    def add_result(self, result: PatentQuestionAnalysis) -> None:
        """记录分析结果"""
        summary = (
            f"意图={result.intent.value}, "
            f"工具={result.target_tool.value}, "
            f"置信度={result.confidence.value}"
        )
        self._builder.add_ai(summary)
        self._history.append(
            {
                "role": "assistant",
                "content": summary,
                "timestamp": time.time(),
            }
        )

    @property
    def turn_count(self) -> int:
        """对话轮次"""
        return len([h for h in self._history if h["role"] == "user"])

    @property
    def token_count(self) -> int:
        """当前 token 数"""
        return self._builder.raw_token_count

    def get_context_summary(self) -> str:
        """获取上下文状态摘要"""
        result = self._builder.build()
        return (
            f"轮次={self.turn_count}, "
            f"消息={self._builder.message_count}条, "
            f"原始Token={self._builder.raw_token_count}, "
            f"裁剪后Token={result.trimmed_tokens}"
        )


# ===========================================================================
# 第四部分：分析管道（统一入口）
# ===========================================================================


class AnalysisPipeline:
    """专利问题分析管道 — D20 核心。

    将 D13 的分散逻辑整合为统一的管道：
      1. 输入预处理（清理、标准化）
      2. 分析执行（规则 or LLM，SafeAnalyzer 保护）
      3. 结果验证（Schema 校验）
      4. 上下文更新（ContextManager 管理）
      5. 输出格式化

    与 D13 的区别：
      D13: analyze_question() 和 analyze_with_llm() 是两个独立函数
      D20: AnalysisPipeline 统一入口，内部策略模式切换
    """

    def __init__(
        self,
        use_llm: bool = False,
        max_context_tokens: int = 2000,
    ) -> None:
        self._use_llm = use_llm
        self._analyzer = SafeAnalyzer()
        self._context = ContextManager(max_tokens=max_context_tokens)
        self._registry = ToolRegistry()

    @property
    def reporter(self) -> ErrorReporter:
        return self._analyzer.reporter

    @property
    def context(self) -> ContextManager:
        return self._context

    @property
    def registry(self) -> ToolRegistry:
        return self._registry

    def analyze(self, question: str) -> PatentQuestionAnalysis | None:
        """分析问题的统一入口。

        流程：
          预处理 → 分析 → 验证 → 上下文更新 → 返回结果
        """
        # 步骤 1：预处理
        question = question.strip()
        if not question:
            print("  ⚠️ 问题不能为空")
            return None

        # 步骤 2：记录到上下文
        self._context.add_question(question)

        # 步骤 3：执行分析（SafeAnalyzer 保护）
        result = self._analyzer.analyze_safe(
            question,
            use_llm=self._use_llm,
        )

        if result is None:
            return None

        # 步骤 4：验证工具可用性
        tool_name = result.target_tool.value
        if tool_name != "none":
            tool_info = self._registry.get(tool_name)
            if tool_info is None:
                print(f"  ⚠️ 工具 {tool_name} 未在注册表中找到")

        # 步骤 5：更新上下文
        self._context.add_result(result)

        return result


# ===========================================================================
# 第五部分：输出格式化
# ===========================================================================


def format_result(result: PatentQuestionAnalysis, compact: bool = False) -> str:
    """格式化分析结果。

    compact=True: 单行摘要
    compact=False: 完整 JSON
    """
    if compact:
        return (
            f"意图={result.intent.value} | "
            f"工具={result.target_tool.value} | "
            f"置信度={result.confidence.value} | "
            f"关键词={result.extracted_entities.keywords}"
        )

    return json.dumps(
        result.model_dump(mode="json"),
        ensure_ascii=False,
        indent=2,
    )


# ===========================================================================
# 第六部分：验收测试（复用 D13 用例）
# ===========================================================================


def run_acceptance_check(pipeline: AnalysisPipeline) -> tuple[int, int]:
    """运行验收测试，返回 (通过数, 总数)。"""
    # 导入 D13 的完整验收用例（如果可用）
    try:
        from lectures.lecture13.cli_v1 import ACCEPTANCE_CASES

        cases = ACCEPTANCE_CASES
    except ImportError:
        print("  ⚠️ 无法导入 D13 验收用例，使用内置用例")
        cases = _BUILTIN_CASES

    passed = 0
    total = len(cases)

    print(f"\n📋 验收测试（共 {total} 条）")
    print("=" * 68)

    for i, case in enumerate(cases, 1):
        print(f"\n  [{i}/{total}] {case.question}")

        result = pipeline.analyze(case.question)
        if result is None:
            print("    ❌ 分析失败")
            continue

        # 检查意图
        intent_ok = result.intent == case.expected_intent
        tool_ok = result.target_tool == case.expected_tool

        # 检查关键词（如果有期望值）
        keyword_ok = True
        if case.expected_keywords:
            extracted = result.extracted_entities.keywords
            keyword_ok = all(
                any(ek.lower() in k.lower() for k in extracted) for ek in case.expected_keywords
            )

        all_ok = intent_ok and tool_ok and keyword_ok

        if all_ok:
            passed += 1
            print(f"    ✅ 通过 — {format_result(result, compact=True)}")
        else:
            details = []
            if not intent_ok:
                details.append(
                    f"意图: 期望={case.expected_intent.value}, 实际={result.intent.value}"
                )
            if not tool_ok:
                details.append(
                    f"工具: 期望={case.expected_tool.value}, 实际={result.target_tool.value}"
                )
            if not keyword_ok:
                details.append(
                    f"关键词: 期望={case.expected_keywords}, "
                    f"实际={result.extracted_entities.keywords}"
                )
            print(f"    ❌ 失败 — {'; '.join(details)}")

    print(f"\n{'=' * 68}")
    print(f"📊 结果: {passed}/{total} 通过 ({passed / total * 100:.0f}%)")
    print("=" * 68)

    return passed, total


# 内置基础用例（当 D13 不可用时的备选）
_BUILTIN_CASES = [
    AcceptanceCase(
        question="帮我搜索生物降解塑料相关专利",
        expected_intent=Intent.SEARCH,
        expected_tool=ToolName.SEARCH_PATENT,
        expected_keywords=["生物降解塑料"],
    ),
    AcceptanceCase(
        question="查看专利 JP2024-001 的详细信息",
        expected_intent=Intent.DETAIL_LOOKUP,
        expected_tool=ToolName.GET_PATENT_DETAIL,
    ),
    AcceptanceCase(
        question="对比 JP2024-001 和 JP2024-002 的区别",
        expected_intent=Intent.COMPARE,
        expected_tool=ToolName.COMPARE_PATENTS,
    ),
    AcceptanceCase(
        question="固态电池的关键技术是什么？",
        expected_intent=Intent.ANSWER_WITH_CONTEXT,
        expected_tool=ToolName.SEARCH_PATENT,
        expected_keywords=["固态电池"],
    ),
    AcceptanceCase(
        question="这个专利",
        expected_intent=Intent.CLARIFY,
        expected_tool=ToolName.NONE,
    ),
]


# ===========================================================================
# 第八部分：CLI 入口（交互式菜单，参考 D13 cli_v1 风格）
# ===========================================================================


EXAMPLE_QUESTIONS = """\
示例问题（可直接复制粘贴）：
  · 帮我搜索生物降解塑料相关专利
  · 查看 JP2024-002 的详细信息
  · JP2024-003 的申请人和状态是什么？
  · 对比 JP2024-001 和 JP2024-002 的 IPC 分类与差异
  · 有没有 Toyota 的固态电池相关专利？
  · 这个专利怎么样？（触发澄清意图）"""


def run_chat_mode(pipeline: AnalysisPipeline) -> None:
    """交互式多轮对话模式。"""
    print()
    print(EXAMPLE_QUESTIONS)
    print("-" * 60)

    while True:
        try:
            question = input("请输入要分析的专利问题: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 再见！")
            break

        if not question:
            continue

        if question.lower() in {"quit", "exit", "q"}:
            print("👋 再见！")
            break

        if question.lower() == "status":
            print(f"  📊 {pipeline.context.get_context_summary()}")
            continue

        if question.lower() == "report":
            pipeline.reporter.print_report()
            continue

        print()
        result = pipeline.analyze(question)

        if result is not None:
            print()
            print(format_result(result, compact=False))

        print("-" * 60)


def main() -> int:
    print("=" * 60)
    print("D20 专利问题分析 CLI v2")
    print("=" * 60)
    print("将自然语言专利问题解析为结构化 JSON。")
    print("综合运用 D15(链路) D16(工具) D17(异常) D18(上下文) 模块。")
    print()
    print("选择模式：")
    print("  1. LLM 模式 — 调用 qwen2.5:7b 结构化输出（约 30-60 秒）")
    print("  2. 规则模式 — 纯规则基线，即时响应")
    print("  3. 验收测试 — 运行 10 条规则验收")
    print("  4. 工具注册表 — 查看已注册工具")
    print("-" * 60)

    try:
        choice = input("请选择模式 [1/2/3/4]（默认 1）: ").strip() or "1"
    except (EOFError, KeyboardInterrupt):
        print("\n👋 再见！")
        return 0

    if choice == "1":
        pipeline = AnalysisPipeline(use_llm=True)
        run_chat_mode(pipeline)
        return 0

    if choice == "2":
        pipeline = AnalysisPipeline(use_llm=False)
        run_chat_mode(pipeline)
        return 0

    if choice == "3":
        pipeline = AnalysisPipeline(use_llm=False)
        passed, total = run_acceptance_check(pipeline)
        return 0 if passed == total else 1

    if choice == "4":
        pipeline = AnalysisPipeline(use_llm=False)
        pipeline.registry.print_registry()
        return 0

    print(f"⚠️ 无效选择: {choice}，请输入 1-4")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

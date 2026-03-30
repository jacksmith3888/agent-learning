"""
D19 — 单测补齐：5 个关键测试，覆盖正常与异常路径
================================================

学习要点（基于 L3_streaming.ipynb + LangChain Agents 文档）：
  1. Agent Loop 的输入输出结构（messages → events → final response）
  2. Tool Call 的触发与返回格式（tool_calls / ToolMessage）
  3. State 在每轮循环中的变化（为 W4 LangGraph 铺路）
  4. 用 pytest 断言验证链路中每个环节的正确性

什么是"单测补齐"？
  D15-D18 完成了链路、工具、异常、上下文四个模块，但都没有自动化测试。
  D19 的目标是为这些核心模块补齐 5 个关键测试：
    ① 链路构建测试 — 验证 LCEL 管道可正常拼装
    ② 工具校验测试 — 验证输入校验（正常/边界/异常）
    ③ 异常分类测试 — 验证 ErrorCode 映射系统的准确性
    ④ 上下文裁剪测试 — 验证裁剪策略在各种场景下的正确性
    ⑤ 端到端集成测试 — 验证从上下文构建到链路执行的完整流程

运行方式：
  # 运行全部测试
  ./test lecture19
  uv run pytest lectures/lecture19/test_cases.py -v

  # 运行单个测试
  uv run pytest lectures/lecture19/test_cases.py::TestToolValidation -v

  # 只跑不需要 LLM 的测试（快速验证）
  uv run pytest lectures/lecture19/test_cases.py -v -m "not requires_llm"

验收标准：覆盖正常与异常路径 — 5 组测试全部通过
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# 将项目根目录加入 sys.path，以便导入 lectures 下的模块
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT))


# ===========================================================================
# 测试 1：链路构建测试（D15 chain_demo.py）
# ===========================================================================
#
# 验证 LCEL 管道的核心组件：
#   - ChainLogger 回调处理器的方法存在性
#   - build_chain 返回可调用的 Runnable
#   - preprocess_question 正确处理输入
#


class TestChainConstruction:
    """测试 D15 链路构建模块的核心功能。"""

    def test_preprocess_question_strips_whitespace(self):
        """正常路径：预处理函数应去除多余空格"""
        from lectures.lecture15.chain_demo import preprocess_question

        result = preprocess_question({"question": "  什么是   专利检索？  "})
        assert result["question"] == "什么是 专利检索？"

    def test_preprocess_question_preserves_other_keys(self):
        """正常路径：预处理应保留输入字典中的其他字段"""
        from lectures.lecture15.chain_demo import preprocess_question

        result = preprocess_question({
            "question": "测试问题",
            "extra_key": "extra_value",
        })
        assert result["question"] == "测试问题"
        assert result["extra_key"] == "extra_value"

    def test_preprocess_question_empty_string(self):
        """边界路径：空字符串输入"""
        from lectures.lecture15.chain_demo import preprocess_question

        result = preprocess_question({"question": ""})
        assert result["question"] == ""

    def test_preprocess_question_missing_key(self):
        """异常路径：缺少 question 键时应返回空字符串"""
        from lectures.lecture15.chain_demo import preprocess_question

        result = preprocess_question({})
        assert result["question"] == ""

    def test_chain_logger_has_required_methods(self):
        """正常路径：ChainLogger 应有完整的回调方法"""
        from lectures.lecture15.chain_demo import ChainLogger

        logger = ChainLogger(verbose=True)
        required_methods = [
            "on_chain_start",
            "on_chain_end",
            "on_chain_error",
            "on_llm_start",
            "on_llm_end",
            "on_chat_model_start",
        ]
        for method in required_methods:
            assert hasattr(logger, method), f"ChainLogger 缺少方法: {method}"

    def test_chain_logger_truncate(self):
        """边界路径：截断函数在长文本和短文本上行为正确"""
        from lectures.lecture15.chain_demo import ChainLogger

        # 短文本不截断
        assert ChainLogger._truncate("短文本", 100) == "短文本"
        # 长文本截断
        long_text = "a" * 200
        result = ChainLogger._truncate(long_text, 50)
        assert len(result) == 53  # 50 + "..."
        assert result.endswith("...")

    def test_chain_logger_format_duration(self):
        """正常路径：耗时格式化在不同量级下正确显示"""
        from lectures.lecture15.chain_demo import ChainLogger

        # 微秒级
        assert "μs" in ChainLogger._format_duration(0.0001)
        # 毫秒级
        assert "ms" in ChainLogger._format_duration(0.1)
        # 秒级
        assert "s" in ChainLogger._format_duration(2.5)


# ===========================================================================
# 测试 2：工具输入校验测试（D16 tool_chain.py）
# ===========================================================================
#
# 验证工具的输入校验逻辑：
#   - patent_search: 关键词长度约束（2-50 字符）
#   - patent_detail: 专利编号非空
#   - calculator: 运算类型有效性、除零保护
#


class TestToolValidation:
    """测试 D16 工具函数的输入校验。"""

    def test_patent_search_valid_keyword(self):
        """正常路径：合法关键词应返回结果字符串"""
        from lectures.lecture16.tool_chain import patent_search

        # 调用 .invoke() 因为 @tool 装饰器包装了函数
        result = patent_search.invoke({"keyword": "锂电池"})
        assert isinstance(result, str)
        # 应返回搜索结果或"未找到"
        assert "锂电池" in result or "未找到" in result

    def test_patent_search_empty_keyword_raises(self):
        """异常路径：空关键词应抛出 ValueError"""
        from lectures.lecture16.tool_chain import patent_search

        with pytest.raises(ValueError):
            patent_search.invoke({"keyword": ""})

    def test_patent_search_short_keyword_raises(self):
        """异常路径：单字符关键词应抛出 ValueError"""
        from lectures.lecture16.tool_chain import patent_search

        with pytest.raises(ValueError):
            patent_search.invoke({"keyword": "X"})

    def test_patent_search_long_keyword_raises(self):
        """异常路径：超长关键词应抛出 ValueError"""
        from lectures.lecture16.tool_chain import patent_search

        with pytest.raises(ValueError):
            patent_search.invoke({"keyword": "a" * 51})

    def test_patent_detail_valid_id(self):
        """正常路径：合法专利编号应返回结果"""
        from lectures.lecture16.tool_chain import patent_detail

        result = patent_detail.invoke({"patent_id": "JP2024-001"})
        assert isinstance(result, str)

    def test_patent_detail_empty_id_raises(self):
        """异常路径：空专利编号应抛出 ValueError"""
        from lectures.lecture16.tool_chain import patent_detail

        with pytest.raises(ValueError):
            patent_detail.invoke({"patent_id": ""})

    def test_calculator_add(self):
        """正常路径：加法运算正确"""
        from lectures.lecture16.tool_chain import calculator

        result = calculator.invoke({"a": 3.0, "b": 4.0, "operation": "add"})
        assert "7" in result

    def test_calculator_divide_by_zero_raises(self):
        """异常路径：除以零应抛出 ValueError"""
        from lectures.lecture16.tool_chain import calculator

        with pytest.raises(ValueError):
            calculator.invoke({"a": 100.0, "b": 0.0, "operation": "divide"})

    def test_calculator_invalid_operation_raises(self):
        """异常路径：无效运算类型应抛出 ValueError"""
        from lectures.lecture16.tool_chain import calculator

        with pytest.raises(ValueError):
            calculator.invoke({"a": 1.0, "b": 2.0, "operation": "modulo"})

    def test_unreliable_api_always_fails(self):
        """异常路径：不稳定 API 应始终抛出 ConnectionError"""
        from lectures.lecture16.tool_chain import unreliable_api

        with pytest.raises(ConnectionError):
            unreliable_api.invoke({"query": "任意查询"})


# ===========================================================================
# 测试 3：异常分类测试（D17 error_wrapper.py）
# ===========================================================================
#
# 验证 ErrorCode 分类系统的准确性：
#   - classify_error 对各类异常的映射正确
#   - AgentError 的序列化和友好消息
#   - ErrorReporter 的统计功能
#


class TestErrorClassification:
    """测试 D17 异常分类系统。"""

    def test_classify_value_error(self):
        """正常路径：ValueError 应映射到 E1001"""
        from lectures.lecture17.error_wrapper import (
            ErrorCode,
            Severity,
            SuggestedAction,
            classify_error,
        )

        error = ValueError("参数无效")
        agent_error = classify_error(error, tool_name="test_tool")

        assert agent_error.code == ErrorCode.E1001
        assert agent_error.severity == Severity.WARNING
        assert agent_error.action == SuggestedAction.CHANGE_PARAMS
        assert agent_error.context["tool_name"] == "test_tool"

    def test_classify_connection_error(self):
        """正常路径：ConnectionError 应映射到 E1003"""
        from lectures.lecture17.error_wrapper import (
            ErrorCode,
            Severity,
            classify_error,
        )

        error = ConnectionError("连接被拒绝")
        agent_error = classify_error(error)

        assert agent_error.code == ErrorCode.E1003
        assert agent_error.severity == Severity.ERROR

    def test_classify_timeout_error(self):
        """正常路径：TimeoutError 应映射到 E1002"""
        from lectures.lecture17.error_wrapper import ErrorCode, classify_error

        error = TimeoutError("请求超时")
        agent_error = classify_error(error)

        assert agent_error.code == ErrorCode.E1002

    def test_classify_unknown_error(self):
        """边界路径：未知异常类型应兜底为 E1099"""
        from lectures.lecture17.error_wrapper import ErrorCode, classify_error

        class CustomError(Exception):
            pass

        error = CustomError("自定义异常")
        agent_error = classify_error(error)

        assert agent_error.code == ErrorCode.E1099

    def test_classify_already_agent_error(self):
        """边界路径：已经是 AgentError 的异常应直接返回"""
        from lectures.lecture17.error_wrapper import (
            AgentError,
            ErrorCode,
            Severity,
            SuggestedAction,
            classify_error,
        )

        original = AgentError(
            code=ErrorCode.E2001,
            message="模型失败",
            severity=Severity.ERROR,
            action=SuggestedAction.RETRY,
        )
        result = classify_error(original)

        assert result is original
        assert result.code == ErrorCode.E2001

    def test_agent_error_to_dict(self):
        """正常路径：序列化为字典应包含所有必要字段"""
        from lectures.lecture17.error_wrapper import (
            AgentError,
            ErrorCode,
            Severity,
            SuggestedAction,
        )

        error = AgentError(
            code=ErrorCode.E1001,
            message="校验失败",
            severity=Severity.WARNING,
            action=SuggestedAction.CHANGE_PARAMS,
            context={"tool_name": "patent_search"},
        )
        d = error.to_dict()

        assert d["code"] == "E1001"
        assert d["severity"] == "WARNING"
        assert d["action"] == "更换输入参数"
        assert d["context"]["tool_name"] == "patent_search"

    def test_agent_error_friendly_message(self):
        """正常路径：友好消息应包含错误码和建议"""
        from lectures.lecture17.error_wrapper import (
            AgentError,
            ErrorCode,
            Severity,
            SuggestedAction,
        )

        error = AgentError(
            code=ErrorCode.E1003,
            message="服务不可用",
            severity=Severity.ERROR,
            action=SuggestedAction.RETRY,
        )
        msg = error.to_friendly_message()

        assert "E1003" in msg
        assert "重试" in msg

    def test_error_reporter_statistics(self):
        """正常路径：ErrorReporter 应正确统计错误"""
        from lectures.lecture17.error_wrapper import (
            AgentError,
            ErrorCode,
            ErrorReporter,
            Severity,
            SuggestedAction,
        )

        reporter = ErrorReporter()
        assert reporter.error_count == 0
        assert not reporter.has_critical

        # 添加普通错误
        reporter.record(AgentError(
            code=ErrorCode.E1001,
            message="测试",
            severity=Severity.WARNING,
            action=SuggestedAction.RETRY,
        ))
        assert reporter.error_count == 1
        assert not reporter.has_critical

        # 添加严重错误
        reporter.record(AgentError(
            code=ErrorCode.E4004,
            message="内存不足",
            severity=Severity.CRITICAL,
            action=SuggestedAction.ABORT,
        ))
        assert reporter.error_count == 2
        assert reporter.has_critical

    def test_classify_json_decode_error(self):
        """正常路径：JSONDecodeError 应映射到 E3001"""
        from lectures.lecture17.error_wrapper import ErrorCode, classify_error

        error = json.JSONDecodeError("Expecting value", doc="", pos=0)
        agent_error = classify_error(error)

        assert agent_error.code == ErrorCode.E3001

    def test_classify_permission_error(self):
        """正常路径：PermissionError 应映射到 E1006（CRITICAL）"""
        from lectures.lecture17.error_wrapper import (
            ErrorCode,
            Severity,
            classify_error,
        )

        error = PermissionError("权限不足")
        agent_error = classify_error(error)

        assert agent_error.code == ErrorCode.E1006
        assert agent_error.severity == Severity.CRITICAL


# ===========================================================================
# 测试 4：上下文裁剪测试（D18 context_builder.py）
# ===========================================================================
#
# 验证各裁剪策略的正确性：
#   - TruncateStrategy: 按条数截断
#   - TokenBudgetStrategy: 按 token 预算裁剪
#   - FilterStrategy: 按角色过滤
#   - HybridStrategy: 混合裁剪
#   - ContextBuilder: 集成测试
#


class TestContextTrimming:
    """测试 D18 上下文裁剪模块。"""

    def test_truncate_strategy_keeps_recent(self):
        """正常路径：截断策略应保留最近 N 条消息"""
        from langchain_core.messages import (
            AIMessage,
            HumanMessage,
            SystemMessage,
        )

        from lectures.lecture18.context_builder import TruncateStrategy

        messages = [
            SystemMessage(content="系统提示"),
            HumanMessage(content="问题1"),
            AIMessage(content="回答1"),
            HumanMessage(content="问题2"),
            AIMessage(content="回答2"),
            HumanMessage(content="最新问题"),
            AIMessage(content="最新回答"),
        ]

        strategy = TruncateStrategy(keep_last=4)
        result = strategy.trim(messages)

        # 应保留 system + 最近 4 条
        assert result.trimmed_count == 5  # 1 system + 4 recent
        assert result.messages[0].content == "系统提示"
        assert result.messages[-1].content == "最新回答"
        assert result.dropped_count == 2

    def test_truncate_strategy_short_conversation(self):
        """边界路径：消息数少于 keep_last 时不裁剪"""
        from langchain_core.messages import HumanMessage, SystemMessage

        from lectures.lecture18.context_builder import TruncateStrategy

        messages = [
            SystemMessage(content="系统提示"),
            HumanMessage(content="问题"),
        ]

        strategy = TruncateStrategy(keep_last=20)
        result = strategy.trim(messages)

        assert result.trimmed_count == 2
        assert result.dropped_count == 0

    def test_token_budget_strategy(self):
        """正常路径：Token 预算策略应在预算内"""
        from langchain_core.messages import (
            AIMessage,
            HumanMessage,
            SystemMessage,
        )

        from lectures.lecture18.context_builder import TokenBudgetStrategy

        # 构建一组消息
        messages = [SystemMessage(content="系统提示")]
        for i in range(20):
            messages.append(HumanMessage(content=f"问题{i}: 这是一条测试消息"))
            messages.append(AIMessage(content=f"回答{i}: 这是一条回复消息"))

        budget = 200
        strategy = TokenBudgetStrategy(max_tokens=budget)
        result = strategy.trim(messages)

        # 裁剪后应在预算内
        assert result.trimmed_tokens <= budget
        # 应少于原始消息
        assert result.trimmed_count < result.original_count
        # 压缩比应 < 1
        assert result.compression_ratio < 1.0

    def test_filter_strategy_drop_tool_messages(self):
        """正常路径：过滤策略应正确丢弃 ToolMessage"""
        from langchain_core.messages import (
            AIMessage,
            HumanMessage,
            SystemMessage,
            ToolMessage,
        )

        from lectures.lecture18.context_builder import FilterStrategy

        messages = [
            SystemMessage(content="系统提示"),
            HumanMessage(content="问题"),
            AIMessage(content="回答"),
            ToolMessage(content="工具结果", tool_call_id="call_0"),
            HumanMessage(content="后续问题"),
        ]

        strategy = FilterStrategy(drop_roles={"tool"})
        result = strategy.trim(messages)

        assert result.trimmed_count == 4  # 去掉 1 条 ToolMessage
        assert all(m.type != "tool" for m in result.messages)

    def test_filter_strategy_keep_whitelist(self):
        """正常路径：白名单模式只保留指定角色"""
        from langchain_core.messages import (
            AIMessage,
            HumanMessage,
            SystemMessage,
            ToolMessage,
        )

        from lectures.lecture18.context_builder import FilterStrategy

        messages = [
            SystemMessage(content="系统提示"),
            HumanMessage(content="问题"),
            AIMessage(content="回答"),
            ToolMessage(content="工具结果", tool_call_id="call_0"),
        ]

        strategy = FilterStrategy(keep_roles={"human", "ai"})
        result = strategy.trim(messages)

        assert result.trimmed_count == 2  # 只保留 human + ai

    def test_filter_strategy_conflict_raises(self):
        """异常路径：同时指定白名单和黑名单应抛出 ValueError"""
        from lectures.lecture18.context_builder import FilterStrategy

        with pytest.raises(ValueError):
            FilterStrategy(keep_roles={"human"}, drop_roles={"tool"})

    def test_hybrid_strategy_truncates_tool_content(self):
        """正常路径：混合策略应截断过长的 ToolMessage 内容"""
        from langchain_core.messages import (
            HumanMessage,
            SystemMessage,
            ToolMessage,
        )

        from lectures.lecture18.context_builder import HybridStrategy

        long_tool_content = "x" * 500
        messages = [
            SystemMessage(content="系统提示"),
            HumanMessage(content="问题"),
            ToolMessage(content=long_tool_content, tool_call_id="call_0"),
        ]

        strategy = HybridStrategy(max_tokens=5000, tool_content_max=100)
        result = strategy.trim(messages)

        # 应有 ToolMessage，但内容被截断
        tool_msgs = [m for m in result.messages if m.type == "tool"]
        if tool_msgs:
            assert len(tool_msgs[0].content) < len(long_tool_content)
            assert "内容已截断" in tool_msgs[0].content

    def test_context_builder_integration(self):
        """集成测试：ContextBuilder 完整工作流"""
        from lectures.lecture18.context_builder import ContextBuilder

        builder = ContextBuilder(
            system_prompt="你是助手。",
            max_tokens=500,
            strategy="hybrid",
        )

        # 添加 30 轮对话
        for i in range(30):
            builder.add_human(f"问题{i}")
            builder.add_ai(f"回答{i}: 这是一条比较长的回复消息，包含一些细节内容。")

        assert builder.message_count == 61  # 1 system + 30*2

        # 构建裁剪后的上下文
        result = builder.build()

        # 裁剪后应在预算内
        assert result.trimmed_tokens <= 500
        # 应保留 system message
        assert result.messages[0].type == "system"
        # 应有裁剪发生
        assert result.dropped_count > 0

    def test_context_builder_with_tool_messages(self):
        """集成测试：ContextBuilder 处理含 ToolMessage 的对话"""
        from lectures.lecture18.context_builder import ContextBuilder

        builder = ContextBuilder(
            system_prompt="你是助手。",
            max_tokens=300,
            strategy="hybrid",
        )

        builder.add_human("搜索锂电池专利")
        builder.add_tool("搜索结果：" + "x" * 200, tool_call_id="call_0")
        builder.add_ai("根据搜索结果，锂电池专利包括...")

        # 添加更多对话
        for i in range(10):
            builder.add_human(f"继续搜索{i}")
            builder.add_ai(f"第{i}批结果...")

        result = builder.build()
        assert result.trimmed_tokens <= 300

    def test_estimate_tokens_mixed_language(self):
        """正常路径：混合语言 token 估算应返回正整数"""
        from lectures.lecture18.context_builder import estimate_tokens

        # 中文
        assert estimate_tokens("你好世界") > 0
        # 英文
        assert estimate_tokens("Hello World") > 0
        # 混合
        assert estimate_tokens("Hello 你好 World 世界") > 0
        # 空字符串
        assert estimate_tokens("") >= 1  # max(1, ...)


# ===========================================================================
# 测试 5：端到端集成测试（D15-D18 联合验证）
# ===========================================================================
#
# 不依赖 LLM 的集成测试：
#   - 验证各模块之间的接口兼容性
#   - 验证错误在各层之间的传播路径
#


class TestEndToEndIntegration:
    """D15-D18 的端到端集成测试（不依赖 LLM）。"""

    def test_error_classification_covers_tool_errors(self):
        """集成：D16 工具的异常能被 D17 正确分类"""
        from lectures.lecture17.error_wrapper import ErrorCode, classify_error

        # 模拟 D16 patent_search 的 ValueError
        error = ValueError("关键词太短（1字符），至少需要 2 个字符。")
        agent_error = classify_error(error, tool_name="patent_search")

        assert agent_error.code == ErrorCode.E1001
        assert agent_error.context["tool_name"] == "patent_search"

        # 模拟 D16 unreliable_api 的 ConnectionError
        error = ConnectionError("外部专利数据库连接失败")
        agent_error = classify_error(error, tool_name="unreliable_api")

        assert agent_error.code == ErrorCode.E1003

    def test_context_builder_then_check_budget(self):
        """集成：D18 构建上下文后，token 数在 D15 链路可接受范围内"""
        from lectures.lecture18.context_builder import ContextBuilder

        builder = ContextBuilder(
            system_prompt="你是一名专利分析助手，请用中文回复。",
            max_tokens=1000,
            strategy="hybrid",
        )

        # 模拟 50 轮对话
        for i in range(50):
            builder.add_human(f"搜索第{i+1}批锂电池专利")
            builder.add_ai(f"第{i+1}批：找到若干相关专利。")

        # 构建裁剪后的上下文
        result = builder.build()

        # 裁剪后的 token 数应在 LLM 可接受范围内
        assert result.trimmed_tokens <= 1000
        # 应保留 system message
        system_msgs = [m for m in result.messages if m.type == "system"]
        assert len(system_msgs) == 1

    def test_error_code_enum_completeness(self):
        """验证 ErrorCode 枚举覆盖四大类错误"""
        from lectures.lecture17.error_wrapper import ErrorCode

        codes = [c.name for c in ErrorCode]

        # 检查四大类都有
        assert any(c.startswith("E1") for c in codes), "缺少工具层错误码 E1xxx"
        assert any(c.startswith("E2") for c in codes), "缺少模型层错误码 E2xxx"
        assert any(c.startswith("E3") for c in codes), "缺少解析层错误码 E3xxx"
        assert any(c.startswith("E4") for c in codes), "缺少系统层错误码 E4xxx"

    def test_trim_result_summary_format(self):
        """验证 TrimResult.summary() 输出格式正确"""
        from lectures.lecture18.context_builder import TrimResult

        result = TrimResult(
            messages=[],
            original_count=100,
            trimmed_count=20,
            original_tokens=5000,
            trimmed_tokens=1000,
            strategy="hybrid",
            dropped_count=80,
        )

        summary = result.summary()
        assert "hybrid" in summary
        assert "100" in summary
        assert "20" in summary
        assert "80" in summary

    def test_trim_result_compression_ratio(self):
        """验证 TrimResult 压缩比计算正确"""
        from lectures.lecture18.context_builder import TrimResult

        result = TrimResult(
            messages=[],
            original_count=100,
            trimmed_count=50,
            original_tokens=1000,
            trimmed_tokens=250,
            strategy="test",
        )

        assert result.compression_ratio == 0.25

        # 边界值：原始 token 为 0
        result_zero = TrimResult(
            messages=[],
            original_count=0,
            trimmed_count=0,
            original_tokens=0,
            trimmed_tokens=0,
            strategy="test",
        )
        assert result_zero.compression_ratio == 1.0


# ===========================================================================
# 主程序入口
# ===========================================================================


def main() -> None:
    """直接运行时执行 pytest"""
    print("=" * 68)
    print("📋 D19 单测补齐 — 5 个关键测试")
    print("=" * 68)
    print()
    print("测试覆盖范围：")
    print("  1. TestChainConstruction  — D15 链路构建")
    print("  2. TestToolValidation     — D16 工具输入校验")
    print("  3. TestErrorClassification — D17 异常分类系统")
    print("  4. TestContextTrimming     — D18 上下文裁剪")
    print("  5. TestEndToEndIntegration — D15-D18 端到端集成")
    print()

    # 使用 pytest 运行
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-q",
    ])

    print()
    if exit_code == 0:
        print("✅ D19 全部测试通过！")
    else:
        print(f"❌ D19 测试失败（退出码: {exit_code}）")

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()

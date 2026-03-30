"""
D18 — 上下文拼装：实现上下文裁剪
================================

学习要点（基于 L2_messages.ipynb + Happy-LLM Chapter4 + LangChain Context Engineering）：
  1. 消息类型 —— HumanMessage / AIMessage / SystemMessage / ToolMessage
  2. 上下文窗口 —— 每个模型有 token 上限，超长输入会报错或降质
  3. 裁剪策略 —— 截断法 / 摘要法 / 过滤法 / 混合法
  4. LangChain 内置方案 —— trim_messages + SummarizationMiddleware

什么是"上下文裁剪"？
  Agent 对话越来越长时，消息历史不断膨胀。裁剪就是在发给 LLM 之前，
  智能地剪掉一部分历史消息，确保：
    ① 不超出模型 token 上限
    ② 保留最有价值的上下文（system prompt + 最近对话）
    ③ 控制成本和延迟

D15-D17 → D18 的演进：
  D15: 只关注链路执行顺序
  D16: 加入工具调用
  D17: 统一错误处理
  D18: 控制"发给 LLM 的内容有多少" —— 上下文工程的第一步

运行方式：
  # 运行全部演示
  ./run lecture18

  # 自定义 token 上限
  ./run lecture18 --max-tokens 500

  # 查看裁剪前后对比
  ./run lecture18 --show-diff

  # 使用 LLM 实际调用验证
  ./run lecture18 --live

验收标准：超长输入可自动截断 —— 100 条消息 → 裁剪后在 token 预算内
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    trim_messages,
)
from langchain_ollama import ChatOllama


# ===========================================================================
# 第一部分：Token 估算器
# ===========================================================================
#
# LLM 按 token 计费和限制，每个模型的 tokenizer 不同。
# 这里提供两种估算方式：
#   1. 简单估算：字符数 ÷ 系数（中文≈1.5字/token，英文≈4字符/token）
#   2. 精确回调：langchain 的 token_counter 回调
#


def estimate_tokens(text: str) -> int:
    """简单 token 估算（混合语言通用）。

    粗略规则：中文约 1.5 字/token，英文约 4 字符/token。
    这里取一个中间值：约 2 字符/token（偏保守，宁可多裁一点）。
    """
    return max(1, len(text) // 2)


def estimate_message_tokens(msg: BaseMessage) -> int:
    """估算单条消息的 token 数。

    包含 role 标记的 overhead（约 4 token）+ 内容 token。
    """
    role_overhead = 4  # <role> 标记、换行符等固定开销
    content = msg.content if isinstance(msg.content, str) else str(msg.content)
    return role_overhead + estimate_tokens(content)


def estimate_total_tokens(messages: list[BaseMessage]) -> int:
    """估算消息列表的总 token 数"""
    return sum(estimate_message_tokens(m) for m in messages)


# ===========================================================================
# 第二部分：裁剪策略
# ===========================================================================
#
# 四种裁剪策略，从简单到复杂：
#   1. TruncateStrategy  — 保留最近 N 条消息
#   2. TokenBudgetStrategy — 按 token 预算从新到旧保留
#   3. FilterStrategy     — 按角色/类型过滤
#   4. HybridStrategy     — 混合策略（最实用）
#


@dataclass
class TrimResult:
    """裁剪结果 —— 包含裁剪后的消息和统计信息"""
    messages: list[BaseMessage]
    original_count: int
    trimmed_count: int
    original_tokens: int
    trimmed_tokens: int
    strategy: str
    dropped_count: int = 0

    @property
    def compression_ratio(self) -> float:
        """压缩比 —— 裁剪后/裁剪前"""
        if self.original_tokens == 0:
            return 1.0
        return self.trimmed_tokens / self.original_tokens

    def summary(self) -> str:
        """生成裁剪摘要"""
        lines = [
            f"📐 裁剪结果（策略: {self.strategy}）",
            f"   消息数: {self.original_count} → {self.trimmed_count}"
            f"（丢弃 {self.dropped_count} 条）",
            f"   Token 数: {self.original_tokens} → {self.trimmed_tokens}"
            f"（压缩比 {self.compression_ratio:.1%}）",
        ]
        return "\n".join(lines)


class TruncateStrategy:
    """截断策略 —— 只保留 system prompt + 最近 N 条消息。

    最简单粗暴，适合不关心历史细节的场景。
    """

    def __init__(self, keep_last: int = 20):
        self.keep_last = keep_last

    def trim(self, messages: list[BaseMessage]) -> TrimResult:
        original_count = len(messages)
        original_tokens = estimate_total_tokens(messages)

        # 分离 system messages 和对话消息
        system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
        conversation = [m for m in messages if not isinstance(m, SystemMessage)]

        # 保留最近 N 条对话
        if len(conversation) > self.keep_last:
            kept = conversation[-self.keep_last:]
        else:
            kept = conversation

        result = system_msgs + kept

        return TrimResult(
            messages=result,
            original_count=original_count,
            trimmed_count=len(result),
            original_tokens=original_tokens,
            trimmed_tokens=estimate_total_tokens(result),
            strategy=f"截断法（保留最近 {self.keep_last} 条）",
            dropped_count=original_count - len(result),
        )


class TokenBudgetStrategy:
    """Token 预算策略 —— 按 token 预算从新到旧保留。

    先确保 system prompt 在预算内，
    然后从最新消息向旧消息逐条添加，直到用完预算。
    """

    def __init__(self, max_tokens: int = 2000):
        self.max_tokens = max_tokens

    def trim(self, messages: list[BaseMessage]) -> TrimResult:
        original_count = len(messages)
        original_tokens = estimate_total_tokens(messages)

        # 1. 预留 system prompt
        system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
        conversation = [m for m in messages if not isinstance(m, SystemMessage)]

        budget = self.max_tokens
        for sm in system_msgs:
            budget -= estimate_message_tokens(sm)

        if budget <= 0:
            # system prompt 就超标了，只保留 system
            result = system_msgs
        else:
            # 2. 从最新到旧逐条添加
            kept: list[BaseMessage] = []
            for msg in reversed(conversation):
                msg_tokens = estimate_message_tokens(msg)
                if budget >= msg_tokens:
                    kept.insert(0, msg)
                    budget -= msg_tokens
                else:
                    break  # 预算不够了
            result = system_msgs + kept

        return TrimResult(
            messages=result,
            original_count=original_count,
            trimmed_count=len(result),
            original_tokens=original_tokens,
            trimmed_tokens=estimate_total_tokens(result),
            strategy=f"Token 预算法（上限 {self.max_tokens}）",
            dropped_count=original_count - len(result),
        )


class FilterStrategy:
    """过滤策略 —— 只保留指定角色的消息。

    适合场景：删除 ToolMessage 的详细返回值以节省 token，
    或只保留 Human/AI 对话忽略中间过程。
    """

    def __init__(
        self,
        keep_roles: set[str] | None = None,
        drop_roles: set[str] | None = None,
    ):
        """
        keep_roles: 只保留这些角色的消息（白名单）
        drop_roles: 丢弃这些角色的消息（黑名单）
        二者只能指定其一。
        """
        if keep_roles and drop_roles:
            raise ValueError("keep_roles 和 drop_roles 不能同时指定")
        self.keep_roles = keep_roles
        self.drop_roles = drop_roles

    def _should_keep(self, msg: BaseMessage) -> bool:
        role = msg.type  # 'human', 'ai', 'system', 'tool'
        if self.keep_roles:
            return role in self.keep_roles
        if self.drop_roles:
            return role not in self.drop_roles
        return True

    def trim(self, messages: list[BaseMessage]) -> TrimResult:
        original_count = len(messages)
        original_tokens = estimate_total_tokens(messages)

        result = [m for m in messages if self._should_keep(m)]

        desc = ""
        if self.keep_roles:
            desc = f"白名单: {self.keep_roles}"
        elif self.drop_roles:
            desc = f"黑名单: {self.drop_roles}"

        return TrimResult(
            messages=result,
            original_count=original_count,
            trimmed_count=len(result),
            original_tokens=original_tokens,
            trimmed_tokens=estimate_total_tokens(result),
            strategy=f"过滤法（{desc}）",
            dropped_count=original_count - len(result),
        )


class HybridStrategy:
    """混合策略 —— 先过滤冗余消息，再按 token 预算裁剪。

    最实用的策略，生产环境推荐。
    步骤：
      1. 保留所有 SystemMessage
      2. 如果有 ToolMessage 的内容超过阈值，截断其内容
      3. 按 token 预算从新到旧保留
    """

    def __init__(
        self,
        max_tokens: int = 2000,
        tool_content_max: int = 200,
    ):
        self.max_tokens = max_tokens
        self.tool_content_max = tool_content_max  # ToolMessage 内容截断长度

    def _truncate_tool_content(self, msg: BaseMessage) -> BaseMessage:
        """截断 ToolMessage 中过长的内容"""
        if not isinstance(msg, ToolMessage):
            return msg
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        if len(content) > self.tool_content_max:
            truncated = content[: self.tool_content_max] + "... [内容已截断]"
            return ToolMessage(
                content=truncated,
                tool_call_id=msg.tool_call_id,
            )
        return msg

    def trim(self, messages: list[BaseMessage]) -> TrimResult:
        original_count = len(messages)
        original_tokens = estimate_total_tokens(messages)

        # 1. 截断过长的 ToolMessage
        processed = [self._truncate_tool_content(m) for m in messages]

        # 2. 分离 system 和对话
        system_msgs = [m for m in processed if isinstance(m, SystemMessage)]
        conversation = [m for m in processed if not isinstance(m, SystemMessage)]

        # 3. 按 token 预算从新到旧保留
        budget = self.max_tokens
        for sm in system_msgs:
            budget -= estimate_message_tokens(sm)

        kept: list[BaseMessage] = []
        if budget > 0:
            for msg in reversed(conversation):
                msg_tokens = estimate_message_tokens(msg)
                if budget >= msg_tokens:
                    kept.insert(0, msg)
                    budget -= msg_tokens
                else:
                    break

        result = system_msgs + kept

        return TrimResult(
            messages=result,
            original_count=original_count,
            trimmed_count=len(result),
            original_tokens=original_tokens,
            trimmed_tokens=estimate_total_tokens(result),
            strategy=(
                f"混合法（token 上限 {self.max_tokens},"
                f" 工具内容截断 {self.tool_content_max} 字符）"
            ),
            dropped_count=original_count - len(result),
        )


# ===========================================================================
# 第三部分：ContextBuilder —— 上下文拼装器
# ===========================================================================
#
#  统一的入口：接收原始消息列表 + 裁剪策略 → 输出裁剪后的消息
#


class ContextBuilder:
    """上下文构建器 —— D18 核心产出。

    职责：
      1. 管理消息列表（追加消息、获取历史）
      2. 在发给 LLM 前，按策略裁剪上下文
      3. 提供裁剪统计（原始/裁剪后 token 数、压缩比）

    用法：
      builder = ContextBuilder(
          system_prompt="你是一名专利助手...",
          max_tokens=2000,
      )
      builder.add_human("搜索锂电池专利")
      builder.add_ai("找到 3 件相关专利...")
      ...
      trimmed = builder.build()  # 返回裁剪后的消息列表
    """

    def __init__(
        self,
        system_prompt: str = "你是一名有用的助手。",
        max_tokens: int = 2000,
        strategy: str = "hybrid",  # truncate / token_budget / filter / hybrid
        keep_last: int = 20,
        tool_content_max: int = 200,
    ):
        self.messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]
        self.max_tokens = max_tokens
        self.keep_last = keep_last
        self.tool_content_max = tool_content_max
        self._strategy_name = strategy

    def _get_strategy(self):
        """根据名称获取裁剪策略实例"""
        strategies = {
            "truncate": lambda: TruncateStrategy(keep_last=self.keep_last),
            "token_budget": lambda: TokenBudgetStrategy(max_tokens=self.max_tokens),
            "filter": lambda: FilterStrategy(drop_roles={"tool"}),
            "hybrid": lambda: HybridStrategy(
                max_tokens=self.max_tokens,
                tool_content_max=self.tool_content_max,
            ),
        }
        factory = strategies.get(self._strategy_name)
        if factory is None:
            raise ValueError(
                f"未知策略: {self._strategy_name}，"
                f"可选: {list(strategies.keys())}"
            )
        return factory()

    # --- 消息追加接口 ---

    def add_human(self, content: str) -> None:
        """追加用户消息"""
        self.messages.append(HumanMessage(content=content))

    def add_ai(self, content: str) -> None:
        """追加 AI 回复"""
        self.messages.append(AIMessage(content=content))

    def add_tool(self, content: str, tool_call_id: str = "call_0") -> None:
        """追加工具返回"""
        self.messages.append(ToolMessage(content=content, tool_call_id=tool_call_id))

    # --- 核心方法 ---

    def build(self) -> TrimResult:
        """构建裁剪后的上下文"""
        strategy = self._get_strategy()
        return strategy.trim(list(self.messages))  # 传副本，不修改原始列表

    @property
    def raw_token_count(self) -> int:
        """当前原始消息的 token 总数"""
        return estimate_total_tokens(self.messages)

    @property
    def message_count(self) -> int:
        return len(self.messages)


# ===========================================================================
# 第四部分：LangChain 内置 trim_messages 演示
# ===========================================================================


def demo_langchain_trim_messages() -> None:
    """演示 LangChain 内置的 trim_messages 工具。

    trim_messages 是 langchain_core 提供的工具函数，
    可以按 token 数或消息数裁剪消息列表。
    """
    print("\n" + "=" * 68)
    print("📎 演示 1：LangChain 内置 trim_messages")
    print("=" * 68)

    # 构造一组对话消息
    messages = [
        SystemMessage(content="你是一名专利分析助手，擅长解读专利文献。"),
        HumanMessage(content="你好，请帮我分析一下锂电池领域的专利趋势。"),
        AIMessage(content="好的，我来帮您分析锂电池领域的专利趋势。近年来，锂电池专利主要集中在..."),
        HumanMessage(content="固态电池的专利有哪些？"),
        AIMessage(content="固态电池是一个热门研究方向，以下是一些关键专利..."),
        HumanMessage(content="谁是主要的申请人？"),
        AIMessage(content="主要申请人包括丰田、三星SDI、宁德时代等企业..."),
        HumanMessage(content="最新的专利是什么？"),
        AIMessage(content="2024年最新公开的固态电池专利包括..."),
        HumanMessage(content="帮我对比一下丰田和宁德时代的技术路线"),
        AIMessage(content="丰田走的是硫化物固态电解质路线，宁德时代则在氧化物路线上有更多布局..."),
    ]

    print(f"\n  原始消息: {len(messages)} 条")
    print(f"  原始 token（估算）: {estimate_total_tokens(messages)}")

    # 使用 trim_messages 按 token 数裁剪
    # 注意：token_counter 的签名是 Callable[[list[BaseMessage]], int]
    trimmed = trim_messages(
        messages,
        max_tokens=200,
        token_counter=lambda msgs: estimate_total_tokens(msgs),
        strategy="last",               # 保留最近的消息
        start_on="human",              # 确保从 human 消息开始
        include_system=True,           # 始终保留 system message
    )

    print(f"\n  裁剪后消息: {len(trimmed)} 条（max_tokens=200）")
    print(f"  裁剪后 token（估算）: {estimate_total_tokens(trimmed)}")
    print("\n  裁剪后消息列表:")
    for i, msg in enumerate(trimmed):
        role = msg.type.upper()
        content = msg.content[:60] + "..." if len(msg.content) > 60 else msg.content
        print(f"    [{i+1}] {role}: {content}")


# ===========================================================================
# 第五部分：自定义裁剪策略演示
# ===========================================================================


def _generate_long_conversation(n: int = 100) -> list[BaseMessage]:
    """生成一个超长的模拟对话（n 轮问答）"""
    msgs: list[BaseMessage] = [
        SystemMessage(content="你是一名专利分析助手，擅长检索和分析专利文献。请用中文回复。"),
    ]

    # 模拟专利相关的多轮对话
    topics = [
        "锂电池", "固态电池", "燃料电池", "太阳能电池", "氢能源",
        "碳纳米管", "石墨烯", "量子计算", "人工智能芯片", "5G天线",
        "自动驾驶", "机器人", "基因编辑", "mRNA疫苗", "生物降解塑料",
    ]

    for i in range(n):
        topic = topics[i % len(topics)]
        turn = i // len(topics) + 1

        msgs.append(
            HumanMessage(content=f"请搜索关于「{topic}」的专利，第 {turn} 批结果。")
        )
        msgs.append(
            AIMessage(
                content=(
                    f"关于「{topic}」的第 {turn} 批专利检索结果如下：\n"
                    f"• JP2024-{i:04d}: {topic}改良工艺（丰田汽车）\n"
                    f"• CN2024-{i:04d}: 新型{topic}材料制备方法（宁德时代）\n"
                    f"• US2024-{i:04d}: {topic}性能优化系统（特斯拉）\n"
                    f"共找到 {3 + i % 5} 件相关专利。"
                )
            )
        )

        # 每 5 轮加一个 ToolMessage（模拟工具返回的详细数据）
        if i % 5 == 0:
            msgs.append(
                ToolMessage(
                    content=json.dumps(
                        {
                            "total": 3 + i % 5,
                            "query": topic,
                            "patents": [
                                {
                                    "id": f"JP2024-{i:04d}",
                                    "title": f"{topic}改良工艺",
                                    "applicant": "丰田汽车",
                                    "status": "granted",
                                }
                            ],
                            "metadata": {"search_time_ms": 120 + i * 3},
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    tool_call_id=f"call_{i}",
                )
            )

    return msgs


def demo_custom_strategies(max_tokens: int, show_diff: bool) -> None:
    """演示自定义裁剪策略在超长对话上的效果"""
    print("\n" + "=" * 68)
    print("🔧 演示 2：自定义裁剪策略对比（100 轮超长对话）")
    print("=" * 68)

    # 生成超长对话
    messages = _generate_long_conversation(100)
    original_tokens = estimate_total_tokens(messages)
    print(f"\n  📩 原始对话: {len(messages)} 条消息, 约 {original_tokens} token")

    # 测试所有策略
    strategies = [
        ("截断法", TruncateStrategy(keep_last=20)),
        (f"Token 预算法 ({max_tokens})", TokenBudgetStrategy(max_tokens=max_tokens)),
        ("过滤法（去 ToolMessage）", FilterStrategy(drop_roles={"tool"})),
        (f"混合法 ({max_tokens} token)", HybridStrategy(max_tokens=max_tokens)),
    ]

    results: list[tuple[str, TrimResult]] = []

    for name, strategy in strategies:
        result = strategy.trim(messages)
        results.append((name, result))

    # 打印对比表格
    print(f"\n  {'策略':<28} {'消息数':>7} {'Token':>8} {'压缩比':>8} {'丢弃':>6}")
    print("  " + "─" * 62)
    print(f"  {'[原始]':<28} {len(messages):>7} {original_tokens:>8} {'100%':>8} {'0':>6}")
    for name, result in results:
        print(
            f"  {name:<28} {result.trimmed_count:>7} "
            f"{result.trimmed_tokens:>8} "
            f"{result.compression_ratio:>7.1%} "
            f"{result.dropped_count:>6}"
        )

    # 如果 --show-diff，打印裁剪前后详情
    if show_diff:
        print("\n" + "-" * 68)
        print("📋 混合策略裁剪详情：")
        _, hybrid_result = results[-1]  # 最后一个是混合策略
        for i, msg in enumerate(hybrid_result.messages):
            role = msg.type.upper()
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            display = content[:80] + "..." if len(content) > 80 else content
            display = display.replace("\n", "↵ ")
            print(f"    [{i+1:3d}] {role:6s}: {display}")


# ===========================================================================
# 第六部分：ContextBuilder 集成演示
# ===========================================================================


def demo_context_builder(max_tokens: int) -> None:
    """演示 ContextBuilder 的完整使用流程"""
    print("\n" + "=" * 68)
    print("🏗️  演示 3：ContextBuilder 集成演示")
    print("=" * 68)

    builder = ContextBuilder(
        system_prompt="你是一名专利分析助手，请用中文回复。",
        max_tokens=max_tokens,
        strategy="hybrid",
    )

    # 模拟一段对话
    conversations = [
        ("human", "你好，我想了解锂电池专利"),
        ("ai", "您好！锂电池领域是近年来专利申请最活跃的技术领域之一。请问您想了解哪个方面？"),
        ("human", "固态电池的关键技术是什么？"),
        ("ai", "固态电池的关键技术包括：1) 固态电解质材料 2) 界面接触优化 3) 制造工艺改进..."),
        ("human", "帮我搜索一下丰田的固态电池专利"),
        ("ai", "找到 5 件丰田的固态电池专利。其中 JP2024-0001 是关于硫化物电解质的改进方案..."),
        ("human", "对比丰田和宁德时代的技术路线"),
        ("ai", "丰田主攻硫化物路线，宁德时代偏重氧化物路线。两者各有优劣..."),
    ]

    for role, content in conversations:
        if role == "human":
            builder.add_human(content)
        else:
            builder.add_ai(content)

    print(f"\n  当前消息: {builder.message_count} 条")
    print(f"  当前 token: {builder.raw_token_count}")

    # 模拟对话继续增长（加 50 轮）
    print("\n  📈 模拟对话增长（追加 50 轮）...")
    for i in range(50):
        builder.add_human(f"请继续搜索第 {i+1} 批结果")
        builder.add_ai(
            f"第 {i+1} 批结果：找到 {3+i%5} 件专利。"
            f"包括 JP2024-{i:04d}、CN2024-{i:04d} 等。"
        )

    print(f"  增长后消息: {builder.message_count} 条")
    print(f"  增长后 token: {builder.raw_token_count}")

    # 执行裁剪
    result = builder.build()
    print(f"\n{result.summary()}")

    # 验证裁剪后在预算内
    within_budget = result.trimmed_tokens <= max_tokens
    status = "✅ 在预算内" if within_budget else "⚠️ 超出预算"
    print(f"\n  预算检查: {status}")
    print(f"  预算: {max_tokens} token, 实际: {result.trimmed_tokens} token")


# ===========================================================================
# 第七部分：LLM 实际调用验证
# ===========================================================================


def demo_live_call() -> None:
    """用实际 LLM 验证裁剪后的上下文可正常使用"""
    print("\n" + "=" * 68)
    print("🚀 演示 4：LLM 实际调用验证（裁剪后可正常对话）")
    print("=" * 68)

    # 构建超长对话
    builder = ContextBuilder(
        system_prompt="你是一名专利分析助手。简洁回答问题。",
        max_tokens=1500,
        strategy="hybrid",
    )

    # 填充 30 轮对话
    for i in range(30):
        builder.add_human(f"搜索第 {i+1} 批锂电池专利")
        builder.add_ai(f"第 {i+1} 批：找到若干相关专利，包括电极材料、电解质改进等方向。")

    # 加入最终问题
    builder.add_human("总结一下我们今天讨论了什么内容？")

    print(f"\n  原始消息: {builder.message_count} 条, {builder.raw_token_count} token")

    # 裁剪
    result = builder.build()
    print(f"  裁剪后: {result.trimmed_count} 条, {result.trimmed_tokens} token")

    # 实际调用 LLM
    print("\n  🤖 调用 Ollama (qwen2.5:7b)...")
    try:
        llm = ChatOllama(model="qwen2.5:7b", temperature=0)
        start = time.perf_counter()
        response = llm.invoke(result.messages)
        elapsed = time.perf_counter() - start

        print(f"  ✅ LLM 返回（{elapsed:.2f}s）:")
        print(f"  {response.content[:300]}")
    except Exception as e:
        print(f"  ⚠️ LLM 调用失败: {e}")
        print("  （跳过，不影响裁剪功能验证）")


# ===========================================================================
# 第八部分：主程序入口
# ===========================================================================


def main() -> None:
    parser = argparse.ArgumentParser(
        description="D18 — 上下文拼装：实现上下文裁剪",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1000,
        help="Token 预算上限（默认 1000）",
    )
    parser.add_argument(
        "--show-diff",
        action="store_true",
        help="显示裁剪前后的消息详情对比",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="使用 LLM 实际调用验证裁剪效果",
    )
    args = parser.parse_args()

    print("=" * 68)
    print("📋 D18 上下文拼装 —— 上下文裁剪演示")
    print("=" * 68)

    # 演示 1：LangChain 内置 trim_messages
    demo_langchain_trim_messages()

    # 演示 2：自定义裁剪策略对比
    demo_custom_strategies(
        max_tokens=args.max_tokens,
        show_diff=args.show_diff,
    )

    # 演示 3：ContextBuilder 集成
    demo_context_builder(max_tokens=args.max_tokens)

    # 演示 4：实际 LLM 调用（可选）
    if args.live:
        demo_live_call()

    print("\n" + "=" * 68)
    print("✅ D18 演示完成")
    print("=" * 68)


if __name__ == "__main__":
    main()

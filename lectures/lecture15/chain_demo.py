"""
D15 — Runnable/Chain 基础：搭一条最小链，链路日志可读
====================================================

学习要点：
  1. LCEL（LangChain Expression Language）—— 用 `|` 管道操作符串联多个 Runnable
  2. ChatPromptTemplate → ChatOllama → StrOutputParser 三步链路
  3. 自定义 CallbackHandler 让每步的输入/输出/耗时在终端清晰可见
  4. RunnableLambda 包装自定义逻辑（如：问题预处理）
  5. RunnablePassthrough 透传数据

什么是"链路日志可读"？
  在 Agent/Chain 系统中，一个请求会经过多个步骤（Prompt 构建 → LLM 调用 → 输出解析等）。
  "链路日志可读"意味着：
    ① 每一步的名称、输入、输出都被记录下来
    ② 每步耗时清晰标注
    ③ 错误发生在哪一步一目了然
    ④ 日志格式统一、对齐，人眼可以快速扫描

  这是 Agent 工程化的基础——如果你无法看清链路执行过程，就无法调试、优化和定位问题。

运行方式：
  # 默认模式：交互式对话（需要 Ollama 运行 qwen2.5:7b）
  python lectures/lecture15/chain_demo.py

  # 指定问题
  python lectures/lecture15/chain_demo.py --query "什么是专利检索？"

  # 关闭链路日志（对比可读性差异）
  python lectures/lecture15/chain_demo.py --query "什么是专利检索？" --no-log

  # 使用 verbose 模式（更详细的日志）
  python lectures/lecture15/chain_demo.py --query "什么是专利检索？" --verbose

验收标准：链路日志可读 —— 终端输出能清楚看到每步名称、输入/输出摘要、耗时
"""

from __future__ import annotations

import argparse
import time
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langchain_ollama import ChatOllama

# ===========================================================================
# 第一部分：自定义链路日志回调（实现"链路日志可读"）
# ===========================================================================
# LangChain 的 Callback 机制允许我们在每个 Runnable 执行的关键节点
# （开始、结束、出错）插入自定义逻辑。
# 这里我们用它来打印结构化日志，让链路执行过程"透明可见"。


class ChainLogger(BaseCallbackHandler):
    """链路日志处理器 —— 让每一步的输入/输出/耗时在终端清晰可见。

    核心思路：
      - on_chain_start: 记录开始时间，打印步骤开始标记
      - on_chain_end:   计算耗时，打印输出摘要
      - on_chain_error: 打印错误信息和发生位置
      - on_llm_start:   记录 LLM 调用的 prompt
      - on_llm_end:     记录 LLM 返回的 token 数
    """

    def __init__(self, verbose: bool = False) -> None:
        super().__init__()
        self.verbose = verbose
        self._step_count = 0
        self._timers: dict[str, float] = {}
        # 缩进控制
        self._depth = 0

    # --- 辅助方法 ---

    def _indent(self) -> str:
        """根据嵌套深度生成缩进"""
        return "  " * self._depth

    @staticmethod
    def _truncate(text: str, max_len: int = 120) -> str:
        """截断过长文本，保持日志整洁"""
        text = text.replace("\n", "↵ ")  # 换行符替换为可见标记
        if len(text) > max_len:
            return text[:max_len] + "..."
        return text

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """格式化耗时显示"""
        if seconds < 0.001:
            return f"{seconds * 1_000_000:.0f}μs"
        if seconds < 1:
            return f"{seconds * 1000:.1f}ms"
        return f"{seconds:.2f}s"

    @staticmethod
    def _extract_name(serialized: dict[str, Any] | None) -> str:
        """从序列化信息中提取可读名称"""
        if not serialized:
            return "Unknown"
        # 优先使用 name 字段
        name = serialized.get("name", "")
        if name:
            return name
        # 其次使用 id 列表的最后一个元素
        id_list = serialized.get("id", [])
        if id_list:
            return id_list[-1]
        return "Unknown"

    def _summarize_input(self, inputs: Any) -> str:
        """将输入数据摘要为可读字符串"""
        if isinstance(inputs, str):
            return self._truncate(inputs)
        if isinstance(inputs, dict):
            # 只显示 key 和 value 的前几个字符
            parts = []
            for k, v in inputs.items():
                v_str = str(v)
                parts.append(f"{k}={self._truncate(v_str, 60)}")
            return "{" + ", ".join(parts) + "}"
        if isinstance(inputs, list):
            # 消息列表：只显示消息数和最后一条
            if inputs and isinstance(inputs[0], BaseMessage):
                return f"[{len(inputs)} messages, last={self._truncate(inputs[-1].content, 60)}]"
            return f"[{len(inputs)} items]"
        return self._truncate(str(inputs), 80)

    # --- Chain 回调 ---

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """链路步骤开始"""
        self._step_count += 1
        name = self._extract_name(serialized)
        run_id = str(kwargs.get("run_id", ""))[:8]
        self._timers[run_id] = time.perf_counter()

        indent = self._indent()
        print(f"{indent}┌─[步骤 {self._step_count}] {name}")
        if self.verbose:
            print(f"{indent}│  输入: {self._summarize_input(inputs)}")
        self._depth += 1

    def on_chain_end(
        self,
        outputs: dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """链路步骤结束"""
        self._depth = max(0, self._depth - 1)
        run_id = str(kwargs.get("run_id", ""))[:8]
        elapsed = time.perf_counter() - self._timers.pop(run_id, time.perf_counter())

        indent = self._indent()
        output_summary = self._summarize_input(outputs)
        print(f"{indent}└─ ✅ 完成 ({self._format_duration(elapsed)})")
        if self.verbose:
            print(f"{indent}   输出: {output_summary}")

    def on_chain_error(
        self,
        error: BaseException,
        **kwargs: Any,
    ) -> None:
        """链路步骤出错"""
        self._depth = max(0, self._depth - 1)
        run_id = str(kwargs.get("run_id", ""))[:8]
        elapsed = time.perf_counter() - self._timers.pop(run_id, time.perf_counter())

        indent = self._indent()
        print(f"{indent}└─ ❌ 错误 ({self._format_duration(elapsed)}): {error}")

    # --- LLM 回调 ---

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        **kwargs: Any,
    ) -> None:
        """LLM 调用开始"""
        run_id = str(kwargs.get("run_id", ""))[:8]
        self._timers[run_id] = time.perf_counter()
        indent = self._indent()
        model_name = self._extract_name(serialized)
        print(f"{indent}🤖 LLM 调用: {model_name}")
        if self.verbose and prompts:
            print(f"{indent}   Prompt: {self._truncate(prompts[0], 100)}")

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[BaseMessage]],
        **kwargs: Any,
    ) -> None:
        """ChatModel 调用开始（比 on_llm_start 更常用）"""
        run_id = str(kwargs.get("run_id", ""))[:8]
        self._timers[run_id] = time.perf_counter()
        indent = self._indent()
        model_name = self._extract_name(serialized)
        msg_count = sum(len(m) for m in messages)
        print(f"{indent}🤖 ChatModel 调用: {model_name} ({msg_count} 条消息)")
        if self.verbose and messages:
            for msg in messages[0]:
                role = msg.__class__.__name__.replace("Message", "")
                print(f"{indent}   [{role}] {self._truncate(msg.content, 80)}")

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """LLM 调用结束"""
        run_id = str(kwargs.get("run_id", ""))[:8]
        elapsed = time.perf_counter() - self._timers.pop(run_id, time.perf_counter())
        indent = self._indent()

        # 尝试提取 token 使用信息
        token_info = ""
        if hasattr(response, "llm_output") and response.llm_output:
            usage = response.llm_output.get("token_usage", {})
            if usage:
                token_info = (
                    f" | tokens: {usage.get('prompt_tokens', '?')}→"
                    f"{usage.get('completion_tokens', '?')}"
                )

        print(f"{indent}✅ LLM 返回 ({self._format_duration(elapsed)}{token_info})")
        if self.verbose and hasattr(response, "generations"):
            for gen_list in response.generations:
                for gen in gen_list:
                    print(f"{indent}   输出: {self._truncate(gen.text, 100)}")


# ===========================================================================
# 第二部分：构建最小链路（LCEL Pipeline）
# ===========================================================================
# LCEL 的核心思想：每个步骤都是一个 Runnable，用 `|` 串联。
#
#   chain = prompt | llm | parser
#
# 这条链路的数据流：
#   dict → ChatPromptTemplate → ChatMessages → ChatOllama → AIMessage → StrOutputParser → str


def preprocess_question(inputs: dict[str, Any]) -> dict[str, Any]:
    """问题预处理（用 RunnableLambda 包装的自定义逻辑）。

    演示如何在链路中插入自定义 Python 函数。
    在实际项目中，这里可以做：
      - 问题标准化（去除多余空格、标点统一）
      - 敏感词过滤
      - 上下文注入
    """
    question = inputs.get("question", "").strip()
    # 简单预处理：去除多余空格
    question = " ".join(question.split())
    return {**inputs, "question": question}


def build_chain(model_name: str = "qwen2.5:7b"):
    """构建最小链路。

    链路结构：
      问题预处理 → Prompt 模板 → LLM 调用 → 字符串解析

    关键概念：
      - RunnableLambda: 将普通 Python 函数包装为 Runnable
      - RunnablePassthrough: 透传输入（用于保留原始数据）
      - ChatPromptTemplate: 将变量填充到 Prompt 模板
      - ChatOllama: 调用本地 Ollama 模型
      - StrOutputParser: 将 AIMessage 解析为纯字符串
    """
    # 步骤 1: 问题预处理
    preprocessor = RunnableLambda(preprocess_question).with_config({"run_name": "问题预处理"})

    # 步骤 2: Prompt 模板
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你是一名专利分析助手。用简洁专业的中文回答问题。"),
            ("human", "{question}"),
        ]
    ).with_config({"run_name": "Prompt构建"})

    # 步骤 3: LLM 调用
    llm = ChatOllama(
        model=model_name,
        temperature=0,
    ).with_config({"run_name": "Ollama-LLM"})

    # 步骤 4: 输出解析
    parser = StrOutputParser().with_config({"run_name": "输出解析"})

    # 用 LCEL 管道操作符 `|` 串联
    chain = preprocessor | prompt | llm | parser

    return chain


# ===========================================================================
# 第三部分：演示链路（带日志 vs 不带日志的对比）
# ===========================================================================


def run_chain_with_logging(
    question: str,
    verbose: bool = False,
    enable_log: bool = True,
    model_name: str = "qwen2.5:7b",
) -> str:
    """执行链路并打印可读日志。

    参数：
      question:   用户问题
      verbose:    是否打印详细日志（含输入/输出内容）
      enable_log: 是否启用链路日志
      model_name: Ollama 模型名称
    """
    chain = build_chain(model_name=model_name)

    # 配置回调：这是实现"链路日志可读"的关键
    config: dict[str, Any] = {}
    if enable_log:
        logger = ChainLogger(verbose=verbose)
        config["callbacks"] = [logger]

    print("=" * 68)
    print("📋 D15 链路执行日志")
    print(f"   问题: {question}")
    print(f"   模型: {model_name}")
    print(f"   日志: {'详细' if verbose else '简要' if enable_log else '关闭'}")
    print("=" * 68)

    start_time = time.perf_counter()

    try:
        # invoke() 是同步执行，整条链路从头到尾跑一遍
        result = chain.invoke(
            {"question": question},
            config=RunnableConfig(**config),
        )
    except Exception as exc:
        elapsed = time.perf_counter() - start_time
        print(f"\n❌ 链路执行失败 ({elapsed:.2f}s): {exc}")
        raise

    elapsed = time.perf_counter() - start_time

    print("─" * 68)
    print(f"⏱️  总耗时: {elapsed:.2f}s")
    print("─" * 68)
    print("📝 最终输出:")
    print(result)
    print("=" * 68)

    return result


# ===========================================================================
# 第四部分：附加演示 —— Streaming 模式下的链路日志
# ===========================================================================


def run_chain_streaming(
    question: str,
    verbose: bool = False,
    model_name: str = "qwen2.5:7b",
) -> str:
    """Streaming 模式执行链路 —— 逐 token 输出 + 链路日志。

    与 invoke 的区别：
      - invoke: 等待整条链路执行完毕，一次性返回结果
      - stream:  逐步产出中间结果（对 LLM 来说就是逐 token 输出）
    """
    chain = build_chain(model_name=model_name)

    logger = ChainLogger(verbose=verbose)
    config = RunnableConfig(callbacks=[logger])

    print("=" * 68)
    print("📋 D15 链路执行日志（Streaming 模式）")
    print(f"   问题: {question}")
    print("=" * 68)

    start_time = time.perf_counter()
    chunks: list[str] = []

    print("📝 流式输出:")
    for chunk in chain.stream({"question": question}, config=config):
        print(chunk, end="", flush=True)
        chunks.append(chunk)
    print()  # 换行

    elapsed = time.perf_counter() - start_time
    print("─" * 68)
    print(f"⏱️  总耗时: {elapsed:.2f}s")
    print("=" * 68)

    return "".join(chunks)


# ===========================================================================
# 第五部分：附加演示 —— 链路结构可视化
# ===========================================================================


def print_chain_graph(model_name: str = "qwen2.5:7b") -> None:
    """打印链路的 ASCII 结构图 —— 可视化数据流向。

    这也是"链路可读"的一部分：不仅运行时日志可读，
    链路本身的结构也要能一目了然。
    """
    chain = build_chain(model_name=model_name)

    print("=" * 68)
    print("🔗 链路结构")
    print("=" * 68)

    # 获取链路图
    graph = chain.get_graph()

    # 尝试打印 ASCII 图（需要 grandalf 可选依赖）
    try:
        print(graph.draw_ascii())
    except ImportError:
        print("（ASCII 图需要 grandalf 依赖，跳过）")

    # 打印 Mermaid 图（可粘贴到 mermaid.live 查看）
    print("─" * 68)
    print("📊 Mermaid 图（可粘贴到 https://mermaid.live 查看）:")
    print("─" * 68)
    print(graph.draw_mermaid())
    print("=" * 68)


# ===========================================================================
# CLI 入口
# ===========================================================================


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="D15: Runnable/Chain 基础 — 最小链路 + 链路日志可读"
    )
    parser.add_argument("--query", "-q", help="要分析的问题")
    parser.add_argument(
        "--no-log",
        action="store_true",
        help="关闭链路日志（用于对比可读性差异）",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="详细日志（显示每步输入/输出内容）",
    )
    parser.add_argument(
        "--stream",
        "-s",
        action="store_true",
        help="使用 streaming 模式（逐 token 输出）",
    )
    parser.add_argument(
        "--graph",
        "-g",
        action="store_true",
        help="打印链路结构图",
    )
    parser.add_argument(
        "--model",
        default="qwen2.5:7b",
        help="Ollama 模型名称（默认 qwen2.5:7b）",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # 打印链路结构
    if args.graph:
        print_chain_graph(model_name=args.model)
        return 0

    # 交互式或命令行模式
    question = args.query
    if not question:
        print("=" * 60)
        print("D15 — 最小链路 + 链路日志可读")
        print("=" * 60)
        print()
        print("示例问题：")
        print("  · 什么是专利检索？")
        print("  · 解释一下 IPC 分类号的含义")
        print("  · 专利申请流程有哪些步骤？")
        print()
        question = input("请输入问题: ").strip()

    if not question:
        print("问题不能为空。")
        return 1

    if args.stream:
        run_chain_streaming(
            question=question,
            verbose=args.verbose,
            model_name=args.model,
        )
    else:
        run_chain_with_logging(
            question=question,
            verbose=args.verbose,
            enable_log=not args.no_log,
            model_name=args.model,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

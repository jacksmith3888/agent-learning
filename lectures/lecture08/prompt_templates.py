"""
Day 8 — Prompt 模板（问答 / 抽取 / 改写）
==========================================
目标：掌握 LangChain PromptTemplate 的变量定义与模板组装，
     为后续结构化输出和动态 Prompt 打基础。

三个模板：
  1. qa_prompt       — 问答模板：基于专利上下文回答用户问题
  2. extract_prompt  — 抽取模板：从非结构化文本中提取关键字段
  3. rewrite_prompt  — 改写模板：将用户口语化表述转为规范专利检索语句

变量定义说明：
  - 每个模板都使用 {variable_name} 占位符
  - 变量通过 input_variables 显式声明，避免运行时遗漏
  - 附带使用示例和单独运行验证
"""

from langchain_core.prompts import ChatPromptTemplate

# ===========================================================================
# 1. 问答模板 — 基于专利上下文回答问题
# ===========================================================================
# 变量：
#   context  — 检索到的专利摘要 / 文档片段
#   question — 用户提出的问题

qa_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "你是一位专业的化学专利分析师。\n"
                "请根据以下专利文档内容回答用户的问题。\n"
                "如果文档中没有足够信息，请明确说明「无法从所提供的文档中得出结论」，\n"
                "不要编造任何不在文档中的内容。\n\n"
                "回答要求：\n"
                "- 使用中文\n"
                "- 简洁准确，控制在 3-5 句话以内\n"
                "- 如有关键数据（如成分比例、温度、压力），需原文引用"
            ),
        ),
        ("human", ("【专利文档】\n{context}\n\n【问题】\n{question}")),
    ]
)

# 变量元信息（方便外部程序检索）
QA_VARIABLES = {
    "context": {
        "description": "检索到的专利文档片段（可以是多段拼接）",
        "type": "str",
        "required": True,
        "example": "本发明涉及一种生物降解塑料组合物，包含 PLA 60-80wt% 和 PBAT 20-40wt%...",
    },
    "question": {
        "description": "用户提出的自然语言问题",
        "type": "str",
        "required": True,
        "example": "这种塑料的 PLA 含量范围是多少？",
    },
}


# ===========================================================================
# 2. 抽取模板 — 从非结构化文本中提取关键字段
# ===========================================================================
# 变量：
#   text          — 待抽取的非结构化专利文本
#   target_fields — 需要提取的字段列表（如：申请人、申请日、IPC分类）

extract_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "你是一位专利信息抽取专家。\n"
                "请从用户提供的文本中精确提取指定字段的值。\n\n"
                "抽取规则：\n"
                "- 严格按照指定字段逐一输出\n"
                "- 每个字段单独一行，格式为「字段名: 值」\n"
                "- 如果文本中找不到某个字段，标注为「未提及」\n"
                "- 不要推测或编造信息，只提取文本中明确出现的内容\n"
                "- 日期统一转换为 YYYY-MM-DD 格式\n"
                "- 人名 / 公司名保持原文（不翻译）"
            ),
        ),
        ("human", ("【待抽取文本】\n{text}\n\n【需要提取的字段】\n{target_fields}")),
    ]
)

# 变量元信息
EXTRACT_VARIABLES = {
    "text": {
        "description": "待抽取的非结构化专利文本（摘要、权利要求书、说明书片段等）",
        "type": "str",
        "required": True,
        "example": (
            "特開2024-12345 由 Toyota Motor Corporation 于 2024年3月15日提出申请，"
            "涉及一种新型固态电池电解质材料，IPC分类号为 H01M 10/0562、H01M 10/052。"
            "该发明公开了一种硫化物系固态电解质..."
        ),
    },
    "target_fields": {
        "description": "需要提取的字段名称列表，用逗号或换行分隔",
        "type": "str",
        "required": True,
        "example": "专利号, 申请人, 申请日, IPC分类号, 技术领域",
    },
}


# ===========================================================================
# 3. 改写模板 — 将口语化表述转为规范专利检索语句
# ===========================================================================
# 变量：
#   user_query     — 用户的口语化原始问题
#   domain         — 技术领域提示（化学、机械、电子等），辅助改写方向

rewrite_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "你是一位专利检索策略专家。\n"
                "你的任务是将用户的口语化描述转换为适合专利数据库检索的规范查询语句。\n\n"
                "改写规则：\n"
                "- 提取核心技术概念，去除口语化修饰词\n"
                "- 补充同义词 / 上位概念 / 下位概念（用括号标注）\n"
                "- 如果涉及特定技术领域，补充该领域常用术语\n"
                "- 输出格式：\n"
                "  1. 规范检索语句（主查询）\n"
                "  2. 扩展关键词（3-5 个同义/相关术语）\n"
                "  3. 建议 IPC 分类号（如果能推断）"
            ),
        ),
        ("human", ("【用户原始描述】\n{user_query}\n\n【技术领域】\n{domain}")),
    ]
)

# 变量元信息
REWRITE_VARIABLES = {
    "user_query": {
        "description": "用户的口语化原始问题或技术描述",
        "type": "str",
        "required": True,
        "example": "有没有那种可以自己分解的塑料袋的专利？就是扔了之后不会污染环境的那种",
    },
    "domain": {
        "description": "技术领域提示，用于辅助改写方向",
        "type": "str",
        "required": True,
        "example": "高分子化学 / 环保材料",
    },
}


# ===========================================================================
# 模板注册表 — 方便统一管理和遍历
# ===========================================================================

TEMPLATE_REGISTRY = {
    "qa": {
        "prompt": qa_prompt,
        "variables": QA_VARIABLES,
        "description": "基于专利上下文的问答模板",
    },
    "extract": {
        "prompt": extract_prompt,
        "variables": EXTRACT_VARIABLES,
        "description": "从非结构化文本中提取关键字段",
    },
    "rewrite": {
        "prompt": rewrite_prompt,
        "variables": REWRITE_VARIABLES,
        "description": "将口语化表述转为规范专利检索语句",
    },
}


# ===========================================================================
# 验证 & 演示
# ===========================================================================


def demo_format_all():
    """演示：用示例数据填充每个模板，并调用 Ollama 模型获取真实输出"""
    from langchain_ollama import ChatOllama

    print("=" * 60)
    print("  Prompt 模板演示（填充变量 + 调用 LLM）")
    print("=" * 60)

    llm = ChatOllama(model="qwen2.5:7b", temperature=0)

    # --- 1. 问答模板 ---
    print("\n📝 [1] 问答模板 (qa_prompt)")
    print("-" * 40)
    qa_messages = qa_prompt.format_messages(
        context=QA_VARIABLES["context"]["example"],
        question=QA_VARIABLES["question"]["example"],
    )
    print("  📤 渲染后的 human 消息:")
    print(f"    {qa_messages[-1].content}\n")
    print("  🤖 LLM 回答:")
    response = llm.invoke(qa_messages)
    print(f"    {response.content}\n")

    # --- 2. 抽取模板 ---
    print("\n📝 [2] 抽取模板 (extract_prompt)")
    print("-" * 40)
    extract_messages = extract_prompt.format_messages(
        text=EXTRACT_VARIABLES["text"]["example"],
        target_fields=EXTRACT_VARIABLES["target_fields"]["example"],
    )
    print("  📤 渲染后的 human 消息:")
    print(f"    {extract_messages[-1].content}\n")
    print("  🤖 LLM 回答:")
    response = llm.invoke(extract_messages)
    print(f"    {response.content}\n")

    # --- 3. 改写模板 ---
    print("\n📝 [3] 改写模板 (rewrite_prompt)")
    print("-" * 40)
    rewrite_messages = rewrite_prompt.format_messages(
        user_query=REWRITE_VARIABLES["user_query"]["example"],
        domain=REWRITE_VARIABLES["domain"]["example"],
    )
    print("  📤 渲染后的 human 消息:")
    print(f"    {rewrite_messages[-1].content}\n")
    print("  🤖 LLM 回答:")
    response = llm.invoke(rewrite_messages)
    print(f"    {response.content}\n")

    # --- 变量汇总 ---
    print("=" * 60)
    print("  变量汇总")
    print("=" * 60)
    for name, info in TEMPLATE_REGISTRY.items():
        print(f"\n  📋 {name}: {info['description']}")
        for var_name, var_meta in info["variables"].items():
            req = "必填" if var_meta["required"] else "可选"
            print(f"     • {var_name} ({var_meta['type']}, {req}) — {var_meta['description']}")


if __name__ == "__main__":
    demo_format_all()

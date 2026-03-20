"""
Day 9 — 结构化输出模型（Schema 定义 + 自动验证）
=================================================
目标：用 Pydantic BaseModel 定义输出 Schema，
     通过 create_agent + response_format 让 LLM 返回可编程操作的结构化对象。

对比 D8：
  D8 — ChatPromptTemplate 控制"怎么问"（输入侧）
  D9 — BaseModel + response_format 控制"怎么答"（输出侧）

三个 Schema：
  1. PatentInfo       — 从文本中抽取专利基本信息
  2. PatentComparison — 对比两件专利的结构化结论
  3. QueryRewrite     — 口语化查询改写为规范检索语句

验收：每个 Schema 都能自动验证 LLM 输出，字段类型/必填项自动校验通过。
"""

from enum import Enum

from pydantic import BaseModel, Field

# ===========================================================================
# 1. PatentInfo — 专利基本信息抽取
# ===========================================================================


class PatentInfo(BaseModel):
    """从非结构化文本中抽取的专利基本信息"""

    # 专利编号，如 特開2024-12345、JP2024-001
    patent_id: str = Field(description="专利编号")
    # 申请人 / 发明人
    applicant: str = Field(description="申请人或发明人名称，保持原文不翻译")
    # 申请日期，格式 YYYY-MM-DD
    filing_date: str = Field(description="申请日期，格式为 YYYY-MM-DD")
    # IPC 分类号列表
    ipc_codes: list[str] = Field(description="IPC 国际专利分类号列表")
    # 技术领域简述
    tech_domain: str = Field(description="技术领域的简短描述")
    # 核心发明点（一句话）
    core_invention: str = Field(description="核心发明内容的一句话概括")


# ===========================================================================
# 2. PatentComparison — 专利对比结论
# ===========================================================================


class SimilarityLevel(str, Enum):
    """相似度等级"""

    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"


class PatentComparison(BaseModel):
    """对比两件专利后的结构化结论"""

    # 专利 A 的编号
    patent_a_id: str = Field(description="专利 A 的编号")
    # 专利 B 的编号
    patent_b_id: str = Field(description="专利 B 的编号")
    # 共同技术领域
    common_domain: str = Field(description="两件专利的共同技术领域")
    # 关键差异点（列表）
    key_differences: list[str] = Field(description="两件专利之间的关键差异点")
    # 技术相似度
    similarity: SimilarityLevel = Field(description="技术方案的相似度等级：高/中/低")
    # 综合结论
    conclusion: str = Field(description="对比结论（2-3句话）")


# ===========================================================================
# 3. QueryRewrite — 查询改写结果
# ===========================================================================


class QueryRewrite(BaseModel):
    """将口语化查询改写为规范专利检索语句"""

    # 原始查询
    original_query: str = Field(description="用户的原始口语化查询")
    # 规范化主查询
    formal_query: str = Field(description="改写后的规范检索语句")
    # 扩展关键词
    expanded_keywords: list[str] = Field(description="3-5 个同义或相关扩展关键词")
    # 建议 IPC 分类号
    suggested_ipc: list[str] = Field(
        default_factory=list,
        description="建议的 IPC 分类号（如果能推断）",
    )


# ===========================================================================
# Schema 注册表
# ===========================================================================

SCHEMA_REGISTRY = {
    "patent_info": {
        "model": PatentInfo,
        "description": "从非结构化文本中抽取专利基本信息",
        "test_input": (
            "特開2024-12345 由 Toyota Motor Corporation 于 2024年3月15日提出申请，"
            "涉及一种新型固态电池电解质材料，IPC分类号为 H01M 10/0562、H01M 10/052。"
            "该发明公开了一种硫化物系固态电解质，通过掺杂锂盐实现高离子导电性。"
        ),
    },
    "patent_comparison": {
        "model": PatentComparison,
        "description": "对比两件专利的结构化结论",
        "test_input": (
            "请对比以下两件专利：\n"
            "专利A (JP2024-001): 生物降解塑料组合物，申请人 Mitsubishi Chemical，"
            "PLA+PBAT 复合材料，用于包装领域。\n"
            "专利B (JP2024-002): 可堆肥塑料薄膜，申请人 Toray Industries，"
            "PLA+PBS 复合材料，用于农业地膜。"
        ),
    },
    "query_rewrite": {
        "model": QueryRewrite,
        "description": "将口语化查询改写为规范专利检索语句",
        "test_input": "有没有那种可以自己分解的塑料袋的专利？就是扔了之后不会污染环境的那种",
    },
}


# ===========================================================================
# 验证 & 演示
# ===========================================================================


def demo_structured_output():
    """演示：用 create_agent + response_format 获取结构化输出，并自动验证"""
    from langchain.agents import create_agent
    from langchain_ollama import ChatOllama

    print("=" * 60)
    print("  结构化输出演示（BaseModel + response_format）")
    print("=" * 60)

    for name, info in SCHEMA_REGISTRY.items():
        schema_cls = info["model"]
        test_input = info["test_input"]

        print(f"\n📋 [{name}] {info['description']}")
        print("-" * 50)

        # 用 create_agent + response_format 构建 Agent
        agent = create_agent(
            model=ChatOllama(model="qwen2.5:7b", temperature=0),
            response_format=schema_cls,
        )

        # 调用 Agent
        print(f"  📤 输入: {test_input[:80]}...")
        result = agent.invoke({"messages": [{"role": "user", "content": test_input}]})

        # 获取结构化响应
        structured = result["structured_response"]
        print(f"  📦 返回类型: {type(structured).__name__}")

        # 打印各字段值
        if isinstance(structured, BaseModel):
            for field_name, value in structured.model_dump().items():
                print(f"     • {field_name}: {value}")
        else:
            # TypedDict 等情况
            for key, value in structured.items():
                print(f"     • {key}: {value}")

        # 自动验证：用 Pydantic model_validate 重新校验
        print("\n  ✅ Pydantic 自动验证:")
        try:
            if isinstance(structured, BaseModel):
                validated = schema_cls.model_validate(structured.model_dump())
            else:
                validated = schema_cls.model_validate(structured)
            print(f"     验证通过！对象类型: {type(validated).__name__}")
            # 检查必填字段是否都有值
            for field_name, field_info in schema_cls.model_fields.items():
                value = getattr(validated, field_name)
                is_filled = bool(value) if value is not None else False
                status = "✅" if is_filled else "⚠️ 空值"
                print(f"     {status} {field_name} = {value}")
        except Exception as e:
            print(f"     ❌ 验证失败: {e}")

        print()

    print("=" * 60)
    print("  所有 Schema 验证完成")
    print("=" * 60)


if __name__ == "__main__":
    demo_structured_output()

"""
Day 10 — 失败样本验证脚本
========================
目标：加载 failure_samples.json 中的 5 条失败样本，
     逐一用 D9 定义的 Schema 进行 Pydantic 验证，
     展示每种失败模式的具体报错信息，并演示修复策略。

对比 D9：
  D9 — 定义 Schema 并验证 LLM 的"正确"输出
  D10 — 主动构造"错误"输出，理解 Schema 验证的边界与盲区

验收标准：
  - 覆盖缺字段 / 类型错 / 多余字段 / 空值 / 格式不符 5 种失败模式
  - 每个样本都能显示具体的验证错误信息
  - 演示 extra='forbid' 配置的效果
"""

import json
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

# 将 lecture09 加入路径，以便导入 Schema
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lecture09"))
from schema_v1 import (
    PatentComparison,
    PatentInfo,
    QueryRewrite,
)

# ===========================================================================
# Schema 名称 → Pydantic 类的映射
# ===========================================================================
SCHEMA_MAP: dict[str, type[BaseModel]] = {
    "PatentInfo": PatentInfo,
    "PatentComparison": PatentComparison,
    "QueryRewrite": QueryRewrite,
}


# ===========================================================================
# 增强版 Schema — 演示如何通过配置/验证器堵住 D9 原始 Schema 的盲区
# ===========================================================================


class StrictPatentInfo(PatentInfo):
    """增强版 PatentInfo：添加字段验证器阻止空值和格式错误"""

    model_config = ConfigDict(extra="forbid")  # 禁止多余字段

    @field_validator("filing_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """校验日期格式必须为 YYYY-MM-DD"""
        import re

        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError(f"日期格式必须为 YYYY-MM-DD，收到: '{v}'")
        return v

    @field_validator("patent_id", "applicant", "tech_domain", "core_invention")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """校验字符串字段不能为空"""
        if not v or not v.strip():
            raise ValueError("字段不能为空字符串")
        return v

    @field_validator("ipc_codes")
    @classmethod
    def validate_ipc_not_empty(cls, v: list[str]) -> list[str]:
        """校验 IPC 分类号列表不能为空"""
        if not v:
            raise ValueError("IPC 分类号列表不能为空")
        return v


class StrictPatentComparison(PatentComparison):
    """增强版 PatentComparison：禁止多余字段 + 枚举兼容映射"""

    model_config = ConfigDict(extra="forbid")

    @field_validator("similarity", mode="before")
    @classmethod
    def map_english_to_chinese(cls, v: Any) -> Any:
        """将英文枚举值映射为中文，提高兼容性"""
        mapping = {"high": "高", "medium": "中", "low": "低"}
        if isinstance(v, str):
            return mapping.get(v.lower(), v)
        return v


class StrictQueryRewrite(QueryRewrite):
    """增强版 QueryRewrite：阻止空值"""

    model_config = ConfigDict(extra="forbid")

    @field_validator("formal_query")
    @classmethod
    def validate_formal_query_not_empty(cls, v: str) -> str:
        """校验改写后的查询不能为空"""
        if not v or not v.strip():
            raise ValueError("formal_query 不能为空，如果无法改写请保持原始查询")
        return v

    @field_validator("expanded_keywords")
    @classmethod
    def validate_keywords_not_empty(cls, v: list[str]) -> list[str]:
        """校验扩展关键词列表至少包含 1 个元素"""
        if not v:
            raise ValueError("expanded_keywords 至少需要 1 个关键词")
        return v


# 增强版 Schema 映射
STRICT_SCHEMA_MAP: dict[str, type[BaseModel]] = {
    "PatentInfo": StrictPatentInfo,
    "PatentComparison": StrictPatentComparison,
    "QueryRewrite": StrictQueryRewrite,
}


# ===========================================================================
# 核心验证逻辑
# ===========================================================================


def load_samples() -> list[dict]:
    """加载失败样本"""
    samples_path = Path(__file__).parent / "failure_samples.json"
    with open(samples_path, encoding="utf-8") as f:
        data = json.load(f)
    return data["samples"]


def validate_sample(
    sample: dict,
    schema_map: dict[str, type[BaseModel]],
    label: str = "原始 Schema",
) -> bool:
    """
    用指定 Schema 验证单个样本。

    返回值:
        True — 验证通过（对于失败样本意味着 Schema 存在盲区）
        False — 验证失败（符合预期）
    """
    schema_name = sample["schema"]
    schema_cls = schema_map.get(schema_name)
    if not schema_cls:
        print(f"  ⚠️  未找到 Schema: {schema_name}")
        return False

    llm_output = sample["llm_output"]

    try:
        validated = schema_cls.model_validate(llm_output)
        print(f"  ✅ [{label}] 验证通过 — 类型: {type(validated).__name__}")
        # 如果是失败样本却通过验证，说明 Schema 有盲区
        if sample["category"] in ("empty_value", "extra_field"):
            print(
                f"  💡 注意: 这是 '{sample['category']}' 类型的样本，通过验证说明原始 Schema 未覆盖此场景"
            )
        return True
    except ValidationError as e:
        error_count = e.error_count()
        print(f"  ❌ [{label}] 验证失败 — 共 {error_count} 个错误:")
        for err in e.errors():
            field = " → ".join(str(loc) for loc in err["loc"])
            print(f"     • {field}: {err['msg']} (type={err['type']})")
        return False


def run_validation():
    """运行完整验证流程"""
    samples = load_samples()

    print("=" * 70)
    print("  D10 — 失败样本验证报告")
    print("  基于 D9 Schema: PatentInfo / PatentComparison / QueryRewrite")
    print("=" * 70)

    # 统计
    original_pass = 0
    original_fail = 0
    strict_pass = 0
    strict_fail = 0

    for sample in samples:
        print(f"\n{'─' * 70}")
        print(f"📋 [{sample['id']}] {sample['description']}")
        print(f"   分类: {sample['category']} | Schema: {sample['schema']}")
        print(f"   预期错误: {sample['expected_error'][:80]}...")
        print()

        # 第一轮：用原始 D9 Schema 验证
        if validate_sample(sample, SCHEMA_MAP, "原始 Schema"):
            original_pass += 1
        else:
            original_fail += 1

        print()

        # 第二轮：用增强版 Schema 验证
        if validate_sample(sample, STRICT_SCHEMA_MAP, "增强 Schema"):
            strict_pass += 1
        else:
            strict_fail += 1

        # 显示修复策略
        print(f"\n  🔧 修复策略: {sample['fix_strategy'][:100]}...")

    # 汇总报告
    print(f"\n{'=' * 70}")
    print("  📊 验证汇总")
    print(f"{'=' * 70}")
    print("\n  原始 Schema (D9):")
    print(f"    ✅ 通过: {original_pass} / {len(samples)}")
    print(f"    ❌ 失败: {original_fail} / {len(samples)}")
    print("\n  增强 Schema (D10):")
    print(f"    ✅ 通过: {strict_pass} / {len(samples)}")
    print(f"    ❌ 失败: {strict_fail} / {len(samples)}")
    print("\n  💡 关键发现:")
    print(f"    - 原始 Schema 可以捕获 {original_fail} 种失败模式")
    print(f"    - 增强 Schema 可以捕获 {strict_fail} 种失败模式")
    if strict_fail > original_fail:
        print(f"    - 增强后额外捕获了 {strict_fail - original_fail} 种盲区")
    print("\n  🎯 D10 核心收获:")
    print("    1. Pydantic 默认只校验类型和必填，不校验业务语义（空值、枚举范围）")
    print("    2. extra='forbid' 可以阻止 LLM 返回多余字段")
    print("    3. @field_validator 是堵住业务盲区的关键工具")
    print("    4. 失败样本是 Schema 设计的最佳测试用例")
    print()


if __name__ == "__main__":
    run_validation()

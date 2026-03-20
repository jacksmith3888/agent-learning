from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
LECTURE10_DIR = ROOT_DIR / "lectures" / "lecture10"
LECTURE11_DIR = ROOT_DIR / "lectures" / "lecture11"

sys.path.insert(0, str(LECTURE10_DIR))
sys.path.insert(0, str(LECTURE11_DIR))

from retry_parser import repair_output
from validate_failures import STRICT_SCHEMA_MAP

SHORT_PROMPT = """
你是专利分析助手。
请根据输入内容输出对应 Schema 的 JSON。
""".strip()

STRONG_PROMPT = """
你是专利分析助手。
任务：根据输入内容输出对应 Schema 的 JSON。

强约束：
1. 只能输出 JSON，不要输出解释。
2. 所有必填字段必须完整返回。
3. 不允许出现 Schema 之外的字段。
4. 日期统一使用 YYYY-MM-DD。
5. similarity 只能填写 高 / 中 / 低。
6. key_differences 必须是字符串数组。
7. formal_query 不能为空；expanded_keywords 至少包含 1 个元素。
8. 输出前先自检字段完整性与类型，但不要展示推理过程。
""".strip()


def load_samples() -> list[dict[str, Any]]:
    """读取 D10 的失败样本。"""
    samples_path = LECTURE10_DIR / "failure_samples.json"
    with open(samples_path, encoding="utf-8") as file:
        return json.load(file)["samples"]


def validate_payload(
    schema_name: str, payload: dict[str, Any]
) -> tuple[bool, list[dict[str, Any]]]:
    """用严格 Schema 校验输出。"""
    schema_cls = STRICT_SCHEMA_MAP[schema_name]
    try:
        schema_cls.model_validate(payload)
        return True, []
    except Exception as exc:  # 避免额外引入 ValidationError 依赖
        if hasattr(exc, "errors"):
            return False, exc.errors()
        raise


def build_user_input(sample: dict[str, Any]) -> str:
    """为每个样本生成简化输入。"""
    return (
        f"Schema: {sample['schema']}\n"
        f"场景: {sample['description']}\n"
        "请输出可直接被程序消费的结构化结果。"
    )


def simulate_model_output(sample: dict[str, Any], prompt_variant: str) -> dict[str, Any]:
    """根据提示强度返回确定性输出。"""
    output = deepcopy(sample["llm_output"])
    if prompt_variant == "strong":
        return repair_output(sample, output)
    return output


def format_error_labels(errors: list[dict[str, Any]]) -> str:
    """简要整理主要报错字段。"""
    labels = []
    for error in errors:
        location = ".".join(str(part) for part in error["loc"])
        labels.append(location)
    return "、".join(labels) if labels else "无"


def summarize_applicability(short_passes: int, strong_passes: int, total: int) -> list[str]:
    """生成 A/B 对比结论。"""
    summary = [
        f"短提示通过率：{short_passes}/{total}",
        f"强约束提示通过率：{strong_passes}/{total}",
    ]

    if strong_passes > short_passes:
        summary.append("结论：结构化输出、自动校验、下游要消费 JSON 的场景，优先用强约束提示。")
    else:
        summary.append("结论：当前样本下两者差异不明显，可优先保留更短提示。")

    summary.append("适用场景A：短提示适合低风险问答、头脑风暴、先求快再人工复核。")
    summary.append("适用场景B：强约束提示适合信息抽取、工具调用前置解析、需要稳定字段的流程。")
    return summary


def run_ab_compare() -> None:
    """输出 D12 的对比报告。"""
    samples = load_samples()
    short_passes = 0
    strong_passes = 0

    print("=" * 72)
    print("D12 Prompt A/B 对比")
    print("=" * 72)
    print("Prompt A（短提示）:")
    print(SHORT_PROMPT)
    print("\nPrompt B（强约束提示）:")
    print(STRONG_PROMPT)

    for sample in samples:
        user_input = build_user_input(sample)
        short_output = simulate_model_output(sample, "short")
        strong_output = simulate_model_output(sample, "strong")

        short_ok, short_errors = validate_payload(sample["schema"], short_output)
        strong_ok, strong_errors = validate_payload(sample["schema"], strong_output)

        short_passes += int(short_ok)
        strong_passes += int(strong_ok)

        print(f"\n[{sample['id']}] {sample['category']} / {sample['schema']}")
        print(f"输入摘要: {user_input.splitlines()[1]}")
        print(
            "  A-短提示: "
            f"{'通过' if short_ok else '失败'}"
            f" | 问题字段: {format_error_labels(short_errors)}"
        )
        print(
            "  B-强约束: "
            f"{'通过' if strong_ok else '失败'}"
            f" | 问题字段: {format_error_labels(strong_errors)}"
        )

    print(f"\n{'=' * 72}")
    print("结论与适用场景")
    print(f"{'=' * 72}")
    for line in summarize_applicability(short_passes, strong_passes, len(samples)):
        print(f"- {line}")


if __name__ == "__main__":
    run_ab_compare()

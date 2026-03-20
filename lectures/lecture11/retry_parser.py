from __future__ import annotations

import json
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

ROOT_DIR = Path(__file__).resolve().parents[2]
LECTURE10_DIR = ROOT_DIR / "lectures" / "lecture10"

sys.path.insert(0, str(LECTURE10_DIR))
from validate_failures import STRICT_SCHEMA_MAP


def load_samples() -> list[dict[str, Any]]:
    samples_path = LECTURE10_DIR / "failure_samples.json"
    with open(samples_path, encoding="utf-8") as file:
        return json.load(file)["samples"]


def validate_with_strict_schema(
    schema_name: str, payload: dict[str, Any]
) -> tuple[bool, list[dict[str, Any]]]:
    schema_cls = STRICT_SCHEMA_MAP[schema_name]
    try:
        schema_cls.model_validate(payload)
        return True, []
    except ValidationError as exc:
        return False, exc.errors()


def classify_error(error: dict[str, Any]) -> str:
    error_type = error["type"]
    message = error["msg"]

    if error_type == "missing":
        return "缺字段"
    if error_type == "extra_forbidden":
        return "多余字段"
    if "不能为空" in message:
        return "空值"
    if "日期格式" in message or "Input should be '高', '中' or '低'" in message:
        return "格式错"
    return "类型错"


def build_retry_prompt(
    sample: dict[str, Any], llm_output: dict[str, Any], errors: list[dict[str, Any]]
) -> str:
    lines: list[str] = [
        "你上一次返回的 JSON 没有通过校验，请严格修复后重新输出。",
        f"目标 Schema: {sample['schema']}",
        "修复要求：",
    ]

    for index, error in enumerate(errors, start=1):
        location = " -> ".join(str(part) for part in error["loc"])
        category = classify_error(error)
        lines.append(f"{index}. [{category}] 字段 {location}: {error['msg']}")

    lines.extend(
        [
            "输出规则：",
            "- 只输出合法 JSON，不要附带解释。",
            "- 只保留 Schema 中定义的字段。",
            "- 缺字段必须补齐，类型必须匹配。",
            "- 日期使用 YYYY-MM-DD，similarity 只能是 高/中/低。",
            "- formal_query 不能为空，expanded_keywords 至少 1 个元素。",
            "上一次输出：",
            json.dumps(llm_output, ensure_ascii=False, indent=2),
        ]
    )
    return "\n".join(lines)


def normalize_date(value: str) -> str:
    matched = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", value)
    if matched:
        year, month, day = matched.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
    return value


def split_differences(value: str) -> list[str]:
    items = re.split(r"[，；。]", value)
    cleaned = [item.strip() for item in items if item.strip()]
    return cleaned or [value]


def repair_output(sample: dict[str, Any], llm_output: dict[str, Any]) -> dict[str, Any]:
    repaired = deepcopy(llm_output)
    schema_name = sample["schema"]

    if schema_name == "PatentInfo":
        repaired.setdefault("patent_id", "UNKNOWN-PATENT-ID")
        repaired.setdefault("core_invention", f"{repaired.get('tech_domain', '未知技术')}相关方案")
        if isinstance(repaired.get("ipc_codes"), str):
            repaired["ipc_codes"] = [repaired["ipc_codes"]]
        if isinstance(repaired.get("filing_date"), str):
            repaired["filing_date"] = normalize_date(repaired["filing_date"])

    if schema_name == "PatentComparison":
        allowed_keys = {
            "patent_a_id",
            "patent_b_id",
            "common_domain",
            "key_differences",
            "similarity",
            "conclusion",
        }
        repaired = {key: value for key, value in repaired.items() if key in allowed_keys}
        if isinstance(repaired.get("key_differences"), str):
            repaired["key_differences"] = split_differences(repaired["key_differences"])
        similarity_mapping = {"High": "高", "Medium": "中", "Low": "低"}
        similarity = repaired.get("similarity")
        if isinstance(similarity, str):
            repaired["similarity"] = similarity_mapping.get(similarity, similarity)

    if schema_name == "QueryRewrite":
        original_query = repaired.get("original_query", "")
        if not repaired.get("formal_query"):
            repaired["formal_query"] = original_query
        if not repaired.get("expanded_keywords"):
            repaired["expanded_keywords"] = [original_query] if original_query else ["待补充关键词"]

    return repaired


def print_error_summary(errors: list[dict[str, Any]]) -> None:
    for error in errors:
        location = " -> ".join(str(part) for part in error["loc"])
        category = classify_error(error)
        print(f"    - [{category}] {location}: {error['msg']}")


def run_retry_demo() -> None:
    samples = load_samples()
    first_pass_success = 0
    retry_success = 0
    retry_failed = 0

    print("=" * 72)
    print("D11 二次解析演示")
    print("=" * 72)

    for sample in samples:
        print(f"\n[{sample['id']}] {sample['description']}")
        original_output = deepcopy(sample["llm_output"])
        passed, errors = validate_with_strict_schema(sample["schema"], original_output)

        if passed:
            first_pass_success += 1
            print("  首轮校验：通过")
            continue

        print("  首轮校验：失败")
        print_error_summary(errors)

        retry_prompt = build_retry_prompt(sample, original_output, errors)
        print("  修复提示：")
        for line in retry_prompt.splitlines()[:10]:
            print(f"    {line}")
        if len(retry_prompt.splitlines()) > 10:
            print("    ...")

        repaired_output = repair_output(sample, original_output)
        retry_passed, retry_errors = validate_with_strict_schema(sample["schema"], repaired_output)

        if retry_passed:
            retry_success += 1
            print("  二次解析：通过")
        else:
            retry_failed += 1
            print("  二次解析：失败")
            print_error_summary(retry_errors)

    total = len(samples)
    final_success = first_pass_success + retry_success

    print(f"\n{'=' * 72}")
    print("结果汇总")
    print(f"{'=' * 72}")
    print(f"总样本数: {total}")
    print(f"首轮直接成功: {first_pass_success}")
    print(f"重试后成功: {retry_success}")
    print(f"重试后仍失败: {retry_failed}")
    print(f"两轮内成功率: {final_success}/{total} = {final_success / total:.0%}")


if __name__ == "__main__":
    run_retry_demo()

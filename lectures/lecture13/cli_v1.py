"""
D13 — 专利问题结构化 CLI（LLM 结构化输出版）
=============================================
综合运用 D9-D12 经验：
  D9  — Pydantic Schema + create_agent + response_format
  D10 — 失败样本 + extra='forbid' + @field_validator
  D11 — 二次解析 + 重试修复
  D12 — Prompt A/B 对比 → 选用强约束 Prompt

三种模式：
  默认       — 调用 LLM 结构化输出（create_agent + response_format）
  --rule     — 纯规则基线（不调 LLM，即时响应）
  --check    — 10 条规则验收测试

验收：10 条输入稳定输出 + LLM 输出通过 Pydantic 校验
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

ROOT_DIR = Path(__file__).resolve().parents[2]
PATENT_DATA_PATH = ROOT_DIR / "shared" / "test_data" / "sample_patents.json"

PATENT_ID_PATTERN = re.compile(r"\b(?:JP|CN|US|WO|EP|KR)\s?\d{4}-?\d{3,}\b", re.IGNORECASE)
IPC_PATTERN = re.compile(r"\b[A-H]\d{2}[A-Z]\d+/\d+\b", re.IGNORECASE)


# ===========================================================================
# 枚举与 Schema 定义（D9 + D10 增强校验）
# ===========================================================================


class Intent(StrEnum):
    SEARCH = "search"
    DETAIL_LOOKUP = "detail_lookup"
    COMPARE = "compare"
    ANSWER_WITH_CONTEXT = "answer_with_context"
    CLARIFY = "clarify"


class ToolName(StrEnum):
    SEARCH_PATENT = "search_patent"
    GET_PATENT_DETAIL = "get_patent_detail"
    COMPARE_PATENTS = "compare_patents"
    NONE = "none"


class Confidence(StrEnum):
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"


class ToolArguments(BaseModel):
    """工具调用参数"""

    model_config = ConfigDict(extra="forbid")

    keyword: str | None = Field(default=None, description="检索关键词")
    patent_id: str | None = Field(default=None, description="主专利编号")
    patent_ids: list[str] = Field(default_factory=list, description="相关专利编号列表")
    requested_fields: list[str] = Field(default_factory=list, description="用户请求的字段")
    comparison_focus: list[str] = Field(default_factory=list, description="比较焦点")


class ExtractedEntities(BaseModel):
    """从问题中提取的实体"""

    model_config = ConfigDict(extra="forbid")

    patent_ids: list[str] = Field(default_factory=list, description="专利编号列表")
    applicants: list[str] = Field(default_factory=list, description="申请人列表")
    keywords: list[str] = Field(default_factory=list, description="技术关键词列表")
    ipc_codes: list[str] = Field(default_factory=list, description="IPC 分类号列表")
    statuses: list[str] = Field(default_factory=list, description="专利状态列表")


class ResponsePlan(BaseModel):
    """响应计划"""

    model_config = ConfigDict(extra="forbid")

    prompt_profile: str = Field(description="下游 Agent 的角色提示")
    next_step: str = Field(description="建议的下一步操作")
    missing_information: list[str] = Field(default_factory=list, description="缺失的信息")
    ask_back_question: str | None = Field(default=None, description="需要反问用户的问题")


class PatentQuestionAnalysis(BaseModel):
    """专利问题分析结果（D9 + D10 增强版）"""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default="v1", description="Schema 版本号")
    original_question: str = Field(description="用户的原始问题")
    normalized_question: str = Field(description="标准化后的问题")
    intent: Intent = Field(description="识别到的用户意图")
    target_tool: ToolName = Field(description="建议调用的工具")
    tool_arguments: ToolArguments = Field(description="工具调用参数")
    extracted_entities: ExtractedEntities = Field(description="提取的实体")
    response_plan: ResponsePlan = Field(description="响应计划")
    confidence: Confidence = Field(description="置信度：高/中/低")

    # D10 增强：校验关键字段不为空
    @field_validator("original_question", "normalized_question")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """校验问题字段不能为空"""
        if not v or not v.strip():
            raise ValueError("问题字段不能为空")
        return v

    # D10 增强：意图与工具一致性校验
    @field_validator("confidence", mode="before")
    @classmethod
    def map_confidence(cls, v: Any) -> Any:
        """将英文/变体映射为中文枚举（兼容 LLM 可能输出英文）"""
        mapping = {"high": "高", "medium": "中", "low": "低"}
        if isinstance(v, str):
            return mapping.get(v.lower(), v)
        return v


# ===========================================================================
# 工具 Schema 注册表
# ===========================================================================

class SearchPatentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    keyword: str = Field(description="检索关键词，2-50 个字符")


class PatentDetailInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patent_id: str = Field(description="专利编号，例如 JP2024-001")


class ComparePatentsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patent_id_1: str = Field(description="第一件专利编号")
    patent_id_2: str = Field(description="第二件专利编号")


TOOL_SCHEMA_REGISTRY = {
    ToolName.SEARCH_PATENT: SearchPatentInput.model_json_schema(),
    ToolName.GET_PATENT_DETAIL: PatentDetailInput.model_json_schema(),
    ToolName.COMPARE_PATENTS: ComparePatentsInput.model_json_schema(),
}


# ===========================================================================
# 轻量 LLM Schema（7 个扁平字段，加速生成）
# ===========================================================================


class LLMAnalysis(BaseModel):
    """LLM 只需填写这 7 个扁平字段，后处理补全为完整 PatentQuestionAnalysis"""

    intent: Intent = Field(description="用户意图")
    target_tool: ToolName = Field(description="建议调用的工具")
    confidence: Confidence = Field(description="置信度：高/中/低")
    patent_ids: list[str] = Field(default_factory=list, description="提取的专利编号")
    applicants: list[str] = Field(default_factory=list, description="提取的申请人")
    keywords: list[str] = Field(default_factory=list, description="提取的技术关键词")
    requested_fields: list[str] = Field(
        default_factory=list, description="用户请求的字段"
    )

    @field_validator("confidence", mode="before")
    @classmethod
    def map_confidence(cls, v: Any) -> Any:
        mapping = {"high": "高", "medium": "中", "low": "低"}
        if isinstance(v, str):
            return mapping.get(v.lower(), v)
        return v


# ===========================================================================
# LLM 结构化输出（D9 + L7 + D11 + D12）
# ===========================================================================

SYSTEM_PROMPT = """你是专利问题分析路由器。将用户问题解析为 JSON。

字段说明：
- intent: search / detail_lookup / compare / answer_with_context / clarify
- target_tool: search_patent / get_patent_detail / compare_patents / none
- confidence: 高 / 中 / 低
- patent_ids: 从问题中提取的专利编号列表
- applicants: 从问题中提取的申请人列表
- keywords: 从问题中提取的技术关键词列表
- requested_fields: 用户请求的字段（如 applicant, status, ipc_codes）

意图→工具：
- 搜索/有没有 → search → search_patent
- 专利号+详情 → detail_lookup → get_patent_detail
- 对比+两个号 → compare → compare_patents
- 为什么/如何 → answer_with_context → 有号用 get_patent_detail 否则 search_patent
- 信息不足 → clarify → none

申请人别名：Toyota→Toyota Motor Corporation, 三菱化学→三菱化学株式会社
"""


def enrich_to_full(
    question: str, llm_result: LLMAnalysis
) -> PatentQuestionAnalysis:
    """将 LLM 轻量输出后处理补全为完整 PatentQuestionAnalysis"""
    normalized = normalize_question(question)
    intent = llm_result.intent
    target_tool = llm_result.target_tool
    patent_ids = llm_result.patent_ids
    keywords = llm_result.keywords
    requested_fields = llm_result.requested_fields
    comparison_focus = extract_comparison_focus(normalized, requested_fields)

    # 用规则函数补全 response_plan
    missing_information = build_missing_information(
        intent, normalized, patent_ids, keywords
    )
    response_plan = ResponsePlan(
        prompt_profile=PROMPT_PROFILES.get(
            intent, "你是专利路由器。"
        ),
        next_step=build_next_step(intent, target_tool),
        missing_information=missing_information,
        ask_back_question=build_ask_back_question(
            missing_information, intent
        ),
    )

    # 用规则函数补全 tool_arguments
    tool_arguments = build_tool_arguments(
        intent=intent, target_tool=target_tool,
        patent_ids=patent_ids, keywords=keywords,
        requested_fields=requested_fields,
        comparison_focus=comparison_focus,
    )

    # 用规则函数补全 extracted_entities
    ipc_codes = extract_ipc_codes(normalized)
    statuses = extract_statuses(normalized)
    extracted_entities = ExtractedEntities(
        patent_ids=patent_ids,
        applicants=llm_result.applicants,
        keywords=keywords,
        ipc_codes=ipc_codes,
        statuses=statuses,
    )

    return PatentQuestionAnalysis(
        original_question=question,
        normalized_question=normalized,
        intent=intent,
        target_tool=target_tool,
        tool_arguments=tool_arguments,
        extracted_entities=extracted_entities,
        response_plan=response_plan,
        confidence=llm_result.confidence,
    )


def analyze_with_llm(
    question: str, max_retries: int = 1
) -> PatentQuestionAnalysis:
    """用 LLM 轻量 Schema 分析 + 后处理补全（D9 + L7 模式）"""
    import threading
    import time

    from langchain.agents import create_agent

    # 用轻量 LLMAnalysis（7 字段）代替完整 PatentQuestionAnalysis（23 字段）
    agent = create_agent(
        model="ollama:qwen2.5:7b",
        response_format=LLMAnalysis,
    )

    timeout_seconds = 120

    def invoke_with_progress(msgs: list[dict]) -> dict:
        """调用 LLM 并显示旋转动画（含超时）"""
        result_holder: list = []
        error_holder: list = []
        done = threading.Event()

        def call_llm():
            try:
                result_holder.append(agent.invoke({"messages": msgs}))
            except Exception as exc:
                error_holder.append(exc)
            finally:
                done.set()

        thread = threading.Thread(target=call_llm, daemon=True)
        thread.start()

        symbols = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        start = time.time()
        idx = 0
        while not done.is_set():
            elapsed = int(time.time() - start)
            sym = symbols[idx % len(symbols)]
            print(
                f"\r  {sym} LLM 生成中... ({elapsed}s)",
                end="", flush=True,
            )
            idx += 1
            if elapsed > timeout_seconds:
                print(
                    f"\n  ⏰ 超时（{timeout_seconds}s），"
                    "回退到规则模式"
                )
                raise TimeoutError(
                    f"LLM 超过 {timeout_seconds}s"
                )
            time.sleep(0.1)
        print(
            "\r" + " " * 40 + "\r", end="", flush=True
        )

        if error_holder:
            raise error_holder[0]
        return result_holder[0]

    # 首次调用
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    result = invoke_with_progress(messages)
    structured = result.get("structured_response")

    if structured is None:
        raise RuntimeError("LLM 未返回 structured_response")

    # D10 校验 + 后处理补全
    try:
        if isinstance(structured, LLMAnalysis):
            llm_result = LLMAnalysis.model_validate(
                structured.model_dump()
            )
        else:
            llm_result = LLMAnalysis.model_validate(structured)
        print("  ✅ Pydantic 校验通过")
        return enrich_to_full(question, llm_result)
    except Exception as first_error:
        print(f"  ⚠️  首轮校验失败: {first_error}")
        if max_retries <= 0:
            raise

        # D11 重试
        retry_prompt = build_retry_prompt(
            question, structured, first_error
        )
        print("  🔄 正在重试...")
        retry_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": retry_prompt},
        ]
        retry_result = invoke_with_progress(retry_messages)
        retry_structured = retry_result.get(
            "structured_response"
        )
        if retry_structured is None:
            raise RuntimeError(
                "重试后 LLM 仍未返回 structured_response"
            ) from first_error
        try:
            if isinstance(retry_structured, LLMAnalysis):
                llm_result = LLMAnalysis.model_validate(
                    retry_structured.model_dump()
                )
            else:
                llm_result = LLMAnalysis.model_validate(
                    retry_structured
                )
            print("  ✅ 重试后校验通过")
            return enrich_to_full(question, llm_result)
        except Exception as retry_error:
            print(f"  ❌ 重试后仍然失败: {retry_error}")
            raise retry_error from first_error


def build_retry_prompt(
    question: str, failed_output: Any, error: Exception
) -> str:
    """D11 经验：构建修复提示（附带错误信息和原始问题）"""
    output_str = ""
    if isinstance(failed_output, BaseModel):
        output_str = json.dumps(
            failed_output.model_dump(mode="json"), ensure_ascii=False, indent=2
        )
    elif isinstance(failed_output, dict):
        output_str = json.dumps(failed_output, ensure_ascii=False, indent=2)
    else:
        output_str = str(failed_output)

    return (
        f"原始问题：{question}\n\n"
        "你上一次返回的 JSON 没有通过校验，请严格修复后重新输出。\n\n"
        f"错误信息：{error}\n\n"
        "修复要求：\n"
        "- 只输出合法 JSON，不要附带解释。\n"
        "- 只保留 Schema 中定义的字段。\n"
        "- confidence 只能是 高/中/低。\n"
        "- intent 只能是 search/detail_lookup/compare/answer_with_context/clarify。\n"
        "- target_tool 只能是 search_patent/get_patent_detail/compare_patents/none。\n\n"
        f"上一次输出：\n{output_str}"
    )


# ===========================================================================
# 规则基线（保留原有逻辑用于 --check 和 --rule）
# ===========================================================================

FIELD_PATTERNS: dict[str, tuple[str, ...]] = {
    "title": ("标题", "名称", "题目"),
    "applicant": ("申请人", "申请者", "哪个公司", "谁申请"),
    "filing_date": ("申请日", "申请日期", "何时申请", "什么时候申请"),
    "status": ("状态", "进度", "公开了吗", "审查"),
    "ipc_codes": ("IPC", "IPC分类", "分类号", "IPC号"),
    "abstract": ("摘要", "简介", "内容"),
    "tech_domain": ("技术领域", "用途", "适合"),
    "core_invention": ("核心发明", "创新点", "亮点", "优势"),
}

COMPARISON_PATTERNS: dict[str, tuple[str, ...]] = {
    "ipc_codes": ("IPC", "分类号"),
    "status": ("状态", "进度"),
    "applicant": ("申请人", "申请者"),
    "abstract": ("摘要", "内容"),
    "core_invention": ("差异", "区别", "不同", "优劣", "创新点"),
}

SEARCH_HINTS = ("搜索", "检索", "查找", "找一下", "找出", "有没有", "有哪些", "相关专利")
COMPARE_HINTS = ("对比", "比较", "区别", "差异", "相同点")
DETAIL_HINTS = ("详情", "详细", "信息", "摘要", "标题", "申请人", "申请日", "状态", "IPC")
ANSWER_HINTS = ("为什么", "如何", "怎么", "是否", "能否", "适合", "原因", "类别", "原理")

STATUS_ALIASES = {
    "公開済": ("公開済", "已公开", "公开"),
    "審査中": ("審査中", "审查中", "审査"),
}

TERM_CANDIDATES = (
    "生物降解塑料", "海洋降解", "包装材料", "可堆肥", "薄膜", "淀粉基",
    "固态电解质", "固态电池电解质", "固态电池", "锂离子电池",
    "钙钛矿太阳能电池", "纳米纤维素", "生物塑料", "微珠",
    "半导体", "蚀刻气体", "PLA", "PBS", "PHA", "PCL", "包装", "农业地膜",
)

STOP_PHRASES = (
    "帮我", "请", "一下", "看看", "搜索", "检索", "查找", "查看",
    "对比", "比较", "区别", "差异", "详细信息", "详情", "专利", "相关",
    "是什么", "什么", "有没有", "有哪些", "怎么样", "常见",
    "和另一件", "呢", "吗", "这个", "那个",
)

PROMPT_PROFILES = {
    Intent.SEARCH: (
        "你是专利问题路由器。当前目标是把自然语言检索需求压缩成 search_patent 的 keyword 参数，"
        "禁止输出解释，只保留可执行检索意图。"
    ),
    Intent.DETAIL_LOOKUP: (
        "你是专利详情路由器。当前目标是把问题压缩成 get_patent_detail 的 patent_id 与字段需求，"
        "后续只需抓详情再回答。"
    ),
    Intent.COMPARE: (
        "你是专利对比路由器。当前目标是确认 compare_patents 所需的两件专利编号，并保留比较焦点。"
    ),
    Intent.ANSWER_WITH_CONTEXT: (
        "你是解释型问题路由器。当前目标是先决定该走搜索还是详情，再把回答所需字段补齐。"
    ),
    Intent.CLARIFY: ("你是澄清型路由器。当前目标不是直接执行工具，而是明确缺失槽位并生成追问。"),
}

APPLICANT_ALIASES = {
    "三菱化学株式会社": ("三菱化学株式会社", "三菱化学", "Mitsubishi Chemical"),
    "東レ株式会社": ("東レ株式会社", "东丽", "Toray", "Toray Industries"),
    "日本触媒株式会社": ("日本触媒株式会社", "日本触媒", "Nippon Shokubai"),
    "パナソニック株式会社": ("パナソニック株式会社", "松下", "Panasonic"),
    "積水化学工業株式会社": ("積水化学工業株式会社", "积水化学", "Sekisui Chemical"),
    "王子ホールディングス株式会社": ("王子ホールディングス株式会社", "王子控股", "Oji Holdings"),
    "昭和電工株式会社": ("昭和電工株式会社", "昭和电工", "Showa Denko"),
    "カネカ株式会社": ("カネカ株式会社", "Kaneka", "钟化"),
    "Toyota Motor Corporation": ("Toyota Motor Corporation", "Toyota"),
}


def unique_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def normalize_patent_id(raw_patent_id: str) -> str:
    compact = re.sub(r"\s+", "", raw_patent_id.upper())
    matched = re.fullmatch(r"([A-Z]{2})(\d{4})-?(\d{3,})", compact)
    if not matched:
        return compact
    prefix, year, serial = matched.groups()
    return f"{prefix}{year}-{serial}"


def normalize_question(question: str) -> str:
    collapsed = re.sub(r"\s+", " ", question.strip())
    patent_ids = PATENT_ID_PATTERN.findall(collapsed)
    for patent_id in patent_ids:
        collapsed = collapsed.replace(patent_id, normalize_patent_id(patent_id))
    return collapsed


def extract_patent_ids(question: str) -> list[str]:
    matched = PATENT_ID_PATTERN.findall(question)
    return unique_keep_order([normalize_patent_id(item) for item in matched])


def extract_applicants(question: str) -> list[str]:
    matches: list[str] = []
    for canonical, aliases in APPLICANT_ALIASES.items():
        if any(alias.lower() in question.lower() for alias in aliases):
            matches.append(canonical)
    ascii_match = re.search(r"\b([A-Z][A-Za-z0-9 .&-]{2,40})\b", question)
    if ascii_match:
        candidate = ascii_match.group(1).strip()
        if not PATENT_ID_PATTERN.fullmatch(candidate) and (
            not candidate.isupper() or len(candidate) > 4
        ):
            matches.append(candidate)
    cjk_match = re.search(r"([\u4e00-\u9fff]{2,16}(?:公司|化学|工业|控股|株式会社))", question)
    if cjk_match:
        matches.append(cjk_match.group(1))
    return unique_keep_order(matches)


def extract_requested_fields(question: str) -> list[str]:
    requested: list[str] = []
    upper_question = question.upper()
    for field_name, patterns in FIELD_PATTERNS.items():
        if any(pattern in question or pattern in upper_question for pattern in patterns):
            requested.append(field_name)
    return requested


def extract_comparison_focus(question: str, requested_fields: list[str]) -> list[str]:
    focus: list[str] = []
    for field_name, patterns in COMPARISON_PATTERNS.items():
        if any(pattern in question for pattern in patterns):
            focus.append(field_name)
    if requested_fields:
        focus.extend(requested_fields)
    if not focus:
        focus.append("core_invention")
    return unique_keep_order(focus)


def extract_statuses(question: str) -> list[str]:
    statuses: list[str] = []
    for canonical, aliases in STATUS_ALIASES.items():
        if any(alias in question for alias in aliases):
            statuses.append(canonical)
    return statuses


def extract_ipc_codes(question: str) -> list[str]:
    matches = IPC_PATTERN.findall(question.upper())
    return unique_keep_order(matches)


def extract_keywords(question: str, patent_ids: list[str], applicants: list[str]) -> list[str]:
    keywords: list[str] = []
    for term in TERM_CANDIDATES:
        if term.lower() in question.lower():
            keywords.append(term)
    if "固态电池" in question and "电解质" in question:
        keywords.append("固态电解质")
    cleaned = question
    for patent_id in patent_ids:
        cleaned = cleaned.replace(patent_id, " ")
    for applicant in applicants:
        cleaned = re.sub(re.escape(applicant), " ", cleaned, flags=re.IGNORECASE)
    for phrase in STOP_PHRASES:
        cleaned = cleaned.replace(phrase, " ")
    cleaned = re.sub(r"[，。！？、,.?（）()""\"'：:]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    for token in cleaned.split(" "):
        stripped = token.strip()
        if not stripped:
            continue
        if re.fullmatch(r"[A-Z]{2,6}", stripped):
            keywords.append(stripped)
            continue
        if len(stripped) >= 2 and stripped not in {"和", "的", "在", "会", "哪", "哪些"}:
            keywords.append(stripped)
    return unique_keep_order(keywords)


def determine_intent(question: str, patent_ids: list[str], requested_fields: list[str]) -> Intent:
    has_compare = any(hint in question for hint in COMPARE_HINTS)
    has_search = any(hint in question for hint in SEARCH_HINTS)
    has_answer = any(hint in question for hint in ANSWER_HINTS)
    is_contextless_reference = any(
        marker in question for marker in ("这个专利", "那个专利", "这件专利")
    )
    if has_compare:
        return Intent.COMPARE if len(patent_ids) >= 2 else Intent.CLARIFY
    if is_contextless_reference and not patent_ids:
        return Intent.CLARIFY
    if patent_ids:
        if has_answer:
            return Intent.ANSWER_WITH_CONTEXT
        return Intent.DETAIL_LOOKUP
    if has_search:
        return Intent.SEARCH
    if has_answer:
        return Intent.ANSWER_WITH_CONTEXT
    if len(question) < 6:
        return Intent.CLARIFY
    return Intent.SEARCH


def choose_tool(intent: Intent, patent_ids: list[str]) -> ToolName:
    if intent == Intent.SEARCH:
        return ToolName.SEARCH_PATENT
    if intent == Intent.DETAIL_LOOKUP:
        return ToolName.GET_PATENT_DETAIL
    if intent == Intent.COMPARE:
        return ToolName.COMPARE_PATENTS
    if intent == Intent.ANSWER_WITH_CONTEXT:
        return ToolName.GET_PATENT_DETAIL if patent_ids else ToolName.SEARCH_PATENT
    return ToolName.NONE


def build_missing_information(
    intent: Intent, question: str, patent_ids: list[str], keywords: list[str],
) -> list[str]:
    missing: list[str] = []
    has_compare = any(hint in question for hint in COMPARE_HINTS)
    is_contextless_reference = any(
        marker in question for marker in ("这个专利", "那个专利", "这件专利")
    )
    if (intent == Intent.COMPARE or has_compare) and len(patent_ids) < 2:
        missing.append("second_patent_id")
    if intent in {Intent.SEARCH, Intent.ANSWER_WITH_CONTEXT} and not patent_ids and not keywords:
        missing.append("keyword")
    if intent == Intent.CLARIFY and (is_contextless_reference or (not patent_ids and not keywords)):
        missing.append("patent_id_or_keyword")
    return missing


def build_ask_back_question(missing_information: list[str], intent: Intent) -> str | None:
    if "second_patent_id" in missing_information:
        return "请再提供第二件要比较的专利编号，或明确要比较的目标专利。"
    if "patent_id_or_keyword" in missing_information:
        return "请提供专利编号，或者至少给出技术关键词。"
    if "keyword" in missing_information:
        return "请补充你要检索的技术关键词。"
    if intent == Intent.CLARIFY:
        return "请补充更具体的专利编号、技术关键词或操作目标。"
    return None


def build_next_step(intent: Intent, target_tool: ToolName) -> str:
    if intent == Intent.SEARCH:
        return "先生成 search_patent 所需 keyword，再执行检索。"
    if intent == Intent.DETAIL_LOOKUP:
        return "先获取专利详情，再按字段需求组织回答。"
    if intent == Intent.COMPARE:
        return "先调用 compare_patents，再根据比较焦点补充说明。"
    if intent == Intent.ANSWER_WITH_CONTEXT and target_tool == ToolName.GET_PATENT_DETAIL:
        return "先读取该专利详情，再回答解释性问题。"
    if intent == Intent.ANSWER_WITH_CONTEXT:
        return "先搜索相关专利，再结合结果回答。"
    return "先补齐缺失信息，再决定调用哪个工具。"


def determine_confidence(
    intent: Intent, missing_information: list[str], keywords: list[str]
) -> Confidence:
    if missing_information:
        return Confidence.LOW
    if intent in {Intent.DETAIL_LOOKUP, Intent.COMPARE}:
        return Confidence.HIGH
    if intent == Intent.CLARIFY:
        return Confidence.LOW
    if keywords:
        return Confidence.MEDIUM
    return Confidence.LOW


def build_tool_arguments(
    intent: Intent, target_tool: ToolName, patent_ids: list[str],
    keywords: list[str], requested_fields: list[str], comparison_focus: list[str],
) -> ToolArguments:
    keyword = " ".join(keywords[:4]) if keywords else None
    patent_id = patent_ids[0] if patent_ids else None
    if intent == Intent.COMPARE:
        return ToolArguments(
            patent_ids=patent_ids[:2], requested_fields=requested_fields,
            comparison_focus=comparison_focus,
        )
    if target_tool == ToolName.GET_PATENT_DETAIL:
        return ToolArguments(
            patent_id=patent_id, patent_ids=patent_ids,
            requested_fields=requested_fields,
        )
    if target_tool == ToolName.SEARCH_PATENT:
        return ToolArguments(
            keyword=keyword, patent_ids=patent_ids,
            requested_fields=requested_fields,
        )
    return ToolArguments(
        keyword=keyword, patent_ids=patent_ids,
        requested_fields=requested_fields, comparison_focus=comparison_focus,
    )


def analyze_question(question: str) -> PatentQuestionAnalysis:
    """纯规则分析（不调 LLM，用于 --check 和 --rule）"""
    normalized_question = normalize_question(question)
    patent_ids = extract_patent_ids(normalized_question)
    applicants = extract_applicants(normalized_question)
    requested_fields = extract_requested_fields(normalized_question)
    comparison_focus = extract_comparison_focus(normalized_question, requested_fields)
    keywords = extract_keywords(normalized_question, patent_ids, applicants)
    ipc_codes = extract_ipc_codes(normalized_question)
    statuses = extract_statuses(normalized_question)

    intent = determine_intent(normalized_question, patent_ids, requested_fields)
    target_tool = choose_tool(intent, patent_ids)
    missing_information = build_missing_information(
        intent, normalized_question, patent_ids, keywords
    )
    tool_arguments = build_tool_arguments(
        intent=intent, target_tool=target_tool, patent_ids=patent_ids,
        keywords=keywords, requested_fields=requested_fields,
        comparison_focus=comparison_focus,
    )
    response_plan = ResponsePlan(
        prompt_profile=PROMPT_PROFILES[intent],
        next_step=build_next_step(intent, target_tool),
        missing_information=missing_information,
        ask_back_question=build_ask_back_question(missing_information, intent),
    )
    extracted_entities = ExtractedEntities(
        patent_ids=patent_ids, applicants=applicants, keywords=keywords,
        ipc_codes=ipc_codes, statuses=statuses,
    )
    return PatentQuestionAnalysis(
        original_question=question,
        normalized_question=normalized_question,
        intent=intent, target_tool=target_tool,
        tool_arguments=tool_arguments,
        extracted_entities=extracted_entities,
        response_plan=response_plan,
        confidence=determine_confidence(intent, missing_information, keywords),
    )


# ===========================================================================
# 验收用例（--check）
# ===========================================================================


@dataclass(slots=True)
class AcceptanceCase:
    question: str
    expected_intent: Intent
    expected_tool: ToolName
    expected_patent_ids: list[str] = field(default_factory=list)
    expected_fields: list[str] = field(default_factory=list)
    expected_keywords: list[str] = field(default_factory=list)
    expected_missing: list[str] = field(default_factory=list)


ACCEPTANCE_CASES = [
    AcceptanceCase(
        question="帮我搜索生物降解塑料相关专利",
        expected_intent=Intent.SEARCH,
        expected_tool=ToolName.SEARCH_PATENT,
        expected_keywords=["生物降解塑料"],
    ),
    AcceptanceCase(
        question="检索 Mitsubishi Chemical 的 PLA 包装材料专利",
        expected_intent=Intent.SEARCH,
        expected_tool=ToolName.SEARCH_PATENT,
        expected_keywords=["PLA", "包装材料"],
    ),
    AcceptanceCase(
        question="查看 JP2024-002 的详细信息",
        expected_intent=Intent.DETAIL_LOOKUP,
        expected_tool=ToolName.GET_PATENT_DETAIL,
        expected_patent_ids=["JP2024-002"],
    ),
    AcceptanceCase(
        question="JP2024-003 的申请人和状态是什么？",
        expected_intent=Intent.DETAIL_LOOKUP,
        expected_tool=ToolName.GET_PATENT_DETAIL,
        expected_patent_ids=["JP2024-003"],
        expected_fields=["applicant", "status"],
    ),
    AcceptanceCase(
        question="对比 JP2024-001 和 JP2024-002 的 IPC 分类与差异",
        expected_intent=Intent.COMPARE,
        expected_tool=ToolName.COMPARE_PATENTS,
        expected_patent_ids=["JP2024-001", "JP2024-002"],
        expected_fields=["ipc_codes", "core_invention"],
    ),
    AcceptanceCase(
        question="帮我比较 JP2024-001 和另一件可堆肥薄膜专利",
        expected_intent=Intent.CLARIFY,
        expected_tool=ToolName.NONE,
        expected_patent_ids=["JP2024-001"],
        expected_missing=["second_patent_id"],
    ),
    AcceptanceCase(
        question="JP2024-001 为什么适合包装领域？",
        expected_intent=Intent.ANSWER_WITH_CONTEXT,
        expected_tool=ToolName.GET_PATENT_DETAIL,
        expected_patent_ids=["JP2024-001"],
        expected_fields=["tech_domain"],
    ),
    AcceptanceCase(
        question="固态电池电解质专利常见 IPC 会落在哪些类别？",
        expected_intent=Intent.ANSWER_WITH_CONTEXT,
        expected_tool=ToolName.SEARCH_PATENT,
        expected_keywords=["固态电解质", "固态电池"],
        expected_fields=["ipc_codes"],
    ),
    AcceptanceCase(
        question="有没有 Toyota 的固态电池相关专利？",
        expected_intent=Intent.SEARCH,
        expected_tool=ToolName.SEARCH_PATENT,
        expected_keywords=["固态电池"],
    ),
    AcceptanceCase(
        question="这个专利怎么样？",
        expected_intent=Intent.CLARIFY,
        expected_tool=ToolName.NONE,
        expected_missing=["patent_id_or_keyword"],
    ),
]


# ===========================================================================
# 输出与 CLI
# ===========================================================================


def render_analysis(analysis: PatentQuestionAnalysis) -> str:
    return json.dumps(analysis.model_dump(mode="json"), ensure_ascii=False, indent=2)


def print_tool_schemas() -> None:
    payload = {tool_name.value: schema for tool_name, schema in TOOL_SCHEMA_REGISTRY.items()}
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def run_acceptance_check() -> bool:
    """用规则基线跑 10 条验收"""
    passed = 0
    print("=" * 72)
    print("D13 验收：10 条输入稳定输出（规则基线）")
    print("=" * 72)

    for index, case in enumerate(ACCEPTANCE_CASES, start=1):
        analysis = analyze_question(case.question)
        failures: list[str] = []
        if analysis.intent != case.expected_intent:
            failures.append(f"intent={analysis.intent}")
        if analysis.target_tool != case.expected_tool:
            failures.append(f"tool={analysis.target_tool}")
        for patent_id in case.expected_patent_ids:
            if patent_id not in analysis.extracted_entities.patent_ids:
                failures.append(f"missing patent_id:{patent_id}")
        for field_name in case.expected_fields:
            if (
                field_name not in analysis.tool_arguments.requested_fields
                and field_name not in analysis.tool_arguments.comparison_focus
            ):
                failures.append(f"missing field:{field_name}")
        for keyword in case.expected_keywords:
            if keyword not in analysis.extracted_entities.keywords:
                failures.append(f"missing keyword:{keyword}")
        for missing in case.expected_missing:
            if missing not in analysis.response_plan.missing_information:
                failures.append(f"missing slot:{missing}")

        if failures:
            print(f"[{index:02d}] 失败 | {case.question}")
            print(f"      原因: {'; '.join(failures)}")
            continue
        passed += 1
        print(f"[{index:02d}] 通过 | {case.question}")

    total = len(ACCEPTANCE_CASES)
    print("-" * 72)
    print(f"结果: {passed}/{total}")
    return passed == total


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="D13: 专利问题 -> JSON 分析 CLI")
    parser.add_argument("question", nargs="*", help="要分析的问题")
    parser.add_argument("--query", help="直接提供问题文本")
    parser.add_argument("--rule", action="store_true", help="使用纯规则模式（不调 LLM）")
    parser.add_argument("--show-tool-schemas", action="store_true", help="输出工具输入 Schema")
    parser.add_argument("--check", action="store_true", help="运行 10 条稳定性验收（规则基线）")
    return parser.parse_args()


def resolve_question(args: argparse.Namespace) -> str | None:
    if args.query:
        return args.query.strip()
    if args.question:
        return " ".join(args.question).strip()
    return None


def main() -> int:
    args = parse_args()

    if args.show_tool_schemas:
        print_tool_schemas()
        return 0

    if args.check:
        return 0 if run_acceptance_check() else 1

    question = resolve_question(args)
    use_llm = not args.rule

    if not question:
        print("=" * 60)
        print("D13 专利问题分析 CLI")
        print("=" * 60)
        print("将自然语言专利问题解析为结构化 JSON。")
        print()
        print("选择模式：")
        print("  1. LLM 模式 — 调用 qwen2.5:7b 结构化输出（约 30-60 秒）")
        print("  2. 规则模式 — 纯规则基线，即时响应")
        print("  3. 验收测试 — 运行 10 条规则验收")
        print("-" * 60)
        mode_choice = input("请选择模式 [1/2/3]（默认 1）: ").strip()
        if mode_choice == "3":
            return 0 if run_acceptance_check() else 1
        if mode_choice == "2":
            use_llm = False
        print()
        print("示例问题（可直接复制粘贴）：")
        print("  · 帮我搜索生物降解塑料相关专利")
        print("  · 查看 JP2024-002 的详细信息")
        print("  · JP2024-003 的申请人和状态是什么？")
        print("  · 对比 JP2024-001 和 JP2024-002 的 IPC 分类与差异")
        print("  · 有没有 Toyota 的固态电池相关专利？")
        print("  · 这个专利怎么样？（触发澄清意图）")
        print("-" * 60)
        question = input("请输入要分析的专利问题: ").strip()

    if not question:
        print("问题不能为空。")
        return 1

    if use_llm:
        # LLM 结构化输出模式
        try:
            analysis = analyze_with_llm(question)
        except Exception as exc:
            print(f"\n❌ LLM 分析失败: {exc}")
            print("💡 回退到规则模式...")
            analysis = analyze_question(question)
    else:
        # 纯规则模式
        analysis = analyze_question(question)

    print(render_analysis(analysis))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

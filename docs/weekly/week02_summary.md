# 第 2 周总结：Prompt 与结构化输出（D8-D14）

更新时间：2026-03-28

---

## 本周目标

> 输入自然语言问题 → 输出格式化 JSON，10 条输入稳定输出

## 每日产出回顾

| Day | 主题 | 产出 | 核心收获 |
|-----|------|------|----------|
| D8 | Prompt 基础 | `lecture08/prompt_templates.py` | 3 个模板（问答/抽取/改写）+ 变量元信息注册表 |
| D9 | 约束输出 | `lecture09/schema_v1.py` | 3 个 Pydantic Schema + create_agent + response_format |
| D10 | 失败样本 | `lecture10/failure_samples.json` + `validate_failures.py` | 5 条典型失败样本 + extra='forbid' 严格校验 |
| D11 | 重试策略 | `lecture11/retry_parser.py` + `retry_flow.mmd` | 二次解析修复流程，两轮内成功率 100% |
| D12 | Prompt A/B | `lecture12/ab_compare.py` | 短提示 vs 强约束：结构化场景强约束通过率 5/5 |
| D13 | 专利问题结构化 | `lecture13/cli_v1.py` | 完整 CLI（LLM 模式 + 规则 fallback），10 条稳定输出 |
| D14 | 周复盘 | `lecture14/prompt_strategies.json` + 本文 | 10 条 Prompt 策略 + L7/L8 迁移笔记 |

## 关键技术收获

### 1. Prompt 设计的三层约束模型

```
┌──────────────────────────────────────────────────┐
│  第 1 层：System Prompt（语义层）                  │
│  → 角色设定 + 行为边界 + 格式要求 + Few-shot 示例  │
├──────────────────────────────────────────────────┤
│  第 2 层：Pydantic Schema（结构层）                │
│  → response_format + Field(description)          │
│  → extra='forbid' + @field_validator             │
├──────────────────────────────────────────────────┤
│  第 3 层：后处理修复（兜底层）                      │
│  → normalize_date() + split_differences()        │
│  → repair_output() + retry prompt                │
└──────────────────────────────────────────────────┘
```

三层叠加后，7B 本地模型的结构化输出成功率从不稳定提升到 10/10 稳定通过。

### 2. 轻量 Schema + 后处理补全

这是本周最重要的架构洞察：

- **问题**：让 7B 模型一次性生成 23 字段 4 层嵌套的 JSON，耗时长且出错率高
- **方案**：拆分为 `LLMAnalysis`（7 个扁平字段）+ `enrich_to_full()` 后处理
- **效果**：LLM 只做语义理解（意图/实体/置信度），规则引擎处理确定性逻辑（工具参数/响应计划）

### 3. Prompt A/B 对比结论

| 维度 | 短提示 | 强约束提示 |
|------|--------|-----------|
| 通过率 | 1/5 (20%) | 5/5 (100%) |
| 响应速度 | 快 | 略慢 |
| 适用场景 | 低风险问答、头脑风暴 | 结构化输出、工具调用前置 |
| 维护成本 | 低 | 中 |

**结论**：凡是下游需要消费 JSON 的场景，一律用强约束提示。

### 4. 从 L7/L8 Notebook 迁移的 6 个模式

| 来源 | 模式 | 迁移状态 |
|------|------|---------|
| L7 | create_agent + response_format | ✅ D9 + D13 |
| L7 | extra='forbid' | ✅ D10 + D13 |
| L7 | @field_validator | ✅ D13 |
| L8 | 动态 Prompt（按意图选模板） | ✅ D13 PROMPT_PROFILES |
| L8 | 中间件（前/后处理） | ✅ D11 repair + D13 enrich |
| L8 | 变量注入 | ✅ D8 ChatPromptTemplate |

## 10 条 Prompt 策略总结

详见 `lectures/lecture14/prompt_strategies.json`，以下是精华版：

| # | 策略 | 一句话总结 |
|---|------|----------|
| S01 | 角色+边界优先 | system prompt 第一句定角色，第二段划边界 |
| S02 | Pydantic Schema 约束 | 用 response_format 绑定 BaseModel，不靠正则解析 |
| S03 | 枚举替代自由文本 | 分类字段用 StrEnum + @field_validator 做别名映射 |
| S04 | 二次解析+修复提示 | 校验失败不丢弃，把错误注入 retry prompt 再来一轮 |
| S05 | 轻量 Schema+后处理 | LLM 填核心字段，规则补全嵌套结构 |
| S06 | 强约束用于 JSON 场景 | 结构化输出用强约束，开放问答用短提示 |
| S07 | Few-shot 嵌入 | 1-3 个完整示例 > 10 条文字规则 |
| S08 | 日期/列表显式约束 | Prompt+Schema+Validator 三层同时约束格式 |
| S09 | LLM+规则双轨 | 默认 LLM，超时/出错自动回退规则引擎 |
| S10 | 模板变量注册表 | 每个变量有 description/type/required/example 元信息 |

## 里程碑达成

- [x] ✅ 输入问题 → 输出格式化 JSON
- [x] ✅ 10 条输入稳定输出（D13 `--check` 全部通过）
- [x] ✅ 每条策略有反例（prompt_strategies.json）

## 下周预告（W3：LangChain 工程化）

- 把 D13 的 `cli_v1.py` 迁移到可复用 LangChain 链路
- 学习 `langchain/L1-L5` notebook（Agent/Tools/Messages/Streaming/MCP）
- 补齐单测和异常处理层
- SK vs LangChain 对照 + LangGraph 预习

## 待改进

1. **置信度计算**：当前规则引擎的置信度逻辑较简单（有缺失=低，有关键词=中），后续考虑基于 LLM 的 logprobs 做更细粒度的评分
2. **Few-shot 示例动态选取**：当前 SYSTEM_PROMPT 的示例是静态的，后续考虑根据输入类型动态选取最相关的 Few-shot
3. **多语言支持**：当前只处理中文/日文专利号格式，后续需要支持 US/EP/WO 等格式的完整解析

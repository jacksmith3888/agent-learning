# Day02 学习笔记：最朴素的 ReAct Agent

> 参考: [HuggingFace Agents Course - Dummy Agent Library](https://huggingface.co/agents-course/notebooks/blob/main/unit1/dummy_agent_library.ipynb)

## 核心概念：为什么需要 Agent 循环？

LLM 本身只能生成文本，不能执行代码或调用外部工具。如果让 LLM 自由生成，它会**伪造工具调用结果**（幻觉）——假装自己查了天气，编造一个看似合理的答案。

Agent 的本质就是：**在 LLM 和真实工具之间架一座桥，用代码控制谁说话、谁执行。**

## 关键机制：`stop` 参数 —— "安全词"

```python
output = client.chat.completions.create(
    messages=messages,
    max_tokens=200,
    stop=["Observation:"],  # 安全词：截停 LLM 输出
)
```

- 系统提示词中约定了固定格式：`Thought → Action → Observation`
- LLM 按格式生成，当它写到 `Observation:` 准备编造结果时，`stop` 参数**强制截停**
- 这个词必须和提示词中的**精确匹配**（大小写敏感）
- 截停后，`response_text` 只包含 Thought 和 Action，不包含 `Observation:`

## 完整循环流程

```
用户提问: "What's the weather in London?"
        │
        ▼
┌─── 循环开始 (最多 max_steps 轮) ───┐
│                                      │
│  ① LLM 生成                         │
│     Thought: 我需要查天气             │
│     Action: {"action":"get_weather", │
│              "action_input":          │
│              {"location":"London"}}   │
│     Observation: ← 到这里被截停!      │
│                                      │
│  ② Python 代码介入                   │
│     extract_action() 提取 JSON       │
│     ↓                                │
│     TOOLS["get_weather"]("London")   │
│     ↓                                │
│     observation = "the weather in    │
│     London is sunny..."  ← 真实结果  │
│                                      │
│  ③ 拼接并送回                        │
│     messages.append({                │
│       "role": "assistant",           │
│       "content": response_text       │
│         + "Observation:\n"           │
│         + observation                │
│     })                               │
│     注意: "Observation:" 是我们手动   │
│     拼上去的，不是 LLM 生成的         │
│                                      │
│  ④ 带完整上下文再次调用 LLM           │
│     messages 包含所有历史消息          │
│     LLM 基于真实结果继续推理          │
│                                      │
│  ⑤ 判断是否结束                      │
│     - 输出包含 "Final Answer:" → 返回 │
│     - 还需要调工具 → 回到 ①          │
│                                      │
└──────────────────────────────────────┘
        │
        ▼
最终答案: "The weather in London is sunny with low temperatures."
```

## 关键细节

### `Observation` 的双重角色

| 位置 | 作用 |
|------|------|
| `stop=["Observation:"]` | 截停 LLM，防止它编造结果 |
| `"Observation:\n" + observation` (字符串拼接) | 我们手动加上，后面跟真实工具返回值 |

### 送回 LLM 是"继续对话"而非"重新生成"

每轮循环把拼接好的内容追加到 `messages` 列表，下次调用时带上**完整对话历史**：

```python
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "What's the weather?"},
    {"role": "assistant", "content": "Thought...Observation:\n真实结果"},  # 追加的
]
```

LLM 看到的是一段连续对话，基于所有上下文继续推理。

### 工具是普通 Python 函数

```python
def get_weather(location: str) -> str:
    return f"the weather in {location} is sunny with low temperatures.\n"

TOOLS = {"get_weather": get_weather}
```

这里用的是模拟数据，真实场景替换为 API 调用即可。Agent 框架不关心工具内部实现，只关心**函数名和返回值**。

## 总结

ReAct Agent 的最小实现只需要三个要素：

1. **提示词约定格式** — 定义 Thought/Action/Observation 的输出结构
2. **`stop` 参数截停** — 在 LLM 编造结果前刹车
3. **代码拼接真实结果** — 执行工具，把真实 observation 注入对话

这就是所有 Agent 框架（LangChain、LlamaIndex 等）的底层原理，只是它们把这个循环封装得更优雅。理解了这个朴素版本，再看框架就是"语法糖"而已。

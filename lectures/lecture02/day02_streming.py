"""
Day 02 - Streaming + Token 计数

学习目标：
  1. 理解流式输出（streaming）的原理：模型逐 chunk 返回生成内容，而非等全部生成完再返回
  2. 掌握 token 计数的两种方式：
     - 方式 A：累加 chunk 获取 usage_metadata（依赖模型/框架支持）
     - 方式 B：直接统计 chunk 数量（每个 chunk 通常对应 1 个 token）

Token 计数原理说明：
  ┌─────────────────────────────────────────────────────────────────┐
  │ LLM 生成文本时，并不是逐"字"生成，而是逐"token"生成。           │
  │                                                                 │
  │ 什么是 token？                                                  │
  │   - token 是模型处理文本的最小单位                              │
  │   - 英文中大约 1 个单词 ≈ 1-2 个 token                         │
  │   - 中文中大约 1 个汉字 ≈ 1-2 个 token（取决于分词器）         │
  │   - 例如 "你好世界" 可能被拆分为 ["你", "好", "世", "界"]       │
  │     也可能是 ["你好", "世界"]，具体取决于模型的 tokenizer        │
  │                                                                 │
  │ 流式输出时的 token 计数：                                       │
  │   - llm.stream() 每次 yield 一个 AIMessageChunk                 │
  │   - 每个 chunk.content 通常包含 1 个 token 对应的文本片段       │
  │   - 因此：chunk 的数量 ≈ 生成的 output token 数量               │
  │                                                                 │
  │ 更精确的方式：                                                  │
  │   - 将所有 chunk 累加（chunk1 + chunk2 + ...）得到完整消息       │
  │   - 完整消息的 usage_metadata 字段包含精确的 token 统计         │
  │   - 包括 input_tokens（输入）和 output_tokens（输出）           │
  │   - 注意：并非所有模型都在流式模式下提供 usage_metadata         │
  └─────────────────────────────────────────────────────────────────┘
"""

import time

from langchain_ollama import ChatOllama

# 初始化 Ollama 模型
llm = ChatOllama(model="qwen2.5:7b")

# ========== 流式输出 + Token 计数 ==========

# 记录开始时间，用于计算总耗时
start_time = time.time()

# chunk_count 用于统计流式输出的 chunk 数量
# 每个 chunk 通常对应模型生成的 1 个 token
chunk_count = 0

# aggregate 用于累加所有 chunk，最终可从中提取 usage_metadata
# 这是 LangChain 推荐的获取精确 token 统计的方式：
#   第一个 chunk 直接赋值，后续 chunk 通过 += 运算符合并
#   AIMessageChunk 重载了 __add__ 方法，会自动合并 content 和 metadata
aggregate = None

print("=" * 50)
print("🤖 正在生成回答（流式输出）...")
print("=" * 50)
print()

for chunk in llm.stream("解释一下 Transformer 架构"):
    # 逐 chunk 打印内容，实现"打字机"效果
    # end="" 不换行，flush=True 立即刷新缓冲区（否则可能攒一批才显示）
    print(chunk.content, end="", flush=True)

    # 累加 chunk：第一个直接赋值，后续用 += 合并
    # 合并后的 aggregate 会包含完整的 content 和 usage_metadata
    if aggregate is None:
        aggregate = chunk
    else:
        aggregate += chunk

    # 每个 chunk 计数 +1（近似等于 1 个 output token）
    chunk_count += 1

# 记录结束时间
end_time = time.time()
elapsed = end_time - start_time

# ========== 打印统计信息 ==========

print()  # 换行，与正文分隔
print()
print("=" * 50)
print("📊 Token 统计")
print("=" * 50)

# 方式 B：基于 chunk 数量的近似统计
# 原理：流式输出中，每个 chunk 通常包含 1 个 token 的文本
# 优点：简单可靠，所有模型都适用
# 缺点：只能统计 output token，无法得知 input token 数量
print(f"  📝 流式 chunk 数量（≈ output tokens）：{chunk_count}")

# 方式 A：从 usage_metadata 获取精确统计（如果模型支持）
# 原理：将所有 chunk 累加后，最终的 aggregate 可能包含 usage_metadata
# usage_metadata 是一个字典，包含：
#   - input_tokens: 输入（prompt）的 token 数量
#   - output_tokens: 输出（生成文本）的 token 数量
#   - total_tokens: 总 token 数量
if aggregate and aggregate.usage_metadata:
    usage = aggregate.usage_metadata
    print(f"  📥 输入 tokens（input_tokens）：{usage.get('input_tokens', 'N/A')}")
    print(f"  📤 输出 tokens（output_tokens）：{usage.get('output_tokens', 'N/A')}")
    print(f"  📊 总 tokens（total_tokens）：{usage.get('total_tokens', 'N/A')}")
else:
    # Ollama 在流式模式下可能不提供 usage_metadata
    # 这种情况下我们只能依赖 chunk 数量的近似值
    print("  ℹ️  该模型未在流式模式下提供 usage_metadata")
    print(f"  📤 近似 output tokens（基于 chunk 计数）：{chunk_count}")

print(f"  ⏱️  总耗时：{elapsed:.2f} 秒")

# 计算生成速度（tokens/秒），这是衡量推理性能的重要指标
if chunk_count > 0:
    tokens_per_sec = chunk_count / elapsed
    print(f"  🚀 生成速度：{tokens_per_sec:.1f} tokens/秒")

print("=" * 50)

# ========== 最终统计摘要（符合 D2 验收要求）==========
print()
print(f"共生成 {chunk_count} 个 token，耗时 {elapsed:.2f} 秒")

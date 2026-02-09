from langchain_ollama import ChatOllama

llm = ChatOllama(model="qwen2.5:7b")
print(llm.invoke("什么是 Agent?").content)

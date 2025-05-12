import llama_index
from llama_index.embeddings.dashscope import DashScopeEmbedding, DashScopeTextEmbeddingModels
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.llms.openai_like import OpenAILike
from dotenv import load_dotenv
import os

load_dotenv()

print ("开始解析文档....")
documents = SimpleDirectoryReader('/Users/barrywang/Documents/Yuzhuo_macBook_air/MCP_Dev/RAG_source').load_data()

print ("正在创建索引....")
index = VectorStoreIndex.from_documents(
    documents,
    embed_model=DashScopeEmbedding(
        model_name=DashScopeTextEmbeddingModels.TEXT_EMBEDDING_V2
    )
)

print ("正在配置提问引擎...")
query_engine = index.as_query_engine(
    streaming = True,
    llm=OpenAILike(
        model=os.getenv("QWEN_MODEL"),
        api_base=os.getenv("QWEN_BASE_URL"),
        api_key=os.getenv("QWEN_API_KEY"),
        is_chat_model=True
    )
)

print("正在生成回复...")
streaming_response = query_engine.query("帮我简单分析一下文档在描述什么信息？")

print ("最终答案：")
streaming_response.print_response_stream()

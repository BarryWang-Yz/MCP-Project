import llama_index
from llama_index.embeddings.dashscope import DashScopeEmbedding, DashScopeTextEmbeddingModels
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.llms.openai_like import OpenAILike
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.llms.dashscope import DashScope
from dotenv import load_dotenv
import os

load_dotenv()

def indexing (document_path="/Users/barrywang/Documents/Yuzhuo_macBook_air/MCP_Dev/RAG_source", persist_path="knowledge_base/test"):
    index = create_index(document_path)
    index.storage_context.persist(persist_path)


def create_index(document_path="/Users/barrywang/Documents/Yuzhuo_macBook_air/MCP_Dev/RAG_source"):
    documents = SimpleDirectoryReader(document_path).load_data()
    index = VectorStoreIndex.from_documents(
        documents,
        embed_model=DashScopeEmbedding(
            model_name=DashScopeTextEmbeddingModels.TEXT_EMBEDDING_V2,
            api_key=os.getenv("QWEN_API_KEY"),
            api_base=os.getenv("QWEN_BASE_URL")
        )
    )

    return index

def load_index(persist_path="knowledge_base/test"):
    storage_context = StorageContext.from_defaults(persist_dir=persist_path)
    return load_index_from_storage(
        storage_context, 
        embed_model=DashScopeTextEmbeddingModels.TEXT_EMBEDDING_V2,
    )

def create_query_engine(index):
    query_engine = index.as_query_engine(
        streaming=True,
        llm=OpenAILike(
            model=os.getenv("QWEN_MODEL"),
            is_chat_model=True
        )
    )

    return query_engine

def ask(question, query_engine):
    streaming_response = query_engine.query(question)
    streaming_response.print_response_stream()


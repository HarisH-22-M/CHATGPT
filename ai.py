from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
import streamlit as st



def ini_model():
    @st.cache_resource
    def initialize_model():
        llm = HuggingFaceEndpoint(
            repo_id="deepseek-ai/DeepSeek-V3.1",
            task="text-generation",
        )
        return ChatHuggingFace(llm=llm, temp=0.7)

    model = initialize_model()
    return model

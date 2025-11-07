from dotenv import load_dotenv
from pymongo import MongoClient
import os
import streamlit as st
from datetime import datetime
from langchain_core.messages import SystemMessage

def initialize_mongodb():
    load_dotenv()

    # MongoDB setup
    MONGODB_URI = os.getenv('MONGO_URI')
    if not MONGODB_URI:
        st.error("Please set up the MONGODB_URI in your .env file")
        st.stop()

    @st.cache_resource
    def init_mongodb():
        client = MongoClient(MONGODB_URI)
        db = client['chatbot_db']
        return db

    # Initialize MongoDB
    db = init_mongodb()
    return db

# Function to initialize session state
def init_session_state():
    if "chat_sessions" not in st.session_state:
        st.session_state.chat_sessions = []
    if "messages" not in st.session_state:
        st.session_state.messages = [SystemMessage(content="You are a helpful assistant")]
    if "session_id" not in st.session_state:
        st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        if st.session_state.session_id not in st.session_state.chat_sessions:
            st.session_state.chat_sessions.append(st.session_state.session_id)
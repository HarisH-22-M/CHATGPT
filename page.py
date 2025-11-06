import streamlit as st
from dotenv import load_dotenv
import os
from datetime import datetime
from pymongo import MongoClient
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Load environment variables
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

# Page config
st.set_page_config(
    page_title="DeepSeek Chat",
    page_icon="🤖",
    layout="wide"  # Changed to wide layout
)

# Function to get chat preview
def get_chat_preview(session_id):
    chat_collection = db['chat_history']
    first_message = chat_collection.find_one({"session_id": session_id}, sort=[("timestamp", 1)])
    return first_message['content'][:30] + "..." if first_message else "Empty chat"

# Function to load chat history
def load_chat_history(session_id):
    chat_collection = db['chat_history']
    return list(chat_collection.find({"session_id": session_id}).sort("timestamp", 1))

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

# Initialize session state
init_session_state()

# Function to reset chat state
def create_new_chat():
    new_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    if "chat_sessions" not in st.session_state:
        st.session_state.chat_sessions = []
    if new_session_id not in st.session_state.chat_sessions:
        st.session_state.chat_sessions.append(new_session_id)
    st.session_state.session_id = new_session_id
    st.session_state.messages = [SystemMessage(content="You are a helpful assistant")]

# Sidebar for chat history
with st.sidebar:
    st.title("💭 Chat History")
    
    # New Chat button
    if st.button("🆕 New Chat", key="new_chat"):
        create_new_chat()
        st.rerun()

    # Display chat history
    st.write("Previous Chats:")
    chat_collection = db['chat_history']
    unique_sessions = chat_collection.distinct("session_id")
    
    # Update session list
    for session in unique_sessions:
        if session not in st.session_state.chat_sessions:
            st.session_state.chat_sessions.append(session)
    
    # Display chat sessions
    for session in reversed(st.session_state.chat_sessions):  # Show newest first
        if st.button(f"📝 {datetime.strptime(session, '%Y%m%d_%H%M%S').strftime('%Y-%m-%d %H:%M')}\n{get_chat_preview(session)}", key=session):
            st.session_state.session_id = session
            # Load messages for the selected session
            stored_messages = load_chat_history(session)
            st.session_state.messages = [SystemMessage(content="You are a helpful assistant")]
            for msg in stored_messages:
                if msg['role'] == 'user':
                    st.session_state.messages.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    st.session_state.messages.append(AIMessage(content=msg['content']))
            st.rerun()

# Load messages for current session
if "messages" not in st.session_state:
    # Try to load previous messages from MongoDB
    stored_messages = load_chat_history(st.session_state.session_id)
    
    if stored_messages:
        st.session_state.messages = [SystemMessage(content="You are a helpful assistant")]
        for msg in stored_messages:
            if msg['role'] == 'user':
                st.session_state.messages.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'assistant':
                st.session_state.messages.append(AIMessage(content=msg['content']))
    else:
        st.session_state.messages = [SystemMessage(content="You are a helpful assistant")]

# Initialize the model
@st.cache_resource
def initialize_model():
    llm = HuggingFaceEndpoint(
        repo_id="deepseek-ai/DeepSeek-V3.1",
        task="text-generation",
    )
    return ChatHuggingFace(llm=llm, temp=0.7)

model = initialize_model()

# Main chat area
main_col = st.container()

with main_col:
    # Main title
    st.title("💬 DeepSeek Chat Assistant")
    st.markdown("Chat with the DeepSeek-V3.1 AI model!")
    
    # Current chat info
    st.caption(f"Current Chat: {datetime.strptime(st.session_state.session_id, '%Y%m%d_%H%M%S').strftime('%Y-%m-%d %H:%M')}")
    
    # Display chat messages
    chat_placeholder = st.container()
    with chat_placeholder:
        for message in st.session_state.messages:
            if isinstance(message, SystemMessage):
                continue
            elif isinstance(message, HumanMessage):
                with st.chat_message("user"):
                    st.write(message.content)
            elif isinstance(message, AIMessage):
                with st.chat_message("assistant"):
                    st.write(message.content)

# Chat input
if prompt := st.chat_input("What would you like to know?"):
    # Store user message in MongoDB
    chat_collection = db['chat_history']
    chat_collection.insert_one({
        "session_id": st.session_state.session_id,
        "role": "user",
        "content": prompt,
        "timestamp": datetime.now()
    })
    
    # Add user message to session state
    st.session_state.messages.append(HumanMessage(content=prompt))
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Generate and display AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = model.invoke(st.session_state.messages)
            st.write(response.content)
    
    # Store AI response in MongoDB
    chat_collection.insert_one({
        "session_id": st.session_state.session_id,
        "role": "assistant",
        "content": response.content,
        "timestamp": datetime.now()
    })
    
    # Add AI response to session state
    st.session_state.messages.append(AIMessage(content=response.content))

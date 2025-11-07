from datetime import datetime
import streamlit as st
from langchain_core.messages import SystemMessage
from initialization import initialize_mongodb

# Get MongoDB instance
db = initialize_mongodb()

def get_next_collection_number():
    """Get the next available collection number"""
    collections = db.list_collection_names()
    chat_collections = [col for col in collections if col.startswith('chat_history_')]
    if not chat_collections:
        return 1
    numbers = [int(col.split('_')[-1]) for col in chat_collections]
    return max(numbers) + 1

def get_or_create_collection():
    """Get current chat collection or create new one"""
    if 'current_collection' not in st.session_state:
        # Initialize with the next available collection number
        st.session_state.current_collection = f'chat_history_{get_next_collection_number()}'
    return db[st.session_state.current_collection]

# Function to find collection for session
def find_collection_for_session(session_id):
    """Find which collection contains the given session"""
    collections = [col for col in db.list_collection_names() if col.startswith('chat_history_')]
    for collection_name in collections:
        collection = db[collection_name]
        if collection.find_one({"session_id": session_id}):
            return collection_name
    return None

# Function to get chat preview
def get_chat_preview(session_id):
    collection_name = find_collection_for_session(session_id)
    if collection_name:
        collection = db[collection_name]
        first_message = collection.find_one({"session_id": session_id}, sort=[("timestamp", 1)])
        if first_message:
            return first_message['content'][:30] + "..."
    return "Empty chat"

# Function to load chat history
def load_chat_history(session_id):
    collection_name = find_collection_for_session(session_id)
    if collection_name:
        # Set the current collection to the one containing this session
        st.session_state.current_collection = collection_name
        collection = db[collection_name]
        return list(collection.find({"session_id": session_id}).sort("timestamp", 1))
    return []

# Function to reset chat state
def create_new_chat():
    new_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    if "chat_sessions" not in st.session_state:
        st.session_state.chat_sessions = []
    if new_session_id not in st.session_state.chat_sessions:
        st.session_state.chat_sessions.append(new_session_id)
    
    # Create new collection for the new chat
    st.session_state.current_collection = f'chat_history_{get_next_collection_number()}'
    
    st.session_state.session_id = new_session_id
    st.session_state.messages = [SystemMessage(content="You are a helpful assistant")]

# Function to save message
def save_message(role, content, session_id):
    # If this is an existing session, find its collection
    collection_name = find_collection_for_session(session_id)
    if collection_name:
        st.session_state.current_collection = collection_name
    
    collection = get_or_create_collection()
    message_data = {
        "session_id": session_id,
        "role": role,
        "content": content,
        "timestamp": datetime.now()
    }
    collection.insert_one(message_data)
import streamlit as st
from chat_fn import get_chat_preview, load_chat_history, create_new_chat, save_message, db
from datetime import datetime
from ai import ini_model
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from initialization import init_session_state

# Page config
st.set_page_config(
    page_title="DeepSeek Chat",
    page_icon="🤖",
    layout="wide"  # Changed to wide layout
)

# Initialize session state
init_session_state()

# Sidebar for chat history
with st.sidebar:
    st.title("💭 Chat History")
    
    # New Chat button
    if st.button("🆕 New Chat", key="new_chat"):
        create_new_chat()
        st.rerun()

    # Display chat history
    st.write("Previous Chats:")
    # Get all chat sessions from all collections
    all_sessions = set()
    collections = [col for col in db.list_collection_names() if col.startswith('chat_history_')]
    for collection_name in collections:
        collection = db[collection_name]
        collection_sessions = collection.distinct("session_id")
        all_sessions.update(collection_sessions)
    
    # Update session list
    for session in all_sessions:
        if session not in st.session_state.chat_sessions:
            st.session_state.chat_sessions.append(session)
    
    # Display chat sessions
    for session in reversed(sorted(st.session_state.chat_sessions)):  # Show newest first
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
model = ini_model()

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
    # Save user message
    save_message("user", prompt, st.session_state.session_id)
    
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
    
    # Save AI response
    save_message("assistant", response.content, st.session_state.session_id)
    
    # Add AI response to session state
    st.session_state.messages.append(AIMessage(content=response.content))

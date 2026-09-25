import streamlit as st
from agents.orchestrator import AgentOrchestrator

st.set_page_config(page_title="FinReq AI - Agentic Requirements Engineering", layout="wide")

st.title("🏦 FinReq AI: Automated Financial SDLC Architect")
st.markdown("""
**Specialized Domain: Digital Banking & Payment Systems**
This AI-powered dashboard acts as a professional requirements engineer for the **Digital Banking** sector.
Input your project idea, and the multi-agent system will architect a complete, regulatorily-compliant SDLC and a detailed SRS.
""")


# Initialize Orchestrator in session state
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = AgentOrchestrator()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Chat Interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Enter your financial project idea (e.g., 'A blockchain-based cross-border payment system for SMEs')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🤖 Agents are collaborating..."):
            try:
                # Run the multi-agent pipeline
                result = st.session_state.orchestrator.process_request(prompt)

                full_response = f"### ✅ Project Analysis Complete\n\n"
                full_response += f"#### 📋 Classified Requirements\n{result['requirements']}\n\n"
                full_response += f"#### ⚖️ Compliance & Risk Analysis\n{result['compliance']}\n\n"
                full_response += f"#### 🚀 Recommended SDLC Model\n{result['sdlc']}\n\n"
                full_response += f"#### 📄 Full SRS & Implementation Plan\n{result['srs_plan']}"

                st.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"An error occurred: {e}")

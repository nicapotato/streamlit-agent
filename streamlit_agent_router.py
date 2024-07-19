import streamlit as st

from streamlit_agent.mrkl_demo import mrkl_demo

def streamlit_agents_demo():
    if st.sidebar.button('Reset Chat History'):
        st.session_state.messages = []
        st.rerun()

    analysis_names_to_funcs = {
        # "None": None,
        # "basic_memory": basic_memory,
        # "basic_streaming": basic_streaming,
        # # "chat_pandas_df": chat_pandas_df,
        # "chat_with_document": chat_with_document,
        # "chat_with_sql": chat_with_sql,
        # "minimal_agent": minimal_agent,
        "mrkl_demo": mrkl_demo,
        # "search_and_chat": search_and_chat,
        # "simple_feedback": simple_feedback,
    }

    if "ai_langchain_router" not in st.session_state:
        # set the initial default value of the slider widget
        st.session_state['ai_langchain_router'] = list(
            analysis_names_to_funcs.keys())[0]

    selected_page = st.sidebar.selectbox("LangChain Demos", analysis_names_to_funcs.keys(),
                                         key=st.session_state['ai_langchain_router'])
    if selected_page == "None":
        ai_llm_landing()
        st.info("#### Select Bot in Sidebar to Proceed")
    else:
        st.markdown(f"## {selected_page}")
        analysis_names_to_funcs[selected_page]()

streamlit_agents_demo()
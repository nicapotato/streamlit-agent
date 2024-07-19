from pathlib import Path

import streamlit as st
import os

from langchain import hub
from langchain.agents import AgentExecutor, Tool, create_react_agent
from langchain.chains import LLMMathChain
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper, SQLDatabase
from langchain_core.runnables import RunnableConfig
from langchain_experimental.sql import SQLDatabaseChain
from langchain_openai import OpenAI
from sqlalchemy import create_engine
import sqlite3

from streamlit_agent.callbacks.capturing_callback_handler import playback_callbacks
from streamlit_agent.clear_results import with_clear_container

DB_PATH = (Path(__file__).parent / "Chinook.db").absolute()

SAVED_SESSIONS = {
    "Who is Leo DiCaprio's girlfriend? What is her current age raised to the 0.43 power?": "leo.pickle",
    "What is the full name of the female artist who recently released an album called "
    "'The Storm Before the Calm' and are they in the FooBar database? If so, what albums of theirs "
    "are in the FooBar database?": "alanis.pickle",
}

def mrkl_demo():

    "# 🦜🔗 MRKL"

    # Setup credentials in Streamlit
    user_openai_api_key = st.secrets['chat-gpt']['openai-personal-key']

    if user_openai_api_key:
        openai_api_key = user_openai_api_key
        enable_custom = True
    else:
        openai_api_key = "not_supplied"
        enable_custom = False

    # Tools setup
    llm = OpenAI(temperature=0, openai_api_key=openai_api_key, streaming=True)
    search = DuckDuckGoSearchAPIWrapper()
    llm_math_chain = LLMMathChain.from_llm(llm)

    # Make the DB connection read-only to reduce risk of injection attacks
    # See: https://python.langchain.com/docs/security
    creator = lambda: sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    db = SQLDatabase(create_engine("sqlite:///", creator=creator))

    db_chain = SQLDatabaseChain.from_llm(llm, db)
    tools = [
        Tool(
            name="Search",
            func=search.run,
            description="useful for when you need to answer questions about current events. You should ask targeted questions",
        ),
        Tool(
            name="Calculator",
            func=llm_math_chain.run,
            description="useful for when you need to answer questions about math",
        ),
        Tool(
            name="FooBar DB",
            func=db_chain.run,
            description="useful for when you need to answer questions about FooBar. Input should be in the form of a question containing full context",
        ),
    ]

    # Initialize agent
    react_agent = create_react_agent(llm, tools, hub.pull("hwchase17/react"))
    mrkl = AgentExecutor(agent=react_agent, tools=tools)

    with st.form(key="form"):
        if not enable_custom:
            "Ask one of the sample questions, or enter your API Key in the sidebar to ask your own custom questions."
        prefilled = st.selectbox("Sample questions", sorted(SAVED_SESSIONS.keys())) or ""
        user_input = ""

        if enable_custom:
            user_input = st.text_input("Or, ask your own question")
        if not user_input:
            user_input = prefilled
        submit_clicked = st.form_submit_button("Submit Question")

    output_container = st.empty()
    if with_clear_container(submit_clicked):
        output_container = output_container.container()
        output_container.chat_message("user").write(user_input)

        answer_container = output_container.chat_message("assistant", avatar="🦜")
        st_callback = StreamlitCallbackHandler(answer_container)
        cfg = RunnableConfig()
        cfg["callbacks"] = [st_callback]

        # If we've saved this question, play it back instead of actually running LangChain
        # (so that we don't exhaust our API calls unnecessarily)
        if user_input in SAVED_SESSIONS:
            session_name = SAVED_SESSIONS[user_input]
            session_path = Path(__file__).parent / "runs" / session_name
            print(f"Playing saved session: {session_path}")
            answer = playback_callbacks([st_callback], str(session_path), max_pause_time=2)
        else:
            answer = mrkl.invoke({"input": user_input}, cfg)

        answer_container.write(answer["output"])

mrkl_demo()
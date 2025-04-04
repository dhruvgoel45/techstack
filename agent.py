from langchain.agents import create_openai_tools_agent
from langchain.agents.agent import AgentExecutor
from langchain_core.prompts import (
    ChatPromptTemplate,
    PromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import ChatMessageHistory
from sqlalchemy import create_engine, text
from langchain_core.tools import StructuredTool
import prompts as p
from sql import sql_tool

# Database connection
DATABASE_URL = "postgresql://technographics_dataset_user:6ygabdgGyylCn0v8WNXn42kBQLQptFHm@dpg-cvnmb0je5dus738lc100-a/technographics_dataset"
engine = create_engine(DATABASE_URL)

# LLM setup
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key="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"
)

tools = [StructuredTool.from_function(func=sql_tool, handle_tool_error=True)]
llm.bind_tools(tools)

system_prompt = PromptTemplate.from_template(
    "".join(
        [
            p.get_agent_description_prompt(),
            p.get_tools_prompt(tools),
            p.get_sql_tool_rules_prompt(),
        ]
    )
)

prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate(prompt=system_prompt),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("ai", "{agent_scratchpad}"),
    ]
)

# Custom history handler for PostgreSQL
class PostgresChatHistory:
    def __init__(self, session_id):
        self.session_id = session_id

    def get_history(self):
        # Create a ChatMessageHistory object to hold the messages
        chat_history = ChatMessageHistory()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT message_type, message_content
                    FROM chat_history
                    WHERE session_id = :session_id
                    ORDER BY sequence ASC
                """),
                {"session_id": self.session_id}
            ).fetchall()
            
            for row in result:
                if row[0] == "human":
                    chat_history.add_message(HumanMessage(content=row[1]))
                elif row[0] == "ai":
                    chat_history.add_message(AIMessage(content=row[1]))
            return chat_history

    def add_message(self, message_type, content):
        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO chat_history (session_id, message_type, message_content)
                    VALUES (:session_id, :message_type, :message_content)
                """),
                {"session_id": self.session_id, "message_type": message_type, "message_content": content}
            )
            conn.commit()

# Agent setup
react_agent = create_openai_tools_agent(llm=llm, prompt=prompt, tools=tools)
agent_executor = AgentExecutor(
    agent=react_agent,
    tools=tools,
    max_iterations=3,
    verbose=True,
    handle_parsing_errors=True,
    return_intermediate_steps=True,
)

agent = RunnableWithMessageHistory(
    agent_executor,
    lambda session_id: PostgresChatHistory(session_id).get_history(),
    input_messages_key="input",
    history_messages_key="chat_history",
)
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
DATABASE_URL = "postgresql://technographics_dataset_user:6ygabdgGyylCn0v8WNXn42kBQLQptFHm@dpg-cvnmb0je5dus738lc100-a.oregon-postgres.render.com/technographics_dataset"
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

# In agent.py
class PostgresChatHistory:
    def __init__(self, session_id):
        self.session_id = session_id
        self._ensure_session_exists()  # New method to initialize session

    def _ensure_session_exists(self):
        """Ensure the session exists in session_details with a default title if new."""
        with engine.connect() as conn:
            # Check if session exists
            result = conn.execute(
                text("SELECT title FROM session_details WHERE session_id = :session_id"),
                {"session_id": self.session_id}
            ).fetchone()
            if not result:
                # Insert with a temporary title if no messages exist yet
                conn.execute(
                    text("""
                        INSERT INTO session_details (session_id, title)
                        VALUES (:session_id, :title)
                        ON CONFLICT (session_id) DO NOTHING
                    """),
                    {"session_id": self.session_id, "title": "New Session"}
                )
                conn.commit()

    def get_history(self):
        # ... (unchanged)
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
            # Insert the message into chat_history
            conn.execute(
                text("""
                    INSERT INTO chat_history (session_id, message_type, message_content)
                    VALUES (:session_id, :message_type, :message_content)
                """),
                {"session_id": self.session_id, "message_type": message_type, "message_content": content}
            )
            # If this is the first human message, update the title in session_details
            if message_type == "human":
                first_message = conn.execute(
                    text("""
                        SELECT COUNT(*) FROM chat_history 
                        WHERE session_id = :session_id AND message_type = 'human'
                    """),
                    {"session_id": self.session_id}
                ).scalar()
                if first_message == 1:  # This is the first human message
                    conn.execute(
                        text("""
                            UPDATE session_details 
                            SET title = :title 
                            WHERE session_id = :session_id
                        """),
                        {"session_id": self.session_id, "title": content}
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
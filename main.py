from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from agent import agent, PostgresChatHistory
from langchain_community.utilities import SQLDatabase


DATABASE_URL = "postgresql://technographics_dataset_user:6ygabdgGyylCn0v8WNXn42kBQLQptFHm@dpg-cvnmb0je5dus738lc100-a.oregon-postgres.render.com/technographics_dataset"
engine = create_engine(DATABASE_URL)
db = SQLDatabase.from_uri(DATABASE_URL)


class GenerationRequest(BaseModel):
    user_query: str
    session_id: str

app = FastAPI()

@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

@app.post("/generate")
async def generate(gen_req: GenerationRequest):
    # Initialize history for this session
    history = PostgresChatHistory(gen_req.session_id)
    
    # Store the user query in the database
    history.add_message("human", gen_req.user_query)
    
    # Invoke the agent with the session history
    response = agent.invoke(
        {"input": gen_req.user_query},
        {"configurable": {"session_id": gen_req.session_id}},
    )
    
    # Store the AI response in the database
    raw_output = response["output"]
    history.add_message("ai", raw_output)
    
    # Fetch the session title
    with engine.connect() as conn:
        title = conn.execute(
            text("SELECT title FROM session_details WHERE session_id = :session_id"),
            {"session_id": gen_req.session_id}
        ).scalar() or "New Session"
    # Parse technologies (if applicable)
    technologies = []
    lines = raw_output.split("\n")
    for line in lines:
        if line.startswith("- "):
            technologies.append(line[2:].strip())  # Remove "- " prefix

    # Return structured JSON response
    return {
        "query": gen_req.user_query,
        "session_id": gen_req.session_id,
        "title": title,  # Add title to response
        "technologies": technologies,
        "response": raw_output
    }
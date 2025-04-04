from fastapi import FastAPI
from pydantic import BaseModel
from agent import agent, PostgresChatHistory

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
        "technologies": technologies,
        "response": raw_output
    }
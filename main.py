from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents.orchestrator import AgentOrchestrator
import uvicorn

app = FastAPI()

# Allow the frontend to talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = AgentOrchestrator()

class ProjectRequest(BaseModel):
    prompt: str

@app.post("/analyze")
async def analyze_project(request: ProjectRequest):
    try:
        # We call the async process_request_async directly since this route is async
        result = await orchestrator.process_request_async(request.prompt)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        print(f"Detailed Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

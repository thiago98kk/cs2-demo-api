from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="CS2 Demo Parser API")


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "cs2-demo-parser"
    }


@app.get("/health")
def health():
    return {
        "ok": True
    }


class ParseRequest(BaseModel):
    demo_id: str
    project_id: str | None = None
    file_url: str
    team_name: str | None = None
    map: str | None = None


@app.post("/parse-demo")
def parse_demo(request: ParseRequest):
    return {
        "success": True,
        "demo_id": request.demo_id,
        "message": "Parser API connected successfully"
    }

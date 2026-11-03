"""Camada HTTP FastAPI para o chatbot já existente em main.py."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Music Store Agent API", version="1.0.0")


class ChatRequest(BaseModel):
	question: str = Field(min_length=1)
	session_id: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
	return {"status": "ok"}


@app.post("/chat")
def chat(request: ChatRequest) -> dict[str, str]:
	"""Encaminha a pergunta à implementação existente, sem duplicar sua lógica."""
	try:
		from main import chat as existing_chat

		result = existing_chat(
			{"question": request.question, "session_id": request.session_id}
		)
	except Exception as exc:
		raise HTTPException(status_code=503, detail=str(exc)) from exc

	if request.session_id and "session_id" not in result:
		result["session_id"] = request.session_id
	return result


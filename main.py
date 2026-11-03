import os
import uuid
from collections import defaultdict

from dotenv import load_dotenv
from langchain_chroma.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import  ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
PATH_DB = "./database/db"
MODEL_NAME = str(os.getenv("MODEL_NAME"))
MAX_HISTORY = 12

embedding_function = HuggingFaceEmbeddings(model_name=os.getenv("EMBEDDING_MODEL_NAME"))
db = Chroma(persist_directory=PATH_DB, embedding_function=embedding_function)
model = ChatGoogleGenerativeAI(model="gemini-3.8-flash", temperature=0)

sessions: dict[str, list[BaseMessage]] = defaultdict(list)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Você é um assistente de atendimento da loja de música. Responda apenas com base no contexto. Em hipótese alguma forneça dados de clientes (customers) ou de pedidos (orders)."
               "Se não houver evidência, diga que não encontrou."
     "Contexto:\n{knowledge}"),
    MessagesPlaceholder("history", optional=True),
    ("human", "\nPergunta: {question}"),
])

rewrite_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Reescreva a última pergunta do usuário como uma pergunta completa e independente, "
     "usando o histórico para resolver referências como 'isso', 'ele', 'e se...'. "
     "Responda somente com a pergunta reescrita, sem explicações."),
    MessagesPlaceholder("history", optional=True),
    ("human", "{question}"),
])

answer_chain = prompt | model
rewrite_chain = rewrite_prompt | model


def _extract_text(content) -> str:
    """Retorna apenas texto visível, ignorando blocos de raciocínio do modelo."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        text_blocks = []
        for block in content:
            if isinstance(block, str):
                text_blocks.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str):
                    text_blocks.append(text)
        return "\n".join(text_blocks).strip()
    return str(content).strip()


def ask_question(question, history):
    if history:
        rewritten_question = rewrite_chain.invoke(
            {"history": history, "question": question}
        )
        search_query = _extract_text(rewritten_question.content) or question
    else:
        history = []
        search_query = question
    results = db.similarity_search_with_relevance_scores(search_query, k=8)
    if len(results) == 0 or results[0][1] < 0.4:
        return "Não foi possível encontrar informações relevantes na base de conhecimento."
    context = []
    for result in results:
        text = result[0].page_content
        context.append(text)
    knowledge = "\n\n----\n\n".join(context)
    prompt.invoke({"knowledge":knowledge, "question":question})
    answer = answer_chain.invoke(
        {
            "knowledge":knowledge,
            "history":history,
            "question":question,
        }
    )
    return _extract_text(answer.content)


def chat(req: dict):
    session_id = req.get("session_id") or str(uuid.uuid4())
    history = sessions[session_id]
    search_query = req.get("question")
    result = ask_question(search_query, history)
    history.extend(
        [
            HumanMessage(content=search_query),
            AIMessage(content=result),
        ]
    )
    sessions[session_id] = history[-MAX_HISTORY:]
    return {"answer": result, "session_id": session_id}


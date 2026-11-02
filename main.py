import os
import uuid
from collections import defaultdict

from dotenv import load_dotenv
from langchain_chroma.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import  ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
PATH_DB = "./database/db"
MODEL_NAME = str(os.getenv("MODEL_NAME"))
MAX_HISTORY = 6

embedding_function = HuggingFaceEmbeddings(model_name=os.getenv("EMBEDDING_MODEL_NAME"))
db = Chroma(persist_directory=PATH_DB, embedding_function=embedding_function)
model = ChatGoogleGenerativeAI(model="gemma-4-31b-it", temperature=0)

sessions: dict[str, list] = defaultdict(list)

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

def ask_question(question, history):
    if history:
        search_query = rewrite_chain.invoke({"history":history, "question":question}).content.strip()
    else:
        history = []
        search_query = question
    results = db.similarity_search_with_relevance_scores(search_query, k=4)
    print(results[0])
    print(results[0][1])
    if len(results) == 0 or results[0][1] < 0.3:
        print("Não foi possível encontrar informações relevantes na base de conhecimento.")
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
    ).content
    return answer


def chat(req: dict):
    first_message = False if req.get("session_id") else True
    session_id = req.get("session_id") or str(uuid.uuid4())
    history = sessions[session_id]
    search_query = req.get("question")
    if first_message:
        return {"answer": ask_question(search_query, history), "session_id": session_id}
    else:
        return {"answer": ask_question(search_query, [])}


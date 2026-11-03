# Music Store Agent

Estrutura base para disponibilizar o chatbot existente por uma API FastAPI. A lógica atual permanece em `main.py` e a criação do índice continua em `database/create_db.py`.

## Preparação

Use Python 3.10 ou superior, crie/ative um ambiente virtual e instale as dependências:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copie `.env.example` para `.env` e preencha as variáveis necessárias, especialmente `GOOGLE_API_KEY`.

## Criar o índice e iniciar a API

Na raiz do projeto:

```powershell
python build_index.py
uvicorn api:app --reload
```

Documentação interativa: `http://127.0.0.1:8000/docs`. Verificação: `GET /health`.

Envie perguntas para `POST /chat` como JSON:

```json
{
	"question": "Quais produtos estão disponíveis?"
}
```

Para continuar uma sessão, inclua o `session_id` devolvido na resposta da primeira pergunta enviada.

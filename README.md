# Music Store Agent

Assistente de perguntas e respostas sobre o catálogo e as políticas da loja. A aplicação expõe uma API HTTP com FastAPI, busca contexto em um índice vetorial Chroma e usa um modelo Google Gemini para responder.

## Requisitos

- Python 3.10 ou superior.
- Chave de API do Google AI Studio com acesso ao modelo configurado.
- Acesso à internet para baixar dependências e o modelo de embeddings Hugging Face.

## Instalação e configuração

Execute os comandos na raiz do repositório, onde ficam `api.py` e `requirements.txt`:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Se o PowerShell bloquear a ativação do ambiente, pode chamar diretamente os executáveis em `.venv\Scripts\`, ou ajustar a política apenas para o processo atual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1
```

Crie o arquivo local `.env` a partir do exemplo e configure as credenciais e modelos:

```powershell
Copy-Item .env.example .env
```

Edite `.env`:

```dotenv
GOOGLE_API_KEY=sua_chave_do_google_ai_studio
MODEL_NAME=gemma-4-31b-it
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

`main.py` instancia atualmente o modelo de chat `gemini-3.8-flash` diretamente no código; nesse estado, `MODEL_NAME` do `.env` não altera o modelo usado pela API. Para trocar o provedor ou modelo, atualize essa configuração no código e verifique a compatibilidade com sua chave. A variável `EMBEDDING_MODEL_NAME` é usada tanto ao construir o índice quanto ao consultá-lo: mantenha o mesmo modelo nas duas etapas, pois vetores com dimensões diferentes não são compatíveis.

## Construir o índice e executar a API

O índice é criado a partir dos CSVs e PDFs presentes em `data/`. Gere ou atualize os vetores antes da primeira execução:

```powershell
python build_index.py
```

O índice Chroma persistido fica em `database/db`. Depois, inicie o servidor de desenvolvimento:

```powershell
uvicorn api:app --reload
```

URLs locais:

- Saúde da API: <http://127.0.0.1:8000/health>

## API de chat

Faça uma requisição `POST /chat` com JSON:

```json
{
  "question": "Qual é o endereço da loja?"
}
```

No Swagger em `/docs`, é possível testar o endpoint sem ferramenta adicional. A resposta contém `answer` e `session_id`. Envie o mesmo `session_id` nas perguntas subsequentes para usar o histórico da sessão. As sessões ficam na memória do processo: são perdidas ao reiniciar a API e não são compartilhadas entre múltiplas instâncias.

No campo session_id utilize o uuid contido na resposta da primeira mensagem enviada ao agente.

```json
{
  "question": "Qual é o preço de outros instrumentos dessa categoria?",
  "session_id": "uuid_da_session" 
}
```

## Decisões técnicas

- **FastAPI:** framework Python com validação dos dados de entrada via Pydantic e documentação OpenAPI/Swagger automática, adequado para disponibilizar rapidamente endpoints de chat.
- **Google Gemini:** modelo generativo acessado pelo LangChain Google GenAI; responde com base nos trechos recuperados. A integração via LangChain mantém prompts e chamadas de modelo organizados.
- **Embeddings Hugging Face e Chroma:** documentos são convertidos em vetores pelo modelo `sentence-transformers/all-MiniLM-L6-v2` e armazenados localmente no Chroma. Isso permite busca semântica sem exigir um serviço externo dedicado de banco vetorial.
- **Retrieval aumentado (RAG):** PDFs são extraídos por página; CSVs são transformados em texto por linha; o texto é normalizado, dividido em trechos de até 2.000 caracteres com sobreposição de 1.000, vetorizado e persistido. Para cada pergunta, a aplicação recupera até oito trechos e só prossegue quando a maior relevância é pelo menos `0.4`.
- **Estratégia de prompt:** as instruções limitam a resposta ao contexto recuperado, orientam o assistente a declarar quando faltarem evidências e proíbem revelar dados de clientes ou pedidos. Em perguntas de continuação, um prompt separado reescreve a pergunta usando as mensagens da sessão para melhorar a busca.
- **Privacidade dos dados:** os CSVs de clientes, pedidos e itens de pedidos não estão presentes em `data/` e não devem ser incluídos na base vetorial. Use apenas dados necessários e autorizados para responder às perguntas.

## Limitações conhecidas e próximos passos

- O histórico é armazenado em memória, sem expiração ou persistência; reiniciar o processo perde as conversas. Com mais tempo, usaria Redis ou um banco com TTL, além de limites por sessão.
- A busca usa apenas similaridade vetorial e um limite fixo. Perguntas factuais curtas — como endereço, telefone ou CEP — podem não recuperar o trecho ideal. Eu avaliaria busca híbrida, filtros por metadados e ajuste do `k`/limiar com um conjunto de perguntas de teste.
- A extração do PDF depende do texto disponível no arquivo e pode falhar com documentos escaneados ou tabelas complexas. OCR e testes de qualidade dos documentos seriam melhorias.
- A chamada ao modelo é síncrona no fluxo da requisição; latência de rede e do provedor afeta o tempo de resposta. Também faltam timeout, retentativas controladas, rate limiting e métricas detalhadas por etapa.
- Não há suíte automatizada de testes ou avaliação sistemática de qualidade do retrieval e das respostas. Eu adicionaria testes de API, casos de regressão para perguntas frequentes e avaliação de precisão/recall dos trechos recuperados.
- O índice é local e precisa ser reconstruído quando os dados ou o modelo de embeddings mudam. Trocar o modelo exige recriar todos os vetores para manter dimensões compatíveis.
- Não foram utilizados os dados de pedidos e de clientes pois não devem ficar expostos para o modelo.

## Uso de assistentes de código

Foi utilizado o **GitHub Copilot no VS Code** como assistente de código. Ele apoiou a exploração da estrutura do projeto, a elaboração e revisão de alterações e a análise de erros. As sugestões foram verificadas contra os arquivos e o comportamento da aplicação; decisões, testes e validação final continuam sob responsabilidade do autor do projeto.

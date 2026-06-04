# DeclaraAI

Assistente inteligente para organização de documentos e apoio à declaração do Imposto de Renda Pessoa Física no Brasil. O projeto é um Micro SaaS acadêmico com Agentic RAG, LLM aberto executado localmente e uma base de conhecimento própria sobre IRPF.

## Problema e Público-Alvo

A declaração do IRPF exige documentos corretos, classificação adequada de despesas e atenção a limites legais. Contribuintes leigos costumam perder deduções válidas, guardar documentos incompletos ou lançar despesas que não são aceitas pela Receita Federal.

O DeclaraAI atende pessoas físicas brasileiras que precisam organizar recibos, notas fiscais, informes de rendimentos e comprovantes ao longo do ano. O sistema não substitui contador, mas ajuda a reduzir erros antes da entrega ou revisão profissional.

## Funcionalidades

| Área | Funcionalidade |
|---|---|
| Chat RAG | Responde perguntas sobre IRPF com base nos documentos indexados |
| Upload | Processa PDF, TXT, HTML, XML, JPG e PNG |
| Classificação | Classifica documentos por categoria tributária com LLM-first e fallback por regras |
| Justificativa | Gera explicação fundamentada com RAG após a classificação |
| Titularidade | Verifica se o beneficiário é titular, dependente provável ou terceiro |
| Histórico | Salva documentos revisados e permite consulta por categoria |
| Base de conhecimento | Lista, adiciona e remove documentos de referência |
| Avaliação | Mede recuperação, cobertura de palavras-chave e comparação de modelos |

## Arquitetura

```text
Usuário
  |
Frontend React + Vite
  |
API FastAPI
  |
  +-- Chat RAG
  |     +-- Retriever semântico
  |     +-- ChromaDB
  |     +-- Re-ranking com CrossEncoder
  |     +-- Ollama com LLM aberto
  |
  +-- Upload de documentos
  |     +-- Extração por tipo de arquivo
  |     +-- Classificação LLM-first
  |     +-- Fallback por regras
  |     +-- Justificativa enriquecida por RAG
  |
  +-- Histórico e resumo anual
        +-- SQLite
```

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.11, FastAPI, Pydantic, SQLAlchemy |
| Frontend | React, Vite, Nginx, Lucide React |
| LLM | Ollama com `mistral` por padrão |
| Embeddings | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| Recuperação | ChromaDB com similaridade cosseno |
| Re-ranking | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` |
| Documentos | PyMuPDF, pdfplumber, BeautifulSoup, OCR com Tesseract |
| Avaliação | Scripts próprios, RAGAS opcional e CSVs em `data/eval/` |

## Base de Conhecimento

| Arquivo | Tipo | Relevância |
|---|---|---|
| `data/knowledge_base/guia_imposto_renda.txt` | TXT | Regras resumidas de obrigatoriedade, deduções e documentos |
| `data/knowledge_base/pr-irpf-2024.pdf` | PDF | Perguntas e respostas oficiais da Receita Federal |

Esses documentos foram escolhidos por cobrirem dúvidas recorrentes sobre saúde, educação, previdência privada, rendimentos, dependentes, aluguéis, prazos e penalidades. A base também pode ser expandida pela interface em `Base de Conhecimento`.

## Pipeline RAG

1. O carregador lê documentos da base e arquivos enviados pelo usuário.
2. O texto é limpo, normalizado e enriquecido com metadados.
3. O chunker divide o conteúdo em trechos de 600 caracteres com 80 caracteres de sobreposição.
4. O gerador de embeddings cria vetores semânticos.
5. O ChromaDB armazena chunks, fontes e metadados.
6. O recuperador busca candidatos e aplica re-ranking.
7. O LLM gera resposta usando apenas o contexto recuperado.
8. A resposta apresenta fontes e indica ausência de informação quando a base não sustenta a pergunta.

## Comportamento Agentic RAG

O agente escolhe ferramentas conforme a intenção do usuário:

| Ferramenta | Quando é usada |
|---|---|
| `busca_vetorial` | Perguntas abertas sobre regras do IRPF |
| `busca_documento_usuario` | Perguntas sobre documentos enviados |
| `classificar_documento` | Upload de um novo documento |
| `verificar_titularidade` | Checagem de titular ou dependente |
| `gerar_justificativa` | Explicação fundamentada após classificação |
| `consulta_banco_dados` | Histórico, resumo anual e totais por categoria |

O workflow completo está em [docs/roadmap_agentic/workflow.md](docs/roadmap_agentic/workflow.md).

## Decisões Técnicas

| Decisão | Justificativa |
|---|---|
| Mistral via Ollama | Modelo aberto, execução local, bom equilíbrio entre qualidade e custo |
| Embedding multilíngue MiniLM | Leve, compatível com português e adequado para CPU |
| ChromaDB | Persistência simples para protótipo local |
| SQLite | Banco relacional sem configuração externa |
| Chunking 600/80 | Preserva contexto fiscal sem gerar trechos longos demais |
| Re-ranking CrossEncoder | Melhora a ordem dos trechos em perguntas complexas |
| LLM-first na classificação | Reduz rigidez das regras e mantém fallback seguro |

## Execução com Docker

```bash
docker compose up -d --build
docker exec -it declaraai-ollama ollama pull mistral
```

Serviços:

| Serviço | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API FastAPI | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| Ollama | http://localhost:11434 |

## Execução Local

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Dependências de desenvolvimento, testes e avaliação:

```bash
cd ..
pip install -r requirements-dev.txt
make test
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Ollama:

```bash
ollama serve
ollama pull mistral
```

## Makefile

```bash
make up-build        # constrói e sobe a stack
make down            # para os contêineres
make modelo          # baixa o modelo Mistral
make ingest          # re-indexa a base de conhecimento
make status          # consulta métricas do RAG
make check           # verifica formatação do backend
make test            # executa testes Python
```

## API Principal

| Método | Endpoint | Uso |
|---|---|---|
| `POST` | `/chat` | Envia pergunta ao assistente |
| `POST` | `/ingest` | Re-indexa a base de conhecimento |
| `GET` | `/status` | Consulta status do pipeline |
| `POST` | `/documents/upload` | Processa documento fiscal |
| `POST` | `/documents/save` | Salva documento no histórico |
| `GET` | `/history` | Lista documentos salvos |
| `GET` | `/knowledge/files` | Lista arquivos da base |
| `POST` | `/knowledge/upload` | Adiciona documento à base |
| `POST` | `/evaluation/recuperacao` | Avalia recuperação no dataset anotado |
| `POST` | `/evaluation/recuperacao-pergunta` | Avalia uma pergunta isolada |

Exemplo:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"pergunta": "Quais despesas médicas posso deduzir no IR?"}'
```

## Avaliação

O projeto possui `data/eval/perguntas.json` com 60 perguntas anotadas por categoria, resposta de referência, palavras-chave esperadas e dificuldade. Os scripts salvam resultados em CSV para comparação final.

```bash
python scripts/avaliar_llm.py --limite 10
python scripts/avaliar_llm.py --no-rag --limite 10
python scripts/avaliar_chunking.py --config fixo_600_80 --limite 10
python scripts/avaliar_ragas.py --modelo mistral --limite 10
```

Saídas esperadas:

| Arquivo | Conteúdo |
|---|---|
| `data/eval/resultados_llm.csv` | Comparação entre modelos e ablation study |
| `data/eval/resultados_chunking.csv` | Comparação de estratégias de chunking |
| `data/eval/resultados_ragas.csv` | Métricas RAGAS |

## Documentação

| Caminho | Conteúdo |
|---|---|
| `docs/roadmap_artigo/roadmap_consolidado.md` | Plano unificado para artigo acadêmico |
| `docs/roadmap_agentic/workflow.md` | Workflow Agentic RAG do DeclaraAI |
| `docs/reports/relatorio_declaraai.tex` | Relatório técnico em LaTeX |
| `docs/diagrams/` | Diagramas de arquitetura, RAG e classificação |

## Privacidade e LGPD

O DeclaraAI foi desenhado para execução local. O LLM roda no Ollama, os vetores ficam no ChromaDB local e o histórico usa SQLite no próprio ambiente do usuário. Esse desenho reduz exposição de dados sensíveis como CPF, renda, saúde, dependentes e documentos fiscais.

## Limitações

| Limitação | Mitigação |
|---|---|
| Não substitui contador | A interface mantém o sistema como apoio informativo |
| Depende do Ollama | O status da interface informa disponibilidade |
| OCR pode falhar em imagens ruins | Usuário revisa dados antes de salvar |
| Regras fiscais mudam anualmente | Base pode ser atualizada pela interface |
| Estratégias avançadas de chunking ainda são experimentais | Scripts registram configurações e resultados |

## Estrutura do Projeto

```text
backend/                 API FastAPI, serviços e pipeline RAG
frontend/                Interface React + Vite
data/knowledge_base/     Base de conhecimento do IRPF
data/eval/               Dataset e resultados de avaliação
data/test_documents/     Documentos fictícios para simulação
docs/                    Diagramas, roadmaps e relatórios
scripts/                 Avaliação de LLMs, chunking e RAGAS
```

## Equipe

| Nome | Matrícula |
|---|---|
| Juliana Ballin Lima | 2315310011 |
| Fernando Luiz Da Silva Freire | 2315310007 |

Projeto acadêmico da Universidade do Estado do Amazonas, disciplina Oficina e Desenvolvimento de Sistemas I.

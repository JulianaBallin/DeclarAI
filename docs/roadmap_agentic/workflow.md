# Workflow Agentic RAG do DeclarAI

Este documento descreve como o DeclarAI atende à abordagem Agentic RAG solicitada na atividade. O domínio é a declaração do Imposto de Renda Pessoa Física no Brasil, com foco em organização de documentos, deduções, titularidade e consulta a regras fiscais.

## 1. Objetivo do Agente

O agente ajuda o usuário a:

- Tirar dúvidas sobre regras do IRPF com base em documentos indexados.
- Processar recibos, notas fiscais, informes e comprovantes.
- Classificar documentos em categorias tributárias.
- Explicar se um gasto é dedutível, potencialmente dedutível ou não dedutível.
- Alertar quando não houver informação suficiente na base de conhecimento.
- Apoiar a organização anual dos documentos salvos.

## 2. Base de Conhecimento

| Arquivo | Tipo | Uso |
|---|---|---|
| `guia_imposto_renda.txt` | TXT | Regras resumidas sobre obrigatoriedade, deduções e documentos |
| `pr-irpf-2024.pdf` | PDF | Perguntas e respostas oficiais da Receita Federal |

A base foi escolhida por reunir conteúdo diretamente relacionado ao IRPF e por apoiar respostas em fontes verificáveis. O usuário também pode incluir novos documentos pela página Base de Conhecimento.

## 3. Ingestão e Pré-processamento

```text
Arquivo
  |
Loader
  |
Extração de texto por tipo
  |
Limpeza e normalização
  |
Metadados fiscais
  |
Chunking
  |
Embeddings
  |
ChromaDB
```

Formatos suportados:

| Formato | Estratégia |
|---|---|
| PDF | PyMuPDF e pdfplumber |
| TXT | Leitura direta em UTF-8 |
| HTML | BeautifulSoup |
| XML | Parser específico para notas fiscais |
| JPG e PNG | OCR com Tesseract |

## 4. Chunking

Configuração padrão:

| Parâmetro | Valor | Justificativa |
|---|---:|---|
| `CHUNK_SIZE` | 600 caracteres | Mantém contexto fiscal suficiente sem trechos longos demais |
| `CHUNK_OVERLAP` | 80 caracteres | Preserva frases cortadas e valores monetários |

A API também permite re-indexação experimental por `POST /knowledge/reindex`, usada pelos scripts de avaliação de chunking.

## 5. Ferramentas do Agente

| Ferramenta | Quando usar | Implementação |
|---|---|---|
| Busca vetorial | Perguntas abertas sobre IRPF | `backend/app/rag/retriever.py` |
| Busca em documento do usuário | Perguntas sobre arquivos salvos | ChromaDB com metadados de fonte |
| Classificação de documento | Após upload | `ServicoClassificaçãoLLM` com fallback |
| Verificação de titularidade | Antes de concluir dedutibilidade | `titularidade_service.py` |
| Justificativa enriquecida | Após classificar documento | `justificativa_service.py` |
| Consulta ao histórico | Resumos e documentos salvos | `history_service.py` e SQLite |
| Avaliação | Comparação de recuperação e respostas | `evaluation_service.py` |

## 6. Fluxo do Chat

```text
Usuário faz pergunta
  |
Pergunta simples de saudação?
  |-- sim: resposta local
  |
Busca vetorial no ChromaDB
  |
Re-ranking dos trechos
  |
Contexto suficiente?
  |-- não: informar ausência de suporte na base
  |
Geração com LLM local
  |
Resposta com fontes consultadas
```

## 7. Fluxo de Upload

```text
Usuário envia arquivo
  |
Validação de formato
  |
Extração de texto e metadados
  |
Classificação LLM-first
  |
Fallback por regras, se necessário
  |
Verificação de validade fiscal e dedutibilidade
  |
Justificativa com RAG
  |
Usuário revisa os dados
  |
Salvar no histórico e indexar no ChromaDB
```

## 8. Regras de Geração

O prompt do gerador exige que o modelo:

- Responda sempre em português brasileiro.
- Use apenas o contexto recuperado.
- Declare quando a resposta não estiver na base.
- Não invente valores, datas, alíquotas ou limites.
- Trate negações fiscais como prioridade.
- Oriente consulta profissional apenas como complemento.

## 9. Modelo Aberto

O modelo padrão é `mistral` via Ollama. A escolha foi feita por equilibrar qualidade, custo computacional e execução local. Os scripts aceitam comparação com `llama3.2:3b`, `phi4-mini`, `gemma3:4b` e `qwen2.5:7b`.

## 10. Interface

A interface é uma aplicação React + Vite com páginas para:

- Chat RAG.
- Upload de documentos.
- Base de conhecimento.
- Histórico.
- Avaliação.
- Status do sistema.

## 11. Avaliação

O sistema usa `data/eval/perguntas.json` com 60 perguntas anotadas. As rotas e scripts calculam:

- Taxa de recuperação.
- Score médio de contexto.
- Cobertura de palavras-chave.
- Casos sem contexto.
- Comparação entre modelos.
- Ablation study sem RAG.
- Métricas RAGAS opcionais.

Resultados são salvos em `data/eval/resultados_*.csv`, permitindo comparação final no relatório e no artigo.

## 12. Limitações Operacionais

- A qualidade depende do modelo Ollama instalado.
- A base precisa ser atualizada quando regras fiscais mudarem.
- OCR pode falhar em imagens ruins.
- O sistema apoia a organização e explicação, mas não substitui contador.

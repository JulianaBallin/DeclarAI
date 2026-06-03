# Roadmap Consolidado — DeclaraAI: Artigo Academico

Versao unificada do roadmap original (v1) e do roadmap expandido (v2).
Itens marcados com **Novo** nao existiam no roadmap original.

## Status geral

| Item | Status |
|------|--------|
| Pipeline RAG funcional | Concluido |
| Classificacao LLM-first com fallback por regras | Concluido |
| Singleton ServicoRAG com warmup | Concluido |
| Dataset de avaliacao (perguntas.json) | Pendente |
| RAGAS instalado e configurado (Novo) | Pendente |
| Experimentos de chunking (5 estrategias) | Pendente |
| Experimentos de retrieval hibrido (Novo) | Pendente |
| Experimentos com LLMs + ablation study | Pendente |
| Comparacao de modelos de embedding (Novo) | Pendente |
| Dataset anotado para classificacao | Pendente |
| Notebooks de graficos | Pendente |
| Frontend React (Vite + shadcn/ui) | Pendente |
| Secao Privacidade/LGPD no artigo (Novo) | Pendente |
| Artigo no Overleaf | Pendente |

---

## 1. Experimentos de Chunking

**Por que entra no artigo:** A segmentacao do texto afeta diretamente a qualidade das respostas.
A literatura de 2025 exige comparacao entre familias diferentes de chunking, nao apenas variacoes
de tamanho dentro de uma mesma familia.

### 1.1 Estrategias a testar

| Estrategia | Descricao | Status |
|------------|-----------|--------|
| Fixo por tokens | Baseline: chunk_size 200/400/600/800, overlap 0/40/80/120 | Existe |
| Por sentenca (Novo) | Split em limites semanticos naturais (NLTK/spaCy) | A criar |
| Semantico (Novo) | Split por mudanca de embedding (SemanticChunker) | A criar |
| Contextual Retrieval (Novo) | Adiciona resumo de contexto a cada chunk antes de indexar | A criar |
| Late chunking (Novo) | Embed documento inteiro, segmentar depois | A criar |

Referencia: Bennani et al., arXiv 2601.14123 (2025)

### 1.2 Metricas de avaliacao

- **Faithfulness** (RAGAS): a resposta esta apoiada no contexto?
- **Answer Relevancy** (RAGAS): a resposta enderedaca a pergunta?
- **Context Precision** (RAGAS): chunks relevantes chegam no topo?
- **Context Recall** (RAGAS): tudo necessario foi recuperado?
- **Precisao@K**: dos K chunks, quantos sao relevantes?
- **MRR (Mean Reciprocal Rank)**: posicao do primeiro chunk relevante
- **Tempo de indexacao e busca**

### 1.3 Arquivos

- [ ] `data/eval/perguntas.json` -- 50-80 perguntas IRPF com respostas de referencia
- [ ] `scripts/avaliar_chunking.py` -- itera as 5 estrategias e salva metricas RAGAS
- [ ] `data/eval/resultados_chunking.csv` -- saida dos experimentos
- [ ] `notebooks/01_experimentos_chunking.ipynb` -- heatmaps e graficos

---

## 2. Experimentos de Estrategia de Recuperacao (Novo)

**Por que entra no artigo:** Documentos de IRPF tem terminologia exata (NF-e, DARF, CNPJ).
Busca hibrida BM25 + vetorial supera busca vetorial pura em documentos fiscais.
Referencia: arXiv 2604.01733 (2025) -- Recall@5 de 0.816 vs 0.587 com busca vetorial pura.

### 2.1 Configuracoes a comparar

| Configuracao | Implementacao |
|--------------|---------------|
| Vetorial puro | ChromaDB atual (baseline) |
| BM25 puro | `rank_bm25` library |
| Hibrido RRF | ChromaDB + BM25 + Reciprocal Rank Fusion |
| Hibrido + Reranking | Hibrido + cross-encoder ms-marco-MiniLM-L-6-v2 |

### 2.2 Arquivos

- [ ] `backend/app/rag/retrieval/hybrid_retriever.py`
- [ ] `backend/app/rag/retrieval/reranker.py`
- [ ] `scripts/avaliar_retrieval.py`
- [ ] `data/eval/resultados_retrieval.csv`
- [ ] `notebooks/01b_retrieval_strategies.ipynb`

---

## 3. Experimentos com Diferentes LLMs (com ablation study)

**Por que entra no artigo:** Sem ablation study (vanilla LLM vs RAG), o artigo nao prova
que o pipeline de recuperacao agrega valor. Revisores vao exigir essa comparacao.

### 3.1 Modelos

| Modelo | Tamanho | Notas |
|--------|---------|-------|
| Vanilla LLM sem RAG (Novo) | -- | Baseline obrigatorio -- ablation study |
| `mistral` | 4.1 GB | Baseline RAG atual |
| `llama3.2:3b` | 2.0 GB | Rapido, leve |
| `phi4-mini` | 2.5 GB | Excelente em saida estruturada |
| `gemma3:4b` | 3.3 GB | Forte em raciocinio |
| `qwen2.5:7b` | 4.7 GB | Melhor suporte multilingual e portugues |

### 3.2 Metricas

- 4 scores RAGAS: faithfulness, answer relevancy, context precision, context recall
- Taxa de alucinacao: % de respostas onde Faithfulness < 0.5
- Latencia: TTFT e tempo total de geracao
- Curva de Pareto: tamanho do modelo vs score de qualidade

### 3.3 Arquivos

- [ ] `scripts/avaliar_llm.py` -- modo `no_rag=True` para ablation study
- [ ] `data/eval/resultados_llm.csv`
- [ ] `notebooks/02_comparacao_llm.ipynb`

---

## 4. Comparacao de Modelos de Embedding (Novo)

**Por que entra no artigo:** O modelo de embedding pode ser o gargalo de qualidade do RAG.
Modelos treinados em ingles podem ter dificuldade com terminologia fiscal em portugues.
Referencia: Amiri e Bocklitz, arXiv 2506.17277 (2025)

### 4.1 Modelos a testar

| Modelo | Dimensoes | Como usar |
|--------|-----------|-----------|
| `all-MiniLM-L6-v2` | 384 | sentence-transformers (baseline provavel) |
| `nomic-embed-text` | 768 | `ollama pull nomic-embed-text` |
| `multilingual-e5-large` | 1024 | sentence-transformers (treinado em multiplos idiomas) |

### 4.2 Arquivos

- [ ] `scripts/avaliar_embeddings.py`
- [ ] `data/eval/resultados_embeddings.csv`

---

## 5. Migracao da Classificacao: LLM-first (concluido)

A arquitetura atual ja implementa LLM-first com fallback por regras.
O campo `origem` registra se a classificacao veio do LLM ou do fallback.

### 5.1 Dataset anotado (pendente)

Para reportar a comparacao com dados concretos no artigo:
- 50-100 documentos por categoria com anotacao manual
- Campos: `tipo_documento`, `categoria_irpf`, `dedutivel`
- Incluir casos dificeis: documentos ambiguos, OCR ruim

### 5.2 Arquivos

- [ ] `data/eval/documentos_anotados.json`
- [ ] `scripts/avaliar_classificacao.py`
- [ ] `notebooks/03_classificacao_documentos.ipynb`

---

## 6. Avaliacao com RAGAS (Novo)

**Por que entra no artigo:** Padrao da industria para avaliacao RAG de ponta a ponta.
Publicado em 2023 (Es et al.), apresentado no EACL 2024.
Pode usar Ollama local como juiz -- sem custo de API.

### 6.1 Configuracao

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from langchain_community.llms import Ollama

llm_judge = Ollama(model="mistral")

results = evaluate(
    dataset=eval_dataset,
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    llm=llm_judge,
)
```

### 6.2 Arquivos

- [ ] `scripts/avaliar_ragas.py`
- [ ] `data/eval/resultados_ragas.csv`
- [ ] `requirements-dev.txt` -- adicionar `ragas`, `deepeval`

---

## 7. Notebooks de Graficos

- [ ] `notebooks/01_experimentos_chunking.ipynb` -- heatmap estrategia x RAGAS scores
- [ ] `notebooks/01b_retrieval_strategies.ipynb` (Novo) -- barras vetorial vs BM25 vs Hibrido
- [ ] `notebooks/02_comparacao_llm.ipynb` -- Pareto tamanho vs qualidade
- [ ] `notebooks/03_classificacao_documentos.ipynb` -- matriz de confusao, F1 por classe
- [ ] `notebooks/04_visao_geral_sistema.ipynb` -- diagrama do pipeline, distribuicao de chunks

---

## 8. Frontend React (Vite + shadcn/ui)

Substituir o Streamlit por um frontend React mais profissional.

### 8.1 Paginas a implementar

- [ ] Chat RAG: input + historico + indicador de fontes
- [ ] Upload: drag-and-drop, progresso, resultado da classificacao
- [ ] Base de Conhecimento: listar/remover arquivos indexados
- [ ] Historico: documentos salvos com filtros por categoria
- [ ] Status do sistema: modelo carregado, chunks indexados, Ollama disponivel

---

## 9. Secao de Privacidade / LGPD (Novo)

**Por que entra no artigo:** Documentos de IRPF contem dados sensiveis (CPF, renda, saude).
O DeclaraAI resolve por arquitetura: tudo roda localmente, nenhum dado sai da maquina.
Posicionar como "privacy-by-design RAG" e um diferencial publicavel.

### 9.1 Conteudo para o artigo

- Subsecao "Consideracoes de Privacidade e LGPD" na secao de Arquitetura
- Dados fiscais sao dados sensiveis conforme LGPD Art. 5, II
- Tabela: Cloud LLM vs Local LLM (custo, latencia, privacidade, dependencia)
- Argumento: Ollama + ChromaDB local = zero data leaving the machine

---

## 10. Artigo no Overleaf

### 10.1 Estrutura (8-10 paginas, SBC ou IEEE)

- [ ] Resumo / Abstract
- [ ] 1. Introducao: problema do contribuinte leigo, IRPF brasileiro
- [ ] 2. Trabalhos Relacionados: RAG, assistentes fiscais, benchmarks de chunking
- [ ] 3. Arquitetura do Sistema: pipeline, componentes, execucao local (LGPD)
- [ ] 4. Metodologia de Avaliacao: dataset, metricas RAGAS, modelos comparados
- [ ] 5. Experimentos e Resultados
  - 5.1 Ablation study: RAG vs Vanilla LLM
  - 5.2 Impacto da estrategia de chunking (5 familias)
  - 5.3 Comparacao de estrategias de recuperacao (busca hibrida + reranking)
  - 5.4 Comparacao de LLMs e modelos de embedding
  - 5.5 Classificacao: regras vs LLM-first
- [ ] 6. Interface e Usabilidade
- [ ] 7. Conclusao e Trabalhos Futuros
- [ ] Referencias

### 10.2 Referencias-chave

| Referencia | Por que citar |
|------------|---------------|
| Lewis et al. (2020) -- RAG original | Fundacao teorica do paradigma |
| Es et al. (2023) -- RAGAS, EACL 2024 | Framework de avaliacao usado |
| Bennani et al. (2025) -- arXiv 2601.14123 | Justifica comparacao sistematica de chunking |
| arXiv 2604.01733 (2025) | Justifica busca hibrida em documentos financeiros |
| Amiri e Bocklitz (2025) -- arXiv 2506.17277 | Justifica comparacao de embedding models |
| Singh et al. (2024) -- ChunkRAG arXiv 2410.19572 | LLM-driven chunk filtering |

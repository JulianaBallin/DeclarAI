# Roadmap Consolidado do Artigo DeclaraAI

Este roadmap unifica os planejamentos anteriores do artigo e organiza as próximas etapas de pesquisa, avaliação e escrita. As versões antigas foram removidas para manter uma única fonte de planejamento.

## Status Geral

| Item | Status | Observação |
|---|---|---|
| Pipeline RAG funcional | Concluído | FastAPI, ChromaDB, embeddings, re-ranking e Ollama |
| Classificação LLM-first | Concluído | Fallback por regras mantido |
| Frontend React | Concluído | Chat, upload, base, histórico, avaliação e status |
| Dataset de avaliação | Concluído | `data/eval/perguntas.json` com 60 perguntas |
| Scripts de avaliação | Concluído | LLMs, chunking e RAGAS |
| Workflow Agentic RAG | Concluído | `docs/roadmap_agentic/workflow.md` |
| Relatório técnico | Concluído | `docs/reports/relatorio_declaraai.tex` |
| Busca híbrida BM25 + vetorial | Futuro | Boa contribuição para artigo |
| Comparação de embeddings | Futuro | Avaliar MiniLM, E5 e nomic |
| Dataset anotado de documentos | Futuro | Necessário para medir classificação |
| Notebooks de gráficos | Futuro | Úteis para visualização final |
| Artigo em formato SBC ou IEEE | Futuro | Depende dos resultados experimentais |

## 1. Objetivo do Artigo

Demonstrar que um Micro SaaS com Agentic RAG pode apoiar contribuintes brasileiros na organização de documentos e na consulta a regras do IRPF, preservando privacidade por execução local.

Contribuições previstas:

- Pipeline RAG especializado em documentos fiscais brasileiros.
- Classificação de documentos com LLM-first e fallback por regras.
- Justificativa enriquecida por RAG após upload.
- Interface web profissional para uso externo ao grupo.
- Avaliação com dataset anotado, ablation study e métricas inspiradas no RAGAS.
- Discussão de privacidade e LGPD em um sistema local.

## 2. Experimentos de Chunking

Objetivo: medir como o tamanho e a sobreposição dos chunks afetam a recuperação.

| Estratégia | Status | Arquivo |
|---|---|---|
| Fixo 200/0 | Disponível via API experimental | `scripts/avaliar_chunking.py` |
| Fixo 400/40 | Disponível via API experimental | `scripts/avaliar_chunking.py` |
| Fixo 600/80 | Baseline do sistema | `backend/app/rag/chunker.py` |
| Fixo 800/120 | Disponível via API experimental | `scripts/avaliar_chunking.py` |
| Fixo 1000/200 | Disponível via API experimental | `scripts/avaliar_chunking.py` |
| Por sentença | Futuro | Implementar split dedicado |
| Semântico | Futuro | Implementar split por mudança de embedding |

Métricas:

- Taxa de recuperação.
- Score médio de contexto.
- Cobertura de palavras-chave.
- Latência média.

## 3. Comparação de LLMs

Objetivo: comparar custo, latência e qualidade entre modelos abertos executados via Ollama.

| Modelo | Perfil |
|---|---|
| `mistral` | Baseline atual |
| `llama3.2:3b` | Modelo leve |
| `phi4-mini` | Saída estruturada e baixo custo |
| `gemma3:4b` | Raciocínio em modelo compacto |
| `qwen2.5:7b` | Bom suporte multilíngue |
| `vanilla_sem_rag` | Baseline sem recuperação |

Arquivo principal: `scripts/avaliar_llm.py`.

## 4. Ablation Study

Comparação necessária para provar que o RAG agrega valor:

| Condição | Como executar |
|---|---|
| LLM com RAG | `python scripts/avaliar_llm.py --modelo mistral` |
| LLM sem RAG | `python scripts/avaliar_llm.py --modelo mistral --no-rag` |

Métricas:

- Cobertura de palavras-chave.
- Latência.
- Chunks recuperados.
- Casos sem suporte documental.

## 5. RAGAS

Objetivo: avaliar respostas de ponta a ponta com métricas aceitas pela comunidade RAG.

Métricas planejadas:

- Faithfulness.
- Answer relevancy.
- Context precision.
- Context recall.

Arquivo principal: `scripts/avaliar_ragas.py`.

## 6. Busca Híbrida

Objetivo futuro: combinar busca vetorial e busca por palavras-chave, pois documentos fiscais têm termos exatos como NF-e, NFS-e, DARF, CPF, CNPJ e carnê-leão.

Implementações planejadas:

- BM25 puro com `rank_bm25`.
- Fusão por Reciprocal Rank Fusion.
- Re-ranking final com CrossEncoder.
- Script `scripts/avaliar_retrieval.py`.

## 7. Comparação de Embeddings

Objetivo futuro: medir se o modelo de embedding atual é o gargalo da recuperação.

| Modelo | Motivo |
|---|---|
| `paraphrase-multilingual-MiniLM-L12-v2` | Baseline atual |
| `multilingual-e5-large` | Melhor cobertura multilíngue |
| `nomic-embed-text` | Alternativa local via Ollama |

## 8. Classificação de Documentos

O sistema já usa LLM-first com fallback por regras. Para artigo, ainda falta um dataset anotado de documentos.

Dataset futuro:

- 50 a 100 documentos por categoria.
- Rótulos de tipo, categoria, dedutibilidade e validade fiscal.
- Casos com OCR ruim, documentos ambíguos e recibos sem nota fiscal.

Métricas:

- Acurácia.
- Precisão, recall e F1 por categoria.
- Taxa de fallback.
- Matriz de confusão.

## 9. Notebooks

Notebooks recomendados:

| Notebook | Objetivo |
|---|---|
| `01_experimentos_chunking.ipynb` | Gráficos de chunking |
| `01b_retrieval_strategies.ipynb` | Busca vetorial, BM25 e híbrida |
| `02_comparacao_llm.ipynb` | Modelos, latência e ablation study |
| `03_classificacao_documentos.ipynb` | Classificação e matriz de confusão |
| `04_visao_geral_sistema.ipynb` | Arquitetura, dados e métricas gerais |

## 10. Privacidade e LGPD

Seção obrigatória do artigo:

- Dados de IRPF podem conter CPF, renda, informações de saúde e dados de dependentes.
- O DeclaraAI executa LLM localmente via Ollama.
- Vetores ficam no ChromaDB local.
- Histórico fica em SQLite local.
- Nenhum documento precisa ser enviado a APIs externas.

## 11. Estrutura Sugerida do Artigo

1. Resumo.
2. Introdução.
3. Trabalhos relacionados.
4. Arquitetura do sistema.
5. Metodologia de avaliação.
6. Experimentos e resultados.
7. Interface e usabilidade.
8. Privacidade e LGPD.
9. Limitações.
10. Conclusão e trabalhos futuros.

## 12. Referências Recomendadas

| Referência | Uso no artigo |
|---|---|
| Lewis et al. (2020) | Fundamento do RAG |
| Es et al. (2023), RAGAS | Avaliação de RAG |
| Bennani et al. (2025) | Comparação de chunking |
| Singh et al. (2024), ChunkRAG | Filtragem e chunking orientados por LLM |
| Amiri e Bocklitz (2025) | Comparação de embeddings |

## 13. Ordem de Execução Recomendada

1. Rodar avaliação de recuperação com o dataset completo.
2. Rodar comparação de LLMs com limite inicial de 10 perguntas.
3. Rodar ablation study sem RAG.
4. Executar avaliação de chunking com o baseline 600/80.
5. Gerar CSVs finais.
6. Criar notebooks de gráficos.
7. Atualizar relatório técnico.
8. Redigir artigo final em formato definido pelo professor.

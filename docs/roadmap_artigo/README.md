# Roadmap do Artigo Academico — DeclaraAI

Esta pasta reune os documentos de planejamento do artigo academico do projeto DeclaraAI.

## Arquivos

| Arquivo | Descricao |
|---------|-----------|
| [roadmap_v1.md](roadmap_v1.md) | Roadmap original — experimentos de chunking, LLMs, classificacao e frontend |
| [roadmap_v2.md](roadmap_v2.md) | Roadmap expandido com RAGAS, busca hibrida, ablation study e privacidade/LGPD |
| [roadmap_consolidado.md](roadmap_consolidado.md) | Versao unificada com todos os itens priorizados por ordem de execucao |

## Ordem de execucao recomendada

```
1.  Dataset de avaliacao (data/eval/perguntas.json)
2.  Instalar RAGAS e configurar com Ollama local
3.  Ablation study: vanilla LLM vs RAG
4.  Experimentos de chunking (5 estrategias) + notebook 01
5.  Experimentos de retrieval (hibrido + reranking) + notebook 01b
6.  Comparacao de LLMs (5 modelos) + notebook 02
7.  Comparacao de modelos de embedding
8.  LLM classificador + dataset anotado + notebook 03
9.  Notebook 04 (visao geral do sistema)
10. Frontend React (Vite + shadcn/ui)
11. Secao Privacidade/LGPD no artigo
12. Redigir artigo no Overleaf com figuras prontas
```

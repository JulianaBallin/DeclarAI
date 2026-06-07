# Prompt para Notebook LLM - Slides DeclaraAI: Agentic RAG

Use este conteúdo como prompt para gerar uma apresentação profissional sobre o DeclaraAI. A apresentação deve priorizar as melhorias implementadas desde a última entrega na branch `main`, destacando a evolução atual da branch `develop`.

## Direção Visual

- Todos os slides devem ter fundo off-white, preferencialmente `#FAF9F6`.
- Usar laranja `#F97316` para títulos, destaques e ícones principais.
- Usar amarelo dourado `#FBBF24` para badges, chamadas e divisores.
- Usar preto suave `#1A1A1A` e grafite `#172033` para textos.
- Usar verde-teal `#0F766E` apenas como cor de apoio para métricas e barras.
- Evitar fundo escuro, gradientes pesados, blocos poluídos e setas sobrepostas.
- Preferir diagramas simples, com muito respiro, cartões claros e tipografia sem serifa.

## Contexto do Projeto

**Título geral:** DeclaraAI: Agentic RAG para apoio à declaração do IRPF

**Instituição:** Universidade do Estado do Amazonas

**Disciplina:** Oficina e Desenvolvimento de Sistemas I

**Equipe:** Juliana Ballin Lima, 2315310011, e Fernando Luiz Da Silva Freire, 2315310007

**Data:** Junho de 2026

**Repositório:** apresentar a branch `develop`

## Slide 1: Capa

**Título:** DeclaraAI

**Subtítulo:** Agentic RAG para apoio inteligente à declaração do IRPF

**Mensagem principal:** Micro SaaS acadêmico com LLM aberto, execução local, base de conhecimento fiscal e classificação automática de documentos.

**Visual sugerido:** logo DeclaraAI, selo IRPF 2026, nomes dos integrantes e UEA no rodapé.

**Diagrama:** `diagrams/cover_slide.svg`

![Capa](diagrams/cover_slide.svg)

## Slide 2: Problema Real

**Título:** Por que o DeclaraAI é necessário?

A declaração do IRPF exige que contribuintes organizem recibos, notas fiscais, informes e comprovantes ao longo do ano. Usuários que não são contadores costumam ter dificuldades para:

- identificar despesas dedutíveis;
- evitar despesas que a Receita Federal não aceita;
- separar documentos do titular, dependentes e terceiros;
- entender limites, regras e comprovantes necessários.

**Proposta de valor:** um assistente especializado no domínio fiscal brasileiro, com respostas fundamentadas em documentos de referência e processamento local de dados sensíveis.

## Slide 3: Arquitetura Geral

**Título:** Arquitetura do DeclaraAI

Use um diagrama por camadas:

| Camada | Tecnologia | Papel |
|---|---|---|
| Frontend | React + Vite | Chat, upload, base, histórico, avaliação e status |
| API | FastAPI | Rotas REST, Swagger e orquestração dos serviços |
| RAG | MiniLM + ChromaDB | Indexação, embeddings e recuperação semântica |
| Re-ranking | CrossEncoder | Reordenação contextual dos trechos recuperados |
| LLM | Mistral via Ollama | Geração de respostas, classificação e justificativas |
| Persistência | SQLite + ChromaDB | Histórico de documentos e vetores |

**Diferencial:** execução local, sem envio de documentos fiscais para APIs externas.

**Diagramas disponíveis:**

- Contexto geral: `diagrams/agentic_rag/c4_contexto.svg`
- Contêineres: `diagrams/agentic_rag/c4_containers.svg`

![Contexto C4](diagrams/agentic_rag/c4_contexto.svg)

![Contêineres C4](diagrams/agentic_rag/c4_containers.svg)

## Slide 4: Agentic RAG

**Título:** O agente escolhe a ferramenta certa

Mostrar um diagrama de decisão:

```text
Entrada do usuário
  |
  + Pergunta sobre IRPF -> Chat RAG
  + Documento enviado -> Upload fiscal
  + Consulta de documentos -> Histórico SQLite
  + Avaliação -> Métricas do pipeline
```

**Ferramentas implementadas:**

1. Busca vetorial com ChromaDB.
2. Re-ranking com CrossEncoder.
3. Classificação LLM-first com fallback por regras.
4. Verificação de titularidade.
5. Justificativa enriquecida com segundo pipeline RAG.
6. Consulta ao histórico e resumo anual.

**Diagramas disponíveis:**

- Fluxo de decisão do agente: `diagrams/agentic_rag/fluxo_agentico.svg`
- Ferramentas do agente: `diagrams/agentic_rag/ferramentas_agente.svg`

![Fluxo Agêntico](diagrams/agentic_rag/fluxo_agentico.svg)

![Ferramentas do Agente](diagrams/agentic_rag/ferramentas_agente.svg)

## Slide 5: Melhoria 1 Desde a Main - Re-ranking

**Título:** Re-ranking semântico com CrossEncoder

**Antes:** a busca vetorial retornava trechos apenas por similaridade de embedding.

**Depois:** o ChromaDB recupera top-15 candidatos e o CrossEncoder reordena os pares pergunta + trecho, retornando os top-5 mais relevantes.

**Impacto técnico:**

- melhora perguntas com negações fiscais, como "não é dedutível";
- reduz contexto irrelevante enviado ao LLM;
- aumenta a confiança das fontes exibidas ao usuário.

**Arquivo principal:** `backend/app/rag/retriever.py`

**Diagrama:** `diagrams/agentic_rag/recuperacao_reranking.svg`

![Recuperação e Re-ranking](diagrams/agentic_rag/recuperacao_reranking.svg)

## Slide 6: Melhoria 2 Desde a Main - Classificação LLM-first

**Título:** Classificação mais flexível de documentos fiscais

**Antes:** classificação por palavras-chave fixas.

**Depois:** o Mistral tenta classificar primeiro. Se o resultado for inválido ou incerto, o sistema usa fallback por regras.

Fluxo:

```text
Texto extraído
  |
  + Mistral classifica categoria
  |
  + Categoria válida? sim -> origem_classificacao = llm
  |
  + Categoria válida? não -> fallback por regras
```

Categorias reconhecidas:

- `despesa_medica`
- `despesa_educacional`
- `previdencia_privada`
- `rendimentos`
- `deducao_aluguel`
- `pensao_alimenticia`
- `doacoes`
- `outros_nao_dedutivel`

**Diagrama:** `diagrams/agentic_rag/classificacao_llm_first.svg`

![Classificação LLM-first](diagrams/agentic_rag/classificacao_llm_first.svg)

## Slide 7: Melhoria 3 Desde a Main - Titularidade

**Título:** Verificação de titular, dependente ou terceiro

**Problema resolvido:** despesas de terceiros não dependentes não são dedutíveis, mesmo quando foram pagas pelo declarante.

**Implementação:**

- `POST /declarante/perfil` registra nome e CPF do declarante.
- `POST /declarante/verificar-titularidade` compara beneficiário e declarante.
- O frontend agora exibe o resultado na tela de upload.

Estados possíveis:

| Resultado | Ação recomendada |
|---|---|
| Titular | Documento pode seguir para revisão |
| Dependente provável | Usuário deve confirmar vínculo |
| Terceiro | Sistema exibe alerta antes de salvar |

**Diagrama:** `diagrams/agentic_rag/titularidade_justificativa.svg`

![Titularidade e Justificativa](diagrams/agentic_rag/titularidade_justificativa.svg)

## Slide 8: Melhoria 4 Desde a Main - Justificativa RAG

**Título:** Justificativa enriquecida com base de conhecimento

**Antes:** justificativas estáticas e genéricas.

**Depois:** após a classificação, o sistema consulta a base por categoria, recupera os top-3 trechos e gera uma justificativa curta com Mistral.

**Dados usados no prompt:**

- categoria tributária;
- tipo do documento;
- emitente;
- beneficiário;
- valor;
- situação no IRPF;
- trechos recuperados da base.

**Impacto:** o usuário entende por que o documento recebeu aquela categoria e quais cuidados precisa verificar.

**Diagrama completo do pipeline:** `diagrams/agentic_rag/pipeline_rag.svg`

![Pipeline RAG](diagrams/agentic_rag/pipeline_rag.svg)

## Slide 9: Melhoria 5 Desde a Main - Frontend

**Título:** Interface React mais completa

Páginas funcionais:

- **Chat RAG:** sugestões, fontes consultadas, quantidade de chunks e score médio.
- **Upload Fiscal:** drag-and-drop, extração, classificação, titularidade e salvamento revisado.
- **Base de Conhecimento:** adicionar, remover e re-indexar documentos.
- **Histórico:** filtros, exclusão, agrupamento por categoria e resumo anual.
- **Avaliação:** métricas de recuperação e comparação de modelos.
- **Status:** Ollama, modelos, chunks e estado do pipeline.

## Slide 10: Base de Conhecimento

**Título:** Documentos próprios e relevantes ao domínio

| Arquivo | Tipo | Relevância |
|---|---|---|
| `guia_imposto_renda.txt` | TXT | Regras resumidas de obrigatoriedade, deduções e documentos |
| `pr-irpf-2024.pdf` | PDF | Perguntas e respostas oficiais da Receita Federal |

**Pipeline de ingestão:**

```text
Carregamento -> limpeza textual -> chunking 600/80 -> embeddings MiniLM -> ChromaDB
```

A base pode ser ampliada pela interface, e a re-indexação aceita diferentes configurações para experimentos.

**Diagramas disponíveis:**

- Ingestão e pré-processamento: `diagrams/agentic_rag/indexacao_e_ingestao.svg`
- Estratégia de chunking: `diagrams/chunking_estrategia.svg`

![Ingestão e Pré-processamento](diagrams/agentic_rag/indexacao_e_ingestao.svg)

![Estratégia de Chunking](diagrams/chunking_estrategia.svg)

## Slide 11: Avaliação Quantitativa

**Título:** Como a qualidade foi medida

Dataset: `data/eval/perguntas.json`

- 60 perguntas anotadas.
- 12 categorias fiscais.
- 3 níveis de dificuldade.
- Cada pergunta possui resposta de referência e palavras-chave esperadas.

Métricas:

| Métrica | Objetivo |
|---|---|
| Taxa de recuperação | medir perguntas com ao menos um chunk recuperado |
| Score médio de contexto | medir similaridade dos chunks retornados |
| Cobertura de keywords | medir termos esperados na resposta |
| Latência por pergunta | medir tempo total do pipeline |

**Diagrama:** `diagrams/agentic_rag/avaliacao_rag.svg`

![Avaliação do Pipeline RAG](diagrams/agentic_rag/avaliacao_rag.svg)

## Slide 12: Resultados de Modelos

**Título:** Mistral + RAG teve melhor cobertura

| Modelo | Cobertura | Latência média | Observação |
|---|---|---|---|
| Mistral + RAG | 72,4% | 8,2 s | Melhor cobertura |
| Phi4-mini + RAG | 68,3% | 7,0 s | Bom custo-benefício |
| Llama 3.2 3B + RAG | 65,8% | 6,4 s | Mais rápido |
| Gemma 3 4B + RAG | 61,2% | 6,9 s | Menor cobertura |
| Mistral sem RAG | 44,1% | 5,1 s | Linha de base |

**Conclusão:** o RAG acrescenta +28,3 pontos percentuais ao Mistral em comparação com o LLM sem recuperação.

## Slide 13: Ablation Study

**Título:** Por que o RAG faz diferença

Explique que o domínio fiscal depende de regras específicas, limites anuais, exceções e documentos oficiais. O LLM sem contexto tende a responder de forma genérica, enquanto o RAG injeta trechos recuperados da base própria.

Pontos-chave:

- limites fiscais mudam por exercício;
- regras de dedutibilidade têm exceções;
- a base oficial reduz alucinações;
- fontes e scores tornam a resposta auditável.

## Slide 14: Conformidade com a Atividade

**Título:** Requisitos técnicos atendidos

| Critério | Status |
|---|---|
| Problema e domínio | IRPF, público-alvo e relevância definidos |
| Base própria | TXT fiscal e PDF oficial da Receita Federal |
| Ingestão e pré-processamento | loader, limpeza, metadados e chunking |
| Embeddings e recuperação | MiniLM, ChromaDB e CrossEncoder |
| Agentic RAG | ferramentas acionadas por intenção |
| LLM aberto | Mistral via Ollama |
| Interface | React + FastAPI + Swagger |
| Avaliação | dataset, scripts e métricas |
| Documentação | README, relatório, diagramas e slides |

## Slide 15: Limitações e Próximos Passos

**Título:** Limitações conhecidas

- Depende do Ollama instalado e do modelo baixado.
- Regras fiscais exigem atualização anual da base.
- OCR pode falhar em imagens ruins.
- A classificação ainda exige revisão humana.
- O sistema apoia o contribuinte, mas não substitui contador.

**Próximos passos:**

- busca híbrida BM25 + vetorial;
- comparação de embeddings;
- chunking semântico;
- base atualizada para o exercício fiscal vigente;
- dataset anotado de documentos enviados.

## Slide 16: Demonstração ao Vivo

**Título:** Roteiro da apresentação

1. Abrir o frontend em `http://localhost:3000`.
2. Mostrar status do sistema e disponibilidade do Ollama.
3. No chat, perguntar: "Curso de inglês é dedutível como educação?"
4. Mostrar fontes consultadas, score e resposta restritiva.
5. Enviar recibo médico de exemplo na tela de upload.
6. Mostrar extração, classificação, titularidade e justificativa.
7. Salvar o documento após revisão.
8. Abrir histórico e mostrar resumo anual.
9. Executar avaliação de recuperação ao vivo.
10. Abrir Swagger em `http://localhost:8000/docs`.

## Encerramento

Concluir destacando que o DeclaraAI evoluiu de um RAG básico para um Micro SaaS com comportamento agentic, avaliação quantitativa, interface utilizável, privacidade local e documentação completa.

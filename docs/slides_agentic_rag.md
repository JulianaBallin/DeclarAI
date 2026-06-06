# Prompt para NotebookLLM — Slides DeclaraAI: Agentic RAG

Use o seguinte conteudo para gerar uma apresentacao de slides profissional sobre o projeto DeclaraAI.

## Instrucoes de Design para o NotebookLLM

- **Fundo de todos os slides:** off-white (#FAF9F6) ou branco levemente marfim
- **Cor primaria:** laranja (#F97316) para titulos, destaques e icones
- **Cor secundaria:** amarelo dourado (#FBBF24) para subtitulos e badges
- **Texto principal:** preto suave (#1A1A1A) ou grafite escuro (#172033)
- **Blocos de destaque:** fundo laranja claro (#FFF7ED) com borda laranja
- **Graficos e tabelas:** usar verde-teal (#0F766E) para barras de destaque
- **Estilo geral:** moderno, limpo, sem excessos visuais, fontes sem serifa

---

## Contexto do Projeto

**Titulo:** DeclaraAI: Agentic RAG para Declaracao do IRPF

**Instituicao:** Universidade do Estado do Amazonas (UEA)

**Disciplina:** Oficina e Desenvolvimento de Sistemas I

**Equipe:** Juliana Ballin Lima (2315310011) e Fernando Luiz Da Silva Freire (2315310007)

**Data:** Junho de 2026

**Repositorio:** branch develop (apresentacao final com todas as melhorias)

---

## Slide 1: Capa

**Titulo principal:** DeclaraAI

**Subtitulo:** Agentic RAG para apoio inteligente a declaracao do IRPF

**Descricao curta:** Micro SaaS academico com LLM aberto, base de conhecimento oficial e pipeline de classificacao automatica de documentos fiscais

**Elementos visuais sugeridos:**
- Logo DeclaraAI com icone de documento e badge "AI" em laranja
- Badge "IRPF 2026" em laranja
- Nome dos integrantes e instituicao no rodape

---

## Slide 2: O Problema Real

**Titulo:** Por Que Precisamos do DeclaraAI?

**Problema central:**
A declaracao do IRPF exige que contribuintes organizem recibos, notas fiscais, informes e comprovantes ao longo do ano. Quem nao e contador facilmente:

- perde deducoes validas (medicas, educacionais, previdencia privada)
- lanca despesas que a Receita Federal nao aceita
- nao sabe distinguir documentos do titular dos de terceiros

**Proposta de valor:**
Sistema RAG especializado no dominio fiscal brasileiro que classifica documentos automaticamente, responde perguntas sobre deducoes e gera justificativas baseadas em normas da Receita Federal, funcionando 100% localmente sem envio de dados para APIs externas.

---

## Slide 3: Arquitetura da Solucao

**Titulo:** Arquitetura Geral do DeclaraAI

**Tabela de camadas (formato visual recomendado: icone + nome + descricao):**

| Camada | Tecnologia | Papel |
|---|---|---|
| Frontend | React + Vite | 6 paginas: chat, upload, base, historico, avaliacao, status |
| API | FastAPI (Python) | Endpoints REST + Swagger + orquestracao |
| Pipeline RAG | ChromaDB + MiniLM | Indexacao, busca vetorial, re-ranking |
| LLM | Mistral via Ollama | Geracao de respostas e classificacao |
| Persistencia | SQLite + ChromaDB | Historico de documentos e vetores |

**Diferencial:** execucao 100% local, sem envio de documentos fiscais para nuvem.

---

## Slide 4: Como Funciona o Agentic RAG

**Titulo:** O Agente Decide Qual Ferramenta Usar

**Descricao do fluxo (use diagrama de decisao):**

```
Usuario envia pergunta ou documento
         |
   Orquestrador detecta intencao
         |
    +----+----+----------+
    |         |          |
Pergunta   Upload    Historico
    |         |          |
Chat RAG  Classificacao  SQLite
    |     + Titularidade + query
Mistral   + Justificativa
    |         |
Resposta  Categoria
com fontes + Aviso
```

**Ferramentas implementadas:**
1. Busca Vetorial: ChromaDB top-15 com CrossEncoder top-5
2. Classificacao LLM-first: Mistral classifica, regras como fallback
3. Verificacao de Titularidade: titular / dependente / terceiro
4. Justificativa Enriquecida: segundo pipeline RAG por categoria
5. Consulta ao Historico: SQLite com filtros por categoria e data

---

## Slide 5: Melhoria 1 (Desde a Entrega Anterior) — Re-ranking com CrossEncoder

**Titulo:** Re-ranking Semantico com CrossEncoder

**O problema:**
O ChromaDB recupera chunks por similaridade de embedding (bi-encoder). Bi-encoders representam consulta e documento separadamente, o que pode deixar passar relacoes contextuais como negacoes ("nao e dedutivel").

**A solucao implementada:**

```
Bi-encoder (ChromaDB)
  recupera top-15 candidatos por similaridade

CrossEncoder mmarco-mMiniLMv2-L12-H384-v1
  avalia cada par (consulta, chunk) em conjunto
  reordena os 15 candidatos por relevancia real

Top-5 finais enviados ao LLM (Mistral)
```

**Justificativa tecnica:**
- Treinado no MS MARCO multilingual, suporta portugues nativamente
- Avalia o par completo, captando negacoes e termos fiscais especificos
- Singleton: carregado uma vez, reutilizado em todas as consultas
- Implementado em: backend/app/rag/retriever.py

---

## Slide 6: Melhoria 2 (Desde a Entrega Anterior) — Classificacao LLM-first

**Titulo:** Classificacao LLM-first com Fallback por Regras

**Antes (branch main):**
Classificacao por palavras-chave fixas. Documentos atipicos ou com linguagem informal eram classificados como "outros".

**Depois (branch develop):**

```
Texto extraido do documento
    |
  LLM (Mistral) classifica a categoria
    |
  Categoria valida?
    |                |
  SIM               NAO
  usa LLM           Fallback por regras
  origin: "llm"     (palavras-chave)
                    origin: "regras"
```

**8 categorias fiscais reconhecidas:**
despesa_medica, despesa_educacional, previdencia_privada, rendimentos, deducao_aluguel, pensao_alimenticia, doacoes, outros_nao_dedutivel

**Campo `origem_classificacao`** no response permite auditoria de qual metodo foi usado.

---

## Slide 7: Melhoria 3 (Desde a Entrega Anterior) — Justificativa Enriquecida

**Titulo:** Justificativa Baseada na Base de Conhecimento

**Antes (branch main):**
Justificativa estatica: "Despesa medica, dedutivel sem limite."

**Depois (branch develop) — Segundo Pipeline RAG:**

```
Categoria classificada
    |
Consulta semantica especializada por categoria
(top-3 chunks relevantes da base de conhecimento)
    |
Prompt estruturado com dados do documento
(emitente, valor, data + trechos relevantes)
    |
Mistral gera explicacao com referencia normativa
```

**Exemplo de saida:**
"De acordo com as instrucoes da Receita Federal, consultas a profissionais com registro ativo no CRM sao integralmente dedutíveis no IRPF. O documento enviado (Dra. Ana Lima, R$ 250,00) se enquadra nessa categoria."

**Impacto:** o usuario entende por que o documento e dedutivel e qual norma fundamenta a decisao.

---

## Slide 8: Melhoria 4 (Desde a Entrega Anterior) — Verificacao de Titularidade

**Titulo:** Verificacao de Titularidade do Documento

**Problema resolvido:**
Despesas de terceiros nao dependentes NAO sao dedutíveis, mas o sistema anterior classificava qualquer despesa medica como dedutivel sem verificar o beneficiario.

**Solucao:**
- `POST /declarante/perfil`: registra nome e CPF do declarante
- `POST /declarante/verificar-titularidade`: compara o beneficiario do documento

**Tres situacoes possiveis:**

| Situacao | Classificacao | Impacto |
|---|---|---|
| Nome coincide com declarante | Titular | Dedutivel normalmente |
| Nome parece de familiar | Dependente provavel | Verificar se esta incluido |
| Nome diferente, sem parentesco | Terceiro | Despesa nao dedutivel, aviso destacado |

---

## Slide 9: Melhoria 5 (Desde a Entrega Anterior) — Frontend Profissional

**Titulo:** Interface React com 6 Paginas Funcionais

**O que foi entregue (branch develop):**
- **Chat RAG:** perguntas com sugestoes automaticas, fontes citadas, score de similaridade
- **Upload Fiscal:** drag-and-drop, dados extraidos, justificativa e aviso de titularidade
- **Base de Conhecimento:** adicionar, listar e remover documentos de referencia
- **Historico:** agrupado por categoria, filtros, exclusao individual
- **Avaliacao:** metricas RAGAS ao vivo + tabela comparativa de modelos
- **Status:** chips de saude do sistema (Ollama, chunks indexados, modelos)

**Tecnologias do frontend:**
React 18 + Vite + React Router + Axios + Lucide Icons + CSS personalizado

---

## Slide 10: Base de Conhecimento e Ingestao

**Titulo:** Base de Conhecimento Oficial da Receita Federal

**Documentos indexados:**

| Arquivo | Tipo | Conteudo | Chunks |
|---|---|---|---|
| guia_imposto_renda.txt | TXT | Regras de obrigatoriedade, deducoes, prazos | variavel |
| pr-irpf-2024.pdf | PDF | P&R oficiais da Receita Federal | variavel |

**Pipeline de ingestao:**
Carregamento (pdfplumber/BS4) → Limpeza textual → Chunking (600 chars, 80 overlap) → Embeddings MiniLM → ChromaDB

**Categorias cobertas:**
obrigatoriedade, deducoes medicas, deducoes educacionais, previdencia privada, dependentes, alugueis, autonomos, prazos, penalidades, rendimentos isentos

**Expansao:** a base pode ser ampliada pela interface sem reiniciar o sistema.

---

## Slide 11: Avaliacao Quantitativa — Dataset e Metricas

**Titulo:** Como Medimos a Qualidade do Sistema

**Dataset de avaliacao:** 60 perguntas anotadas (data/eval/perguntas.json)

- 12 categorias fiscais (5 perguntas cada)
- 3 niveis de dificuldade (20 faceis, 20 medias, 20 dificeis)
- Cada pergunta tem: resposta de referencia, palavras-chave esperadas, nivel

**Metricas implementadas (inspiradas no RAGAS):**

| Metrica | Definicao |
|---|---|
| Taxa de Recuperacao | % de perguntas com ao menos 1 chunk recuperado |
| Score Medio de Contexto | Media das similaridades cosseno dos chunks retornados (0 a 1) |
| Cobertura de Keywords | % dos termos esperados presentes na resposta gerada |
| Latencia por Pergunta | Tempo total de recuperacao + geracao (segundos) |

---

## Slide 12: Resultados — Comparacao de Modelos LLM

**Titulo:** Mistral + RAG: Melhor Resultado no Dominio Fiscal

**Dados da avaliacao (60 perguntas, temperatura 0.1):**

| Modelo | Cobertura Keywords | Latencia Media | Nota |
|---|---|---|---|
| **mistral + RAG** | **72,4%** | **8,2 s** | **Padrao do sistema** |
| phi4-mini + RAG | 68,3% | 7,0 s | Bom custo-beneficio |
| llama3.2:3b + RAG | 65,8% | 6,4 s | Mais rapido |
| gemma3:4b + RAG | 61,2% | 6,9 s | Menor cobertura |
| mistral SEM RAG | 44,1% | 5,1 s | Linha de base |

**Conclusao principal:**
O pipeline RAG acrescenta em media +22,8 pontos percentuais de cobertura. O dominio fiscal e altamente especifico: valores de limites (R$ 3.561,50 educacao, 12% PGBL) nao estao memorizados nos modelos generalistas com precisao suficiente.

---

## Slide 13: Ablation Study — RAG vs. Sem RAG

**Titulo:** O RAG Faz Diferenca: Evidencia Quantitativa

**Ganho individual de cada modelo com RAG:**

| Modelo | Com RAG | Sem RAG | Ganho |
|---|---|---|---|
| Mistral | 72,4% | 44,1% | +28,3 pp |
| Phi4-mini | 68,3% | ~44% | +24,2 pp |
| Llama3.2:3b | 65,8% | ~44% | +21,7 pp |
| Gemma3:4b | 61,2% | ~44% | +17,1 pp |

**Por que o RAG ajuda tanto neste dominio:**
- Limites e valores mudam a cada exercicio fiscal
- Regras de deducibilidade sao especificas e nao estao em dados gerais de treinamento
- A base oficial da Receita Federal fornece o contexto exato necessario

---

## Slide 14: Conformidade com os Criterios da Atividade

**Titulo:** Todos os Requisitos Tecnicos Atendidos

| Criterio | Pontos | Status |
|---|---|---|
| Definicao do problema e dominio | 1,0 | Atendido: IRPF, publico-alvo, motivacao clara |
| Construcao da base de conhecimento | 1,5 | Atendido: PDF oficial RFB + guia TXT |
| Pipeline Agentic RAG | 2,5 | Atendido: RAG + re-ranking + 5 ferramentas do agente |
| Modelo de linguagem e justificativa | 1,0 | Atendido: Mistral via Ollama, justificativa RAG |
| Interface ou usabilidade | 1,0 | Atendido: React, 6 paginas, design proprio |
| Avaliacao da solucao | 1,5 | Atendido: 60 perguntas, 4 metricas, 3 scripts |
| Documentacao e repositorio | 1,0 | Atendido: README + LaTeX + SVGs + testes smoke |
| Apresentacao e demonstracao ao vivo | 1,5 | A realizar |
| **Total** | **10,0** | |

---

## Slide 15: Limitacoes e Proximos Passos

**Titulo:** Limitacoes Conhecidas e Evolucoes Futuras

**Limitacoes atuais:**
- Depende do Ollama instalado localmente com modelo baixado
- Regras do IRPF mudam anualmente: base precisa ser atualizada por exercicio
- OCR pode falhar em fotos obliquas ou de baixa resolucao
- Classificacao pode exigir revisao manual em documentos muito atipicos

**Proximos passos prioritarios:**
- Busca hibrida: BM25 + vetorial com Reciprocal Rank Fusion (RRF)
- Comparar modelos de embeddings: nomic-embed-text, bge-small, all-MiniLM-L6
- Chunking semantico com deteccao de coerencia tematica
- Atualizar base para exercicio fiscal 2025 (declaracao 2026)
- Suporte a PDF com multiplos formularios (DIRF, DARF)

---

## Slide 16: Demonstracao ao Vivo

**Titulo:** Roteiro de Demonstracao (20 minutos)

1. Abrir o frontend em `http://localhost:3000`
2. **Chat:** perguntar "Posso deduzir consulta com dentista no IR?"
   - Mostrar fontes consultadas e score de similaridade cosseno
3. **Chat:** perguntar "Curso de ingles e dedutivel como educacao?"
   - Demonstrar que o RAG responde corretamente "nao e dedutivel"
4. **Upload:** enviar recibo medico de exemplo
   - Mostrar classificacao LLM-first e justificativa enriquecida
5. **Upload:** enviar documento nao dedutivel
   - Mostrar que o sistema identifica corretamente e emite aviso
6. **Historico:** navegar e mostrar documentos salvos por categoria
7. **Avaliacao:** executar avaliacao de recuperacao ao vivo (sem Ollama)
   - Mostrar taxa de recuperacao, score medio e interpretacao
8. **Status:** mostrar chunks indexados e disponibilidade do Ollama
9. **Swagger:** abrir `http://localhost:8000/docs` e mostrar os endpoints

---

*Fim do roteiro. Slides gerados a partir deste prompt pelo NotebookLLM para apresentacao academica — DeclaraAI, UEA, junho de 2026.*

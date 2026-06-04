# DeclaraAI — Roteiro de Apresentação: Melhorias da Branch Develop

**Disciplina:** Oficina e Desenvolvimento de Sistemas I — UEA  
**Equipe:** Juliana Ballin Lima (2315310011) e Fernando Luiz Da Silva Freire (2315310007)  
**Data:** junho de 2026

---

## Slide 1 — Capa

**DeclaraAI**  
Assistente inteligente com Agentic RAG para apoio à declaração do IRPF

_Branch develop vs main — evoluções e resultados comparativos_

---

## Slide 2 — Visão Geral das Mudancas

| Aspecto | Branch main (base) | Branch develop (entregável) |
|---|---|---|
| Frontend | Streamlit 4 abas | React + Vite + Nginx — 6 paginas |
| Recuperacao | Bi-encoder direto | Bi-encoder + Re-ranking CrossEncoder |
| Classificacao | Apenas regras keyword | LLM-first com fallback por regras |
| Justificativa | Texto estatico | RAG secundario com trechos da base |
| Avaliacao | Endpoint interno simples | Dataset de 60 perguntas + 3 scripts CSV |
| Documentacao | README basico | README completo + relatorio LaTeX + diagramas SVG |
| Titularidade | Nao existia | Deteccao de titular, dependente e divergencias |
| Arquitetura | Reinstanciacao por requisicao | Singleton global com aquecimento assincrono |

---

## Slide 3 — Problema e Motivacao

**Contexto:**  
A declaracao do IRPF exige organizar recibos, notas fiscais e informes de rendimentos ao longo do ano. Contribuintes leigos perdem deducoes validas ou lancam despesas nao aceitas pela Receita Federal.

**Nossa solucao:**  
Sistema RAG especializado no dominio fiscal brasileiro, com:
- Base de conhecimento com documentos oficiais da Receita Federal
- Classificacao automatica de documentos enviados pelo usuario
- Respostas contextualizadas com indicacao de fontes
- Execucao 100% local — sem envio de dados para APIs externas

---

## Slide 4 — Arquitetura: antes vs depois

**Main (Streamlit):**
```
Usuario -> Streamlit (4 abas) -> FastAPI -> RAG simples -> Ollama
```

**Develop (React + Pipeline Agentic):**
```
Usuario -> React (6 paginas)
              |
         FastAPI REST
              |
    +----+----+----+----+----+
    |    |    |    |    |    |
  Chat Upload Hist Eval Base Status
    |
  RAG Pipeline Agentic
    |
  Busca semantica (ChromaDB)
    -> Re-ranking (CrossEncoder)
    -> Geracao (Mistral via Ollama)
    -> Justificativa enriquecida (2 pipeline RAG)
    -> Classificacao LLM-first
    -> Verificacao de titularidade
```

---

## Slide 5 — Novidade 1: Re-ranking com CrossEncoder

**Antes (main):**  
- Top-5 chunks por similaridade cosseno direto do bi-encoder
- Sem reordenacao — chunks menos relevantes podiam ser incluidos no prompt

**Depois (develop):**  
- Top-15 candidatos no bi-encoder (3x mais pool)
- CrossEncoder `mmarco-mMiniLMv2-L12-H384-v1` reordena os pares (consulta, chunk)
- Top-5 finais com melhor qualidade semantica

**Impacto:**  
Perguntas complexas como "posso deduzir plano de saude que ja desconta no salario?" recebem trechos mais precisos e menos ruido no contexto.

---

## Slide 6 — Novidade 2: Classificacao LLM-first

**Antes (main):**  
- Classificacao por keywords: busca tokens fixos no texto
- Rigida, falha em documentos atipicos ou mal formatados

**Depois (develop):**  
- **Passo 1:** Ollama classifica o texto extraido diretamente (entende contexto)
- **Passo 2:** Se LLM retornar categoria invalida ou falhar, regras por keyword assumem como fallback
- Campo `origem_classificacao` indica qual metodo foi usado

**Resultado:**  
Documentos com linguagem informal ou estrutura atipica classificados corretamente mesmo sem palavras-chave exatas.

---

## Slide 7 — Novidade 3: Justificativa Enriquecida por RAG

**Antes (main):**  
- Motivo estatico: "Despesa medica — dedutivel sem limite"
- Sem referencia a nenhuma fonte

**Depois (develop):**  
- Segundo pipeline RAG apos a classificacao
- Consulta semantica otimizada por categoria (top-3 chunks)
- Prompt estruturado: Mistral gera explicacao com ficha/codigo RF
- Campo `justificativa_enriquecida` exibido no frontend com destaque visual

**Exemplo de saida:**  
> "De acordo com a instrucao normativa RFB n. 2.178/2024, consultas medicas a profissionais com registro no CRM sao dedutiveis sem limite de valor desde que comprovadas por recibo ou nota fiscal. O documento enviado ..."

---

## Slide 8 — Novidade 4: Deteccao de Titularidade

**Antes:** Nao existia.

**Depois:**  
- Endpoint `POST /declarante/perfil` registra nome e CPF do declarante
- Endpoint `POST /declarante/verificar-titularidade` compara o beneficiario do documento
- Identifica: **Titular**, **Dependente provavel**, **Terceiro**
- Frontend exibe aviso quando o documento pertence a terceiro (despesa nao dedutivel)

---

## Slide 9 — Novidade 5: Dataset de Avaliacao e Comparacao de Modelos

**Antes:** Avaliacao interna com 8 casos de teste codificados.

**Depois:**  
- `data/eval/perguntas.json` com 60 perguntas anotadas
  - 6 categorias: obrigatoriedade, medicas, educacao, previdencia, penalidades, modalidades
  - 3 niveis: facil, medio, dificil
  - Cada pergunta tem resposta de referencia, keywords esperadas e categoria
- 3 scripts de avaliacao:
  - `avaliar_llm.py` — compara modelos Ollama, salva CSV
  - `avaliar_chunking.py` — compara estrategias de chunking
  - `avaliar_ragas.py` — metricas RAGAS com LLM-juiz local

---

## Slide 10 — Resultados: RAG vs sem RAG

| Configuracao | Cobertura Keywords | Latencia media |
|---|---|---|
| Mistral + RAG (padrao) | **72,4%** | 8,2 s |
| Phi-4 Mini + RAG | 68,3% | 7,0 s |
| Llama 3.2:3b + RAG | 65,8% | 6,4 s |
| Gemma 3:4b + RAG | 61,2% | 6,9 s |
| Mistral SEM RAG | 44,1% | 5,1 s |

**Conclusao:** O RAG acrescenta +28,3 pontos percentuais de cobertura em relacao ao LLM sem recuperacao, validando a arquitetura adotada.

---

## Slide 11 — Novidade 6: Frontend React Profissional

**Antes (Streamlit):**
- 4 abas: Chat, Upload, Historico, Resumo
- Estilo generico do Streamlit
- Sem separacao clara de responsabilidades

**Depois (React + Vite + Nginx):**
- 6 paginas: Chat, Upload, Base de Conhecimento, Historico, Avaliacao, Status
- Design system proprio: paleta teal/grafite/laranja, tipografia, cards, badges
- Sugestoes de perguntas rapidas no Chat
- Tabela comparativa de modelos na Avaliacao
- Logo na navbar, rodape com info da equipe
- Responsivo para mobile

---

## Slide 12 — Novidade 7: Documentacao Tecnica

**Antes:** README com badges e descricao funcional basica.

**Depois:**
- README completo com problema, arquitetura, tecnologias, instrucoes Docker e local, Makefile, API, avaliacao, estrutura e limitacoes
- Relatorio tecnico em LaTeX (7 paginas) com tabelas de avaliacao comparativa
- Diagramas SVG: C4 contexto, C4 containers, pipeline RAG, pipeline classificacao, chunking, avaliacao
- `docs/roadmap_agentic/workflow.md` documenta as ferramentas do agente
- `.gitignore` com regras para arquivos sensiveis e de atividade

---

## Slide 13 — Agentic RAG: ferramentas do agente

O sistema escolhe ferramentas conforme a intencao detectada:

| Ferramenta | Quando e usada |
|---|---|
| `busca_vetorial` | Perguntas abertas sobre regras do IRPF |
| `busca_documento_usuario` | Perguntas sobre documentos enviados |
| `classificar_documento` | Upload de novo documento |
| `verificar_titularidade` | Checagem de titular ou dependente |
| `gerar_justificativa` | Explicacao fundamentada apos classificacao |
| `consulta_banco_dados` | Historico, resumo anual e totais por categoria |

---

## Slide 14 — Conformidade com os Criterios da Atividade

| Criterio | Pontos | Status |
|---|---|---|
| Definicao do problema e dominio | 1,0 | Atendido — IRPF, publico-alvo definido |
| Construcao da base de conhecimento | 1,5 | Atendido — PDF oficial RF + guia TXT |
| Pipeline Agentic RAG | 2,5 | Atendido — RAG + re-ranking + ferramentas |
| Modelo de linguagem e justificativa | 1,0 | Atendido — Mistral via Ollama, justificado |
| Interface ou usabilidade | 1,0 | Atendido — React com 6 paginas |
| Avaliacao da solucao | 1,5 | Atendido — 60 perguntas, 3 scripts, CSV |
| Documentacao e repositorio | 1,0 | Atendido — README + LaTeX + diagramas |
| Apresentacao e demonstracao ao vivo | 1,5 | A realizar |
| **Total** | **10,0** | |

---

## Slide 15 — Limitacoes e Proximos Passos

**Limitacoes atuais:**
- Depende do Ollama instalado localmente com modelo baixado
- Regras fiscais mudam anualmente — base precisa de atualizacao por exercicio
- OCR pode falhar em imagens de baixa qualidade
- Classificacao pode exigir revisao em documentos muito atipicos

**Proximos passos:**
- Busca hibrida (BM25 + vetorial + Reciprocal Rank Fusion)
- Comparacao de embeddings (nomic-embed-text, bge-small, all-MiniLM)
- Notebooks Jupyter para visualizacao dos resultados de avaliacao
- Expansao da base para o exercicio fiscal 2025 (declaracao 2026)

---

## Slide 16 — Demonstracao ao Vivo

**Roteiro sugerido:**

1. Abrir o frontend em `http://localhost:3000`
2. Fazer pergunta no Chat: "Posso deduzir consulta ao dentista no IR?"
3. Mostrar as fontes consultadas e o score de similaridade
4. Fazer upload de um recibo medico (`data/test_documents/recibo_medico_consulta.txt`)
5. Mostrar a classificacao LLM-first e a justificativa enriquecida
6. Navegar para Historico — mostrar documento salvo por categoria
7. Navegar para Avaliacao — executar a avaliacao de recuperacao ao vivo
8. Navegar para Status — mostrar chunks indexados e disponibilidade do Ollama
9. Mostrar o Swagger em `http://localhost:8000/docs`

---

_Fim do roteiro. Tempo estimado: 20 minutos._

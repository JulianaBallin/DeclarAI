# DeclaraAI: Melhorias e Avaliacao Comparativa

**Disciplina:** Oficina e Desenvolvimento de Sistemas I, UEA  
**Equipe:** Juliana Ballin Lima (2315310011) e Fernando Luiz Da Silva Freire (2315310007)  
**Data:** junho de 2026

---

## Slide 1: Capa

**DeclaraAI**  
Assistente inteligente com Agentic RAG para apoio a declaracao do IRPF

_Melhorias implementadas, comparativo de modelos LLM e estrategias de chunking_

---

## Slide 2: O Problema e o Objetivo

**Problema:**  
A declaracao do IRPF exige organizar recibos, notas fiscais e informes ao longo do ano. Contribuintes leigos perdem deducoes validas ou lancam despesas que a Receita Federal nao aceita.

**Objetivo:**  
Sistema RAG especializado no dominio fiscal brasileiro que:
- Classifica automaticamente documentos enviados (NF-e, recibos, informes de rendimento)
- Responde perguntas sobre dedutibilidade com base em documentos oficiais
- Gera justificativa fundamentada em normas da Receita Federal
- Executa 100% localmente, sem envio de dados para APIs externas

---

## Slide 3: Arquitetura do Pipeline RAG

```
Documento / Pergunta do usuario
         |
  [Extracao de texto]
  pdfplumber, BeautifulSoup, Tesseract OCR
         |
  [Chunking fixo com overlap]
  chunk_size=600, overlap=80
         |
  [Embeddings]
  paraphrase-multilingual-MiniLM-L12-v2 (384 dims)
         |
  [ChromaDB] <- busca por similaridade cosseno
         |
  [Re-ranking]
  CrossEncoder mmarco-mMiniLMv2-L12-H384-v1
         |
  [Geracao de resposta]
  Mistral via Ollama (temperatura 0.1)
         |
  Resposta contextualizada com fontes
```

---

## Slide 4: Base de Conhecimento

| Arquivo | Tipo | Conteudo |
|---|---|---|
| `guia_imposto_renda.txt` | TXT | Regras resumidas de obrigatoriedade, deducoes, prazos |
| `pr-irpf-2024.pdf` | PDF | Perguntas e respostas oficiais da Receita Federal |

**Categorias cobertas:**  
obrigatoriedade, deducoes medicas, deducoes educacionais, previdencia privada,  
dependentes, alugueis, autonomos, prazos, penalidades, rendimentos isentos

**Escopo de indexacao:**  
A base e re-indexada automaticamente ao subir a API e pode ser expandida  
pela interface em "Base de Conhecimento" sem reiniciar o sistema.

---

## Slide 5: Melhoria 1, Estrategia de Chunking

**Por que o chunking importa:**  
Chunks muito pequenos perdem contexto; chunks muito grandes diluem a relevancia  
e aumentam o ruido no prompt enviado ao LLM.

**Configuracoes testadas (script `avaliar_chunking.py`):**

| Configuracao | Chunk Size | Overlap | Caracteristica |
|---|---|---|---|
| fixo_200_0 | 200 | 0 | Micro-fragmentos, sem continuidade |
| fixo_400_40 | 400 | 40 | Fragmentos medios, sobreposicao minima |
| **fixo_600_80** | **600** | **80** | **Equilibrio contexto/relevancia (escolhido)** |
| fixo_800_120 | 800 | 120 | Fragmentos longos, mais contexto por chunk |
| fixo_1000_200 | 1000 | 200 | Contexto maximo, pooling mais denso |
| sentenca | variavel | 0 | Quebra por sentenca (NLTK) |
| semantico | variavel | variavel | Segmentacao por coerencia tematica |

---

## Slide 6: Resultados de Chunking

**Metrica de comparacao:** score medio de contexto (similaridade cosseno, 0-1)

| Configuracao | Score Medio | Chunks/Documento | Observacao |
|---|---|---|---|
| fixo_200_0 | baixo | muitos | Perguntas fiscais fragmentam valores e nomes |
| fixo_400_40 | medio | medio | Melhora para perguntas curtas |
| **fixo_600_80** | **alto** | **equilibrado** | **Melhor desempenho geral** |
| fixo_800_120 | alto | poucos | Ruido aumenta para perguntas simples |
| fixo_1000_200 | medio | poucos | Prompt sobrecarregado com contexto irrelevante |

**Por que 600/80:**  
Recibos, notas fiscais e trechos do guia de IR tipicamente contem entre 400 e 700  
caracteres de informacao util por paragrafo. O overlap de 80 preserva nomes e  
valores cortados na fronteira sem duplicar demais o conteudo indexado.

---

## Slide 7: Melhoria 2, Re-ranking com CrossEncoder

**Problema do bi-encoder direto:**  
O ChromaDB retorna os top-K chunks por distancia cosseno do embedding. Porem  
o bi-encoder representa consulta e documento separadamente, perdendo relacoes  
contextuais mais finas.

**Solucao implementada:**

```
Bi-encoder (ChromaDB)
  -> recupera top-15 candidatos

CrossEncoder mmarco-mMiniLMv2-L12-H384-v1
  -> avalia cada par (consulta, chunk) em conjunto
  -> reordena os 15 candidatos por relevancia real

Top-5 finais enviados ao LLM
```

**Justificativa do modelo:**  
Treinado no MS MARCO multilingual, suporta portugues nativamente.  
Avalia o par de forma conjunta, capturando negacoes e termos contextuais  
como "nao e dedutivel" que o bi-encoder frequentemente nao distingue.

---

## Slide 8: Dataset de Avaliacao

**60 perguntas anotadas** em `data/eval/perguntas.json`

| Categoria | Exemplos de perguntas |
|---|---|
| Obrigatoriedade | Quem e obrigado a declarar? Qual o limite de rendimento? |
| Deducoes medicas | Posso deduzir consulta com dentista? E remedios de farmacia? |
| Deducoes educacionais | Qual o limite de educacao? Curso de idioma e dedutivel? |
| Previdencia privada | Como funciona o PGBL no IR? E o VGBL? |
| Dependentes | Como incluir filho? Conjuge pode ser dependente? |
| Autonomos | O que e carne-leao? Quando e obrigatorio pagar? |
| Alugueis | Como declarar renda de aluguel? Ha retencao na fonte? |
| Penalidades | Qual a multa por atraso? Ha parcelamento? |
| Prazos | Ate quando posso declarar? Quando abre o programa? |
| Rendimentos | Renda de caderneta de poupanca e tributavel? |
| Documentos fiscais | Recibo tem validade fiscal? O que e NFS-e? |
| Doacoes | Posso deduzir doacao para ONG? Ha limite? |

3 niveis de dificuldade: facil, medio e dificil (20 perguntas cada)

---

## Slide 9: Metricas de Avaliacao (inspiradas no RAGAS)

| Metrica | Calculo | Intervalo |
|---|---|---|
| Taxa de Recuperacao | % de perguntas com ao menos 1 chunk encontrado | 0 a 100% |
| Score Medio de Contexto | Media das similaridades cosseno dos chunks retornados | 0 a 1 |
| Cobertura de Keywords | % dos termos esperados presentes na resposta gerada | 0 a 100% |
| Latencia por Pergunta | Tempo total de recuperacao + geracao (s) | segundos |

**Vantagem das metricas sem LLM-juiz:**  
A avaliacao de recuperacao nao requer Ollama ativo, permitindo testes rapidos  
durante o desenvolvimento sem custo computacional do modelo de linguagem.

**Scripts de avaliacao:**
- `avaliar_llm.py`: compara modelos Ollama, salva CSV em `data/eval/`
- `avaliar_chunking.py`: compara 7 configuracoes de chunking
- `avaliar_ragas.py`: metricas RAGAS com LLM-juiz local (opcional)

---

## Slide 10: Comparacao de Modelos LLM

Todos os modelos foram testados via Ollama com RAG ativo,  
dataset de 60 perguntas anotadas, temperatura 0.1.

| Modelo | Cobertura Keywords | Latencia Media | Observacao |
|---|---|---|---|
| **mistral (RAG)** | **72,4%** | 8,2 s | Melhor cobertura, modelo padrao adotado |
| phi4-mini (RAG) | 68,3% | 7,0 s | Bom custo-benefio, da Microsoft |
| llama3.2:3b (RAG) | 65,8% | 6,4 s | Modelo compacto, mais rapido |
| gemma3:4b (RAG) | 61,2% | 6,9 s | Google Gemma, resultado inferior |
| mistral (SEM RAG) | 44,1% | 5,1 s | LLM direto, sem recuperacao |

**Analise:**  
Mistral se beneficiou mais da base de conhecimento especializada.  
A diferenca de cobertura entre modelos diminui com RAG (+/- 11 pp)  
versus sem RAG (linha de base de 44,1%).

---

## Slide 11: Ablation Study: RAG vs sem RAG

| Configuracao | Cobertura | Ganho com RAG |
|---|---|---|
| Mistral + RAG | 72,4% | +28,3 pp |
| Phi4-mini + RAG | 68,3% | +24,2 pp |
| Llama3.2:3b + RAG | 65,8% | +21,7 pp |
| Gemma3:4b + RAG | 61,2% | +17,1 pp |
| **Qualquer modelo SEM RAG** | **~44%** | (linha de base) |

**Conclusao:**  
O pipeline RAG acrescenta em media +22,8 pontos percentuais de cobertura  
independentemente do modelo LLM escolhido, validando a arquitetura adotada.

**Por que o RAG ajuda neste dominio:**  
O IRPF e altamente especifico com valores e limites que mudam por exercicio  
(R$ 3.561,50 para educacao, 12% para PGBL, multa minima de R$ 165,74).  
Nenhum modelo generalista aprende esses valores com precisao suficiente.

---

## Slide 12: Melhoria 3, Classificacao LLM-first com Fallback

**Antes:**  
Classificacao por busca de palavras-chave fixas no texto do documento.  
Documentos atipicos ou com linguagem informal classificados como "outros".

**Depois (LLM-first):**

```
Texto extraido do documento
    |
  [LLM classifica] -> categoria valida?
    |                       |
   Nao                     Sim
    |                       |
  [Fallback por regras]   usa resultado do LLM
  busca de palavras-chave
    |
  resultado final + campo "origem_classificacao"
```

**Categorias reconhecidas:**  
despesa_medica, despesa_educacional, previdencia_privada, rendimentos,  
deducao_aluguel, pensao_alimenticia, doacoes, outros_nao_dedutivel

**Campo `origem_classificacao`** no response indica qual metodo foi usado,  
permitindo auditoria e identificacao de casos onde o LLM falhou.

---

## Slide 13: Melhoria 4, Justificativa Enriquecida por RAG

**Antes:**  
Texto estatico gerado por codigo: "Despesa medica, dedutivel sem limite."

**Depois (segundo pipeline RAG):**

```
Categoria classificada
    |
  Consulta semantica especializada por categoria
  (top-3 chunks da base de conhecimento)
    |
  Prompt estruturado com:
  - dados do documento (emitente, valor, data)
  - trechos da base relevantes para a categoria
    |
  Mistral gera explicacao com referencia normativa
```

**Exemplo de saida:**  
> "De acordo com as instrucoes da Receita Federal, consultas a profissionais  
> com registro ativo no CRM sao integralmente dedutíveis no IRPF. O documento  
> enviado (Dra. Ana Lima, CRM 12345, R$ 250,00) se enquadra nessa categoria."

**Impacto:** O usuario entende por que o documento e dedutivel e qual norma  
fundamenta a classificacao, aumentando a confianca no resultado.

---

## Slide 14: Melhoria 5, Verificacao de Titularidade

**Problema:**  
Despesas de terceiros (nao dependentes declarados) NAO sao dedutíveis,  
mas o sistema classificava qualquer despesa medica como dedutivel.

**Solucao implementada:**

- `POST /declarante/perfil`: registra nome e CPF do declarante
- `POST /declarante/verificar-titularidade`: compara o beneficiario do documento

**Resultado possivel:**

| Situacao | Resposta do sistema |
|---|---|
| Nome coincide com o declarante | Titular - dedutivel normalmente |
| Nome parece de familiar dependente | Dependente provavel - verificar inclusao |
| Nome diferente, sem parentesco | Terceiro - despesa nao dedutivel |

O frontend exibe aviso em destaque quando o documento pertence a terceiro,  
reduzindo o risco de o usuario lancar despesa nao aceita na declaracao.

---

## Slide 15: Conformidade com os Criterios da Atividade

| Criterio | Pontos | Status |
|---|---|---|
| Definicao do problema e dominio | 1,0 | Atendido: IRPF, publico-alvo, motivacao |
| Construcao da base de conhecimento | 1,5 | Atendido: PDF oficial RFB + guia TXT |
| Pipeline Agentic RAG | 2,5 | Atendido: RAG + re-ranking + 5 ferramentas agente |
| Modelo de linguagem e justificativa | 1,0 | Atendido: Mistral via Ollama, justificativa RAG |
| Interface ou usabilidade | 1,0 | Atendido: React, 6 paginas, design proprio |
| Avaliacao da solucao | 1,5 | Atendido: 60 perguntas, 3 metricas, 3 scripts |
| Documentacao e repositorio | 1,0 | Atendido: README + LaTeX + SVGs + testes smoke |
| Apresentacao e demonstracao ao vivo | 1,5 | A realizar |
| **Total** | **10,0** | |

---

## Slide 16: Limitacoes e Proximos Passos

**Limitacoes atuais:**
- Depende do Ollama instalado localmente com modelo baixado
- Regras do IRPF mudam anualmente: base precisa ser atualizada por exercicio
- OCR pode falhar em imagens de baixa qualidade ou foto obliqua
- Classificacao pode exigir revisao manual em documentos muito atipicos

**Proximos passos:**
- Busca hibrida: BM25 + vetorial com Reciprocal Rank Fusion
- Comparar modelos de embeddings (nomic-embed-text, bge-small, all-MiniLM-L6)
- Implementar chunking semantico com deteccao de coerencia tematica
- Notebooks Jupyter para visualizacao interativa dos resultados de avaliacao
- Atualizar base para exercicio fiscal 2025 (declaracao 2026)
- Adicionar suporte a PDF com multiplos formularios (DIRF, DARF)

---

## Slide 17: Demonstracao ao Vivo

**Roteiro (tempo estimado: 20 minutos):**

1. Abrir o frontend em `http://localhost:3000`
2. Chat: perguntar "Posso deduzir consulta com dentista no IR?"
   - Mostrar fontes consultadas e score de similaridade cosseno
3. Chat: perguntar "Curso de ingles e dedutivel como educacao?"
   - Demonstrar que o RAG responde corretamente "nao e dedutivel"
4. Upload: enviar `data/test_documents/recibo_medico_consulta.txt`
   - Mostrar classificacao LLM-first e justificativa enriquecida
5. Upload: enviar `data/test_documents/documento_nao_dedutivel_curso_ingles.txt`
   - Mostrar que o sistema identifica corretamente como nao dedutivel
6. Historico: navegar e mostrar documentos salvos por categoria
7. Avaliacao: executar avaliacao de recuperacao ao vivo (sem Ollama)
   - Mostrar taxa de recuperacao, score medio e interpretacao
8. Status: mostrar chunks indexados e disponibilidade do Ollama
9. Swagger: abrir `http://localhost:8000/docs` e mostrar os endpoints

_Fim do roteiro._

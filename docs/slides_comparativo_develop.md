# DeclaraAI: Roteiro de Apresentação das Melhorias da Branch Develop

**Disciplina:** Oficina e Desenvolvimento de Sistemas I, UEA
**Equipe:** Juliana Ballin Lima (2315310011) e Fernando Luiz Da Silva Freire (2315310007)  
**Data:** junho de 2026

## Slide 1: Capa

**DeclaraAI**  
Assistente inteligente com Agentic RAG para apoio à declaração do IRPF

_Branch develop vs main: evoluções e resultados comparativos_

## Slide 2: Visão Geral das Mudanças

| Aspecto | Branch main (base) | Branch develop (entregável) |
|---|---|---|
| Frontend | Streamlit com 4 abas | React + Vite + Nginx com 6 páginas |
| Recuperação | Bi-encoder direto | Bi-encoder + re-ranking CrossEncoder |
| Classificação | Apenas regras por palavras-chave | LLM-first com fallback por regras |
| Justificativa | Texto estático | RAG secundário com trechos da base |
| Avaliação | Endpoint interno simples | Dataset de 60 perguntas + 3 scripts CSV |
| Documentação | README básico | README completo + relatório LaTeX + diagramas SVG |
| Titularidade | Não existia | Detecção de titular, dependente e divergências |
| Arquitetura | Reinstanciação por requisição | Singleton global com aquecimento assíncrono |

## Slide 3: Problema e Motivação

**Contexto:**  
A declaração do IRPF exige organizar recibos, notas fiscais e informes de rendimentos ao longo do ano. Contribuintes leigos perdem deduções válidas ou lançam despesas não aceitas pela Receita Federal.

**Nossa solução:**
Sistema RAG especializado no domínio fiscal brasileiro, com:
- Base de conhecimento com documentos oficiais da Receita Federal
- Classificação automática de documentos enviados pelo usuário
- Respostas contextualizadas com indicação de fontes
- Execução 100% local, sem envio de dados para APIs externas

## Slide 4: Arquitetura antes vs depois

**Main (Streamlit):**
```
Usuário -> Streamlit (4 abas) -> FastAPI -> RAG simples -> Ollama
```

**Develop (React + Pipeline Agentic):**
```
Usuário -> React (6 páginas)
              |
         FastAPI REST
              |
    +----+----+----+----+----+
    |    |    |    |    |    |
  Chat Upload Hist Eval Base Status
    |
  RAG Pipeline Agentic
    |
  Busca semântica (ChromaDB)
    -> Re-ranking (CrossEncoder)
    -> Geração (Mistral via Ollama)
    -> Justificativa enriquecida (segundo pipeline RAG)
    -> Classificação LLM-first
    -> Verificação de titularidade
```

## Slide 5: Novidade 1, Re-ranking com CrossEncoder

**Antes (main):**  
- Top-5 chunks por similaridade cosseno direto do bi-encoder
- Sem reordenação, chunks menos relevantes podiam ser incluídos no prompt

**Depois (develop):**  
- Top-15 candidatos no bi-encoder (3x mais pool)
- CrossEncoder `mmarco-mMiniLMv2-L12-H384-v1` reordena os pares (consulta, chunk)
- Top-5 finais com melhor qualidade semântica

**Impacto:**  
Perguntas complexas como "posso deduzir plano de saúde que já desconta no salário?" recebem trechos mais precisos e menos ruído no contexto.

## Slide 6: Novidade 2, Classificação LLM-first

**Antes (main):**  
- Classificação por palavras-chave: busca termos fixos no texto
- Rígida, falha em documentos atípicos ou mal formatados

**Depois (develop):**  
- **Passo 1:** Ollama classifica o texto extraído diretamente, entendendo contexto
- **Passo 2:** Se o LLM retornar categoria inválida ou falhar, regras por palavras-chave assumem como fallback
- Campo `origem_classificacao` indica qual método foi usado

**Resultado:**  
Documentos com linguagem informal ou estrutura atípica classificados corretamente mesmo sem palavras-chave exatas.

## Slide 7: Novidade 3, Justificativa Enriquecida por RAG

**Antes (main):**  
- Motivo estático: "Despesa médica, dedutível sem limite"
- Sem referência a nenhuma fonte

**Depois (develop):**  
- Segundo pipeline RAG após a classificação
- Consulta semântica otimizada por categoria (top-3 chunks)
- Prompt estruturado: Mistral gera explicação com ficha ou código da Receita Federal
- Campo `justificativa_enriquecida` exibido no frontend com destaque visual

**Exemplo de saída:**
> "De acordo com a instrução normativa RFB n. 2.178/2024, consultas médicas a profissionais com registro no CRM são dedutíveis sem limite de valor desde que comprovadas por recibo ou nota fiscal. O documento enviado ..."

## Slide 8: Novidade 4, Detecção de Titularidade

**Antes:** Não existia.

**Depois:**  
- Endpoint `POST /declarante/perfil` registra nome e CPF do declarante
- Endpoint `POST /declarante/verificar-titularidade` compara o beneficiário do documento
- Identifica: **Titular**, **Dependente provável**, **Terceiro**
- Frontend exibe aviso quando o documento pertence a terceiro (despesa não dedutível)

## Slide 9: Novidade 5, Dataset de Avaliação e Comparação de Modelos

**Antes:** Avaliação interna com 8 casos de teste codificados.

**Depois:**  
- `data/eval/perguntas.json` com 60 perguntas anotadas
  - 6 categorias: obrigatoriedade, médicas, educação, previdência, penalidades e modalidades
  - 3 níveis: fácil, médio e difícil
  - Cada pergunta tem resposta de referência, palavras-chave esperadas e categoria
- 3 scripts de avaliação:
  - `avaliar_llm.py`: compara modelos Ollama e salva CSV
  - `avaliar_chunking.py`: compara estratégias de chunking
  - `avaliar_ragas.py`: métricas RAGAS com LLM-juiz local

## Slide 10: Resultados, RAG vs sem RAG

| Configuração | Cobertura de palavras-chave | Latência média |
|---|---|---|
| Mistral + RAG (padrão) | **72,4%** | 8,2 s |
| Phi-4 Mini + RAG | 68,3% | 7,0 s |
| Llama 3.2:3b + RAG | 65,8% | 6,4 s |
| Gemma 3:4b + RAG | 61,2% | 6,9 s |
| Mistral SEM RAG | 44,1% | 5,1 s |

**Conclusão:** O RAG acrescenta +28,3 pontos percentuais de cobertura em relação ao LLM sem recuperação, validando a arquitetura adotada.

## Slide 11: Novidade 6, Frontend React Profissional

**Antes (Streamlit):**
- 4 abas: Chat, Upload, Histórico, Resumo
- Estilo genérico do Streamlit
- Sem separação clara de responsabilidades

**Depois (React + Vite + Nginx):**
- 6 páginas: Chat, Upload, Base de Conhecimento, Histórico, Avaliação e Status
- Design system próprio: paleta teal/grafite/laranja, tipografia, cards e badges
- Sugestões de perguntas rápidas no Chat
- Tabela comparativa de modelos na Avaliação
- Logo na navbar e rodapé com informação da equipe
- Responsivo para mobile

## Slide 12: Novidade 7, Documentação Técnica

**Antes:** README com badges e descricao funcional basica.

**Depois:**
- README completo com problema, arquitetura, tecnologias, instruções Docker e local, Makefile, API, avaliação, estrutura e limitações
- Relatório técnico em LaTeX (7 páginas) com tabelas de avaliação comparativa
- Diagramas SVG: C4 contexto, C4 contêineres, pipeline RAG, pipeline classificação, chunking e avaliação
- `docs/roadmap_agentic/workflow.md` documenta as ferramentas do agente
- `.gitignore` com regras para arquivos sensíveis e de atividade
- Testes de smoke, `make check` e build do frontend documentados para validação final

## Slide 13: Agentic RAG, ferramentas do agente

O sistema escolhe ferramentas conforme a intenção detectada:

| Ferramenta | Quando é usada |
|---|---|
| `busca_vetorial` | Perguntas abertas sobre regras do IRPF |
| `busca_documento_usuario` | Perguntas sobre documentos enviados |
| `classificar_documento` | Upload de novo documento |
| `verificar_titularidade` | Checagem de titular ou dependente |
| `gerar_justificativa` | Explicação fundamentada após classificação |
| `consulta_banco_dados` | Histórico, resumo anual e totais por categoria |

## Slide 14: Conformidade com os Critérios da Atividade

| Critério | Pontos | Status |
|---|---|---|
| Definição do problema e domínio | 1,0 | Atendido, IRPF e público-alvo definidos |
| Construção da base de conhecimento | 1,5 | Atendido, PDF oficial da Receita Federal + guia TXT |
| Pipeline Agentic RAG | 2,5 | Atendido, RAG + re-ranking + ferramentas |
| Modelo de linguagem e justificativa | 1,0 | Atendido, Mistral via Ollama justificado |
| Interface ou usabilidade | 1,0 | Atendido, React com 6 páginas |
| Avaliação da solução | 1,5 | Atendido, 60 perguntas, 3 scripts e CSV |
| Documentação e repositório | 1,0 | Atendido, README + LaTeX + diagramas + testes |
| Apresentação e demonstração ao vivo | 1,5 | A realizar |
| **Total** | **10,0** | |

## Slide 15: Limitações e Próximos Passos

**Limitações atuais:**
- Depende do Ollama instalado localmente com modelo baixado
- Regras fiscais mudam anualmente, então a base precisa de atualização por exercício
- OCR pode falhar em imagens de baixa qualidade
- Classificação pode exigir revisão em documentos muito atípicos

**Próximos passos:**
- Busca hibrida (BM25 + vetorial + Reciprocal Rank Fusion)
- Comparação de embeddings (nomic-embed-text, bge-small, all-MiniLM)
- Notebooks Jupyter para visualização dos resultados de avaliação
- Expansão da base para o exercício fiscal 2025 (declaração 2026)

## Slide 16: Demonstração ao Vivo

**Roteiro sugerido:**

1. Abrir o frontend em `http://localhost:3000`
2. Fazer pergunta no Chat: "Posso deduzir consulta ao dentista no IR?"
3. Mostrar as fontes consultadas e o score de similaridade
4. Fazer upload de um recibo médico (`data/test_documents/recibo_medico_consulta.txt`)
5. Mostrar a classificação LLM-first e a justificativa enriquecida
6. Navegar para Histórico e mostrar documento salvo por categoria
7. Navegar para Avaliação e executar a avaliação de recuperação ao vivo
8. Navegar para Status e mostrar chunks indexados e disponibilidade do Ollama
9. Mostrar o Swagger em `http://localhost:8000/docs`

_Fim do roteiro. Tempo estimado: 20 minutos._

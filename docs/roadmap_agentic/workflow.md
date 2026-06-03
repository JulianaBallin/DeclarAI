# Workflow Agentico — DeclaraAI

Descricao do fluxo agentico do sistema DeclaraAI como Micro SaaS com Agentic RAG,
atendendo aos requisitos tecnicos da atividade academica.

---

## Visao Geral

O DeclaraAI implementa a abordagem **Agentic RAG** (Opcao A da atividade): um LLM com
comportamento de agente que decide quando consultar a base de conhecimento, quais ferramentas
utilizar, como decompor perguntas complexas e como validar as respostas geradas.

O dominio de aplicacao e a declaracao do Imposto de Renda Pessoa Fisica (IRPF) brasileiro,
com foco em contribuintes pessoas fisicas que precisam organizar documentos, entender
deducoes e preencher a declaracao anual.

---

## 1. Base de Conhecimento

O projeto possui base de conhecimento propria construida a partir de documentos do dominio fiscal.

### Documentos indexados

| Arquivo | Tipo | Relevancia |
|---------|------|------------|
| `guia_imposto_renda.txt` | TXT | Regras gerais do IRPF, deducoes e obrigatoriedade |
| `pr-irpf-2024.pdf` | PDF | Perguntas e respostas oficiais da Receita Federal 2024 |

**Justificativa:** Esses documentos cobrem as principais duvidas dos contribuintes sobre
deducoes medicas, educacionais, previdencia privada, alugueis e rendimentos tributaveis.
Sao fontes primarias da Receita Federal, garantindo precisao e confiabilidade.

O sistema tambem aceita documentos do usuario (recibos, notas fiscais, informes de rendimentos)
que sao processados, classificados e indexados para consulta personalizada.

---

## 2. Ingestao e Pre-processamento

### Pipeline de ingestao

```
Documento do usuario
       |
   [Loader] -- detecta formato (PDF, TXT, HTML, XML, JPG/PNG)
       |
   [Extrator de texto] -- parse estruturado por tipo
       |    * PDF: PyMuPDF + pdfplumber
       |    * HTML: BeautifulSoup
       |    * XML (NF-e): parser especifico com namespaces
       |    * Imagem: Tesseract OCR (pytesseract)
       |
   [Limpeza textual] -- remove cabecalhos/rodapes, normaliza espacos,
       |                remove caracteres de controle
       |
   [Tratamento de metadados] -- extrai emitente, CNPJ, data, valor, CPF
       |
   [Chunker] -- divide em trechos conforme estrategia configurada
       |
   [Embedder] -- gera vetor semantico por chunk
       |
   [VectorStore] -- salva no ChromaDB com metadados
```

### Estrategia de chunking

Configuracao padrao (ajustavel via `.env`):

| Parametro | Valor padrao | Justificativa |
|-----------|-------------|---------------|
| `CHUNK_SIZE` | 600 tokens | Preserva contexto suficiente sem exceder janela do LLM |
| `CHUNK_OVERLAP` | 80 tokens | Evita cortar ideias no limite entre chunks |

Separadores priorizados: `\n\n` (paragrafos), `\n` (linhas), ` ` (palavras).

---

## 3. Ferramentas do Agente

O agente possui as seguintes ferramentas, acionadas conforme o tipo de pergunta:

### Ferramenta 1: busca_vetorial

**Quando usar:** Perguntas abertas sobre regras do IRPF, duvidas sobre deducoes,
interpretacao de legislacao fiscal.

**Como funciona:** Converte a pergunta em vetor via sentence-transformers e busca
os K chunks mais semanticamente similares no ChromaDB (cosine similarity).

**Parametros:** `top_k=5`, `score_threshold=0.3`

### Ferramenta 2: busca_documento_usuario

**Quando usar:** O usuario faz perguntas sobre documentos que ele proprio enviou
("qual foi o valor do meu recibo medico?", "meu plano de saude e dedutivel?").

**Como funciona:** Filtra o ChromaDB por metadados do usuario (session_id ou CPF)
antes de realizar a busca semantica.

### Ferramenta 3: classificar_documento

**Quando usar:** O usuario envia um novo documento para analise.

**Como funciona:** Envia o texto extraido ao LLM com prompt estruturado. O LLM
retorna JSON com tipo, categoria IRPF, dedutibilidade, motivo e confianca.
Se o LLM falhar ou retornar JSON invalido, o servico de regras atua como fallback.

**Saida esperada:**
```json
{
  "tipo_documento": "NF-e",
  "categoria_irpf": "despesa_saude",
  "dedutivel": true,
  "motivo": "Nota fiscal de consulta medica, dedutivel sem limite",
  "confianca": 0.95,
  "origem": "llm"
}
```

### Ferramenta 4: consulta_banco_dados

**Quando usar:** Perguntas sobre historico de documentos salvos, totais por categoria,
resumo anual para a declaracao.

**Como funciona:** Gera e executa queries SQL no banco SQLite local (declaraai.db)
com os documentos salvos pelo usuario.

### Ferramenta 5: gerar_justificativa

**Quando usar:** Apos classificar um documento, o agente enriquece a resposta com
contexto da base de conhecimento sobre as regras de deducao aplicaveis.

**Como funciona:** Combina o resultado da classificacao com chunks relevantes
recuperados da base de conhecimento, depois envia ao LLM para gerar uma justificativa
clara e contextualizada para o usuario.

### Ferramenta 6: verificar_titularidade

**Quando usar:** Antes de classificar um documento como dedutivel, verifica se o
beneficiario do documento corresponde ao declarante ou a um dependente.

**Como funciona:** Compara o nome extraido do documento com o nome do declarante
registrado na sessao. Retorna status: `titular`, `provavel_dependente` ou `terceiro`.

---

## 4. Fluxo de Decisao do Agente

### 4.1 Fluxo para perguntas do chat (RAG classico)

```
Usuario faz pergunta
         |
   [Saudacao/small-talk?] --> Resposta local imediata (sem LLM)
         |
   [Pergunta sobre IR]
         |
   [busca_vetorial] -- recupera top-5 chunks relevantes
         |
   [Chunks encontrados?]
      Sim --> [Gera resposta com contexto] --> Exibe resposta + fontes
      Nao --> [Indica ausencia de informacao] --> Sugere reformular
```

### 4.2 Fluxo para upload de documentos (pipeline Agentic)

```
Usuario envia arquivo
         |
   [Loader + Extrator] -- detecta formato, extrai texto
         |
   [classificar_documento] -- LLM-first com fallback por regras
         |
   [verificar_titularidade] -- compara com perfil do declarante
         |
   [busca_vetorial] -- recupera regras de deducao aplicaveis
         |
   [gerar_justificativa] -- LLM combina classificacao + contexto RAG
         |
   [Formulario de confirmacao] -- usuario revisa e corrige dados
         |
   [Salvar + indexar] -- persiste no SQLite e re-indexa no ChromaDB
```

### 4.3 Fluxo para resumo anual

```
Usuario solicita resumo do ano X
         |
   [consulta_banco_dados] -- busca todos os documentos do ano
         |
   [Agrupa por categoria tributaria]
         |
   [Calcula totais] -- soma valores por categoria
         |
   [Aplica regras de limite] -- verifica limites IRPF (saude, educacao)
         |
   [Exibe dashboard] -- metricas, alertas de limite, lista por categoria
```

---

## 5. Modelo de Linguagem

O sistema usa exclusivamente modelos **open-source via Ollama** (execucao local).

**Modelo padrao:** `mistral` (4.1 GB)

**Justificativa da escolha:**
- Bom equilibrio entre qualidade e custo computacional
- Funciona em hardware convencional (8 GB RAM)
- Boa compreensao de portugues
- Suporte a saida estruturada JSON (formato necessario para classificacao)
- Zero dependencia de API externa: dados sensiveis nao saem da maquina

**Modelos alternativos testados:**

| Modelo | Tamanho | Perfil |
|--------|---------|--------|
| `llama3.2:3b` | 2.0 GB | Mais leve, adequado para hardware mais modesto |
| `phi4-mini` | 2.5 GB | Excelente em saida estruturada |
| `gemma3:4b` | 3.3 GB | Forte em raciocinio |
| `qwen2.5:7b` | 4.7 GB | Melhor suporte a portugues e multiplos idiomas |

---

## 6. Geracao de Respostas

O LLM gera respostas seguindo as seguintes diretrizes (definidas no system prompt):

1. **Coerencia:** Respostas baseadas exclusivamente nos documentos recuperados
2. **Resposta direta:** Enderedaca a pergunta especifica sem digrassoes
3. **Anti-alucinacao:** Se a informacao nao estiver no contexto, o LLM indica claramente
4. **Citacao de fontes:** Menciona os documentos utilizados quando relevante
5. **Aviso legal:** Lembra que o sistema nao substitui orientacao de contador

**Template do prompt (resumido):**
```
Voce e um assistente especializado em IRPF brasileiro.
Use APENAS as informacoes do contexto abaixo para responder.
Se a informacao nao estiver no contexto, diga que nao sabe.

Contexto:
{chunks_recuperados}

Pergunta do usuario: {pergunta}
```

---

## 7. Interface

O sistema possui interface web construida com **Streamlit**, acessivel via navegador.

**Abas disponiveis:**

| Aba | Funcao |
|-----|--------|
| Chat | Perguntas em linguagem natural respondidas pelo pipeline RAG |
| Upload | Envio e processamento automatico de documentos fiscais |
| Base de Conhecimento | Gerenciamento dos documentos de referencia |
| Historico | Consulta e filtragem dos documentos salvos |
| Resumo Anual | Visao consolidada por categoria tributaria |
| Avaliacao | Metricas quantitativas do pipeline RAG |

A API REST documentada esta disponivel em `http://localhost:8000/docs` (Swagger UI).

---

## 8. Avaliacao do Sistema

### 8.1 Metricas implementadas

| Metrica | Descricao |
|---------|-----------|
| Taxa de Recuperacao | % de perguntas com ao menos 1 chunk recuperado |
| Score Medio de Contexto | Similaridade cosseno media dos chunks retornados |
| Cobertura de Keywords | % de termos esperados presentes na resposta gerada |

### 8.2 Plano de avaliacao futura (RAGAS)

Para o artigo academico, serao implementadas metricas RAGAS completas:

- **Faithfulness:** Respostas estao apoiadas no contexto?
- **Answer Relevancy:** Respostas enderedacam as perguntas?
- **Context Precision:** Chunks relevantes chegam no topo?
- **Context Recall:** Toda informacao necessaria foi recuperada?

O RAGAS sera configurado com Ollama local como juiz, sem custo de API externa.

### 8.3 Limitacoes conhecidas

1. **Dependencia do Ollama:** O sistema requer Ollama rodando localmente
2. **Latencia:** Geracao de resposta pode levar 10-30 segundos dependendo do hardware
3. **Idioma:** Modelos menores tem qualidade reduzida em portugues vs ingles
4. **OCR:** Imagens com baixa qualidade podem ter extracao imprecisa
5. **Dataset de avaliacao:** O dataset de perguntas de referencia ainda e pequeno (8 casos)

---

## 9. Privacidade e LGPD

O DeclaraAI implementa **privacy-by-design**:

- Ollama roda o modelo no proprio computador do usuario
- ChromaDB armazena os vetores localmente
- SQLite armazena o banco local
- **Nenhum documento e nenhuma pergunta saem da maquina**

Isso e especialmente relevante para o contexto de IRPF, onde os documentos contem
dados sensiveis protegidos pela LGPD (Lei 13.709/2018, Art. 5, II): CPF, renda anual,
dados bancarios, informacoes de saude e dados de dependentes.

---

## 10. Arquitetura Tecnica

### Stack

| Componente | Tecnologia | Justificativa |
|-----------|------------|---------------|
| Backend | FastAPI (Python) | Performance, tipagem forte, Swagger auto-gerado |
| Frontend | Streamlit | Rapido para prototipo; React planejado para versao final |
| LLM | Ollama (local) | Execucao local, sem custo de API, privacidade |
| Vector Store | ChromaDB | Leve, embutido, sem servidor separado |
| Banco de dados | SQLite | Zero configuracao, suficiente para uso individual |
| Embedding | sentence-transformers | Modelos abertos, execucao local |
| OCR | Tesseract | Open-source, suporte a portugues |

### Diagrama simplificado

```
[Usuario]
    |
[Interface Web - Streamlit / React]
    |
[API REST - FastAPI]
    |
    +---> [RAG Service]
    |           |
    |     [Retriever] <--> [ChromaDB (vetores)]
    |           |
    |     [Generator] <--> [Ollama (LLM local)]
    |
    +---> [Document Service]
    |           |
    |     [Loader + Chunker + Embedder]
    |           |
    |     [Classification Service (LLM-first + fallback)]
    |
    +---> [History Service] <--> [SQLite]
    |
    +---> [Knowledge Service] <--> [Base de conhecimento (PDF/TXT)]
```

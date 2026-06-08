# Roteiro de Demonstração DeclarAI

Este roteiro prepara o ambiente e orienta uma demonstração curta, com duração máxima de 5 minutos. A ideia é mostrar primeiro que o sistema está inteiro e funcionando, depois destacar as partes de maior valor: Chat RAG, upload fiscal, classificação, titularidade, justificativa, histórico e avaliação.

## 1. Preparação do Ambiente

Execute estes comandos antes da apresentação. Eles sobem a aplicação completa com Docker.

```bash
cd /home/cronos-1226/Documentos/uea/DeclarAI
git checkout develop
git pull origin develop
docker compose up -d --build
docker exec declarai-ollama ollama pull mistral
```

Confirme se os serviços estão no ar.

```bash
docker compose ps
curl -s -I http://localhost:3000
curl -s http://localhost:8000/ | python3 -m json.tool
curl -s http://localhost:8000/status | python3 -m json.tool
```

Observação: se o Docker marcar o front-end como `unhealthy`, mas `curl -s -I http://localhost:3000` retornar `HTTP/1.1 200 OK`, a interface está servindo normalmente. No ambiente testado, o healthcheck interno do Nginx tentou resolver `localhost` por IPv6, mas a página abriu corretamente pela porta publicada no host.

Re-indexe a base de conhecimento antes da demo.

```bash
curl -s -X POST http://localhost:8000/ingest | python3 -m json.tool
```

Aqueça o modelo com uma pergunta curta. Isso reduz a chance de a primeira chamada ao LLM demorar durante a apresentação.

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"pergunta":"Curso de inglês é dedutível como educação?"}' \
  | python3 -m json.tool
```

Rode a mesma pergunta uma segunda vez. A primeira execução pode baixar e carregar embeddings, CrossEncoder e Mistral; no teste, a segunda chamada respondeu em cerca de 4 segundos.

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"pergunta":"Curso de inglês é dedutível como educação?"}' \
  | python3 -m json.tool
```

Abra as páginas que serão usadas.

```bash
xdg-open http://localhost:3000
xdg-open http://localhost:8000/docs
```

Para a demo de 5 minutos, processe o upload principal uma vez pelo navegador antes da apresentação e deixe o resultado aberto na tela `Upload`. No teste em CPU, o upload com classificação e justificativa levou cerca de 2 minutos; mostrar o resultado já processado preserva tempo para explicar valor técnico.

## 2. Plano B Local

Use esta alternativa apenas se o Docker falhar.

Terminal 1, back-end:

```bash
cd /home/cronos-1226/Documentos/uea/DeclarAI
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir backend
```

Terminal 2, Ollama:

```bash
ollama serve
ollama pull mistral
```

Terminal 3, front-end:

```bash
cd /home/cronos-1226/Documentos/uea/DeclarAI/frontend
npm install
npm run dev -- --host 0.0.0.0
```

URLs locais no plano B:

- Front-end: `http://localhost:5173`
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

## 3. Arquivos para a Demo

Use estes documentos fictícios. Eles já estão no repositório e foram criados para simular casos reais de IRPF.

| Caso | Arquivo | O que mostrar |
|---|---|---|
| Pergunta difícil | Chat, sem arquivo | Curso de inglês não é dedutível |
| Upload principal | `data/test_documents/simulation/05_recibo_dentista_pedro.txt` | Recibo Médico, dedução saúde, valor, titularidade e justificativa |
| Titularidade | Swagger ou comando `verificar-titularidade` | Pedro como dependente provável |
| Upload alternativo | `data/test_documents/simulation/10_mensalidade_pedro_henrique.pdf` | educação (pode classificar como não identificado — evitar na demo ao vivo) |
| Caso de alerta | `data/test_documents/simulation/07_gasto_nao_dedutivel_roupa.txt` | gasto não dedutível |
| Base de conhecimento | `data/knowledge_base/guia_imposto_renda.txt` e `data/knowledge_base/pr-irpf-2024.pdf` | documentos próprios do domínio |

Perfil para registrar na tela de upload:

```text
Nome: Ana Clara Rodrigues Nascimento
CPF: 071.234.567-18
```

## 4. Roteiro de 5 Minutos

### 0:00 a 0:30 | Abertura

Tela: `Status`

Mostre:

- RAG inicializado;
- quantidade de chunks indexados;
- modelo LLM;
- disponibilidade do Ollama.

Fala sugerida:

> "O DeclarAI é um Micro SaaS acadêmico para apoiar contribuintes na organização da declaração de IRPF. A ideia não é substituir um contador, mas reduzir erros comuns usando uma base fiscal própria, LLM aberto e execução local."

### 0:30 a 1:00 | Visão Geral do Sistema

Tela: navegação superior.

Mostre rapidamente as abas:

- Chat;
- Upload;
- Base de Conhecimento;
- Histórico;
- Avaliação;
- Status.

Fala sugerida:

> "A aplicação está dividida pelos fluxos principais do usuário. A pessoa pode consultar regras, enviar documentos, revisar classificações, salvar no histórico e avaliar a qualidade do RAG."

### 1:00 a 2:00 | Chat RAG com Pergunta Difícil

Tela: `Chat`

Pergunta:

```text
Curso de inglês é dedutível como educação?
```

Mostre:

- resposta restritiva;
- fontes consultadas;
- quantidade de trechos;
- score médio.

Fala sugerida:

> "Aqui a pergunta é boa para testar alucinação, porque curso de idioma parece educação, mas não entra como despesa dedutível. O agente recupera contexto da base e responde de forma conservadora, mostrando fontes e score."

### 2:00 a 3:15 | Upload Fiscal e Agentic RAG

Tela: `Upload`

Passos:

1. Registre o perfil da declarante:

```text
Ana Clara Rodrigues Nascimento
071.234.567-18
```

2. Envie o arquivo:

```text
data/test_documents/simulation/05_recibo_dentista_pedro.txt
```

3. Se a tela já estiver pré-processada, mostre o resultado diretamente. Se decidir processar ao vivo, avise que essa etapa aciona o LLM local e pode levar perto de 2 minutos em CPU.
4. Mostre os campos extraídos. **Destaque Tipo do documento (Recibo), Natureza (Saúde) e Situação no IRPF** — mesmo que o badge de categoria venha genérico, esses campos refletem o caso odontológico.
5. Mostre valor, emitente, referência IRPF (código 10 - Dentista) e justificativa enriquecida.

Fala sugerida:

> "Este é o trecho mais agentic da aplicação. O upload aciona várias ferramentas: extração do texto, classificação LLM-first com fallback por regras, verificação de titularidade e uma justificativa gerada com outro ciclo RAG. O recibo de dentista classifica como despesa médica dedutível e o paciente Pedro aparece como dependente provável."

Fala para a justificativa:

> "Mesmo quando a categoria técnica exige revisão, a interface mostra a natureza do documento, a situação no IRPF e uma justificativa apoiada pela base fiscal. A revisão humana continua no centro, mas agora com contexto."

Mostre titularidade logo depois pelo Swagger em `POST /declarante/verificar-titularidade` ou pelo comando abaixo:

```bash
curl -s -X POST "http://localhost:8000/declarante/verificar-titularidade?nome_beneficiario=Pedro%20Henrique%20Rodrigues%20Nascimento" \
  | python3 -m json.tool
```

Fala para titularidade:

> "O documento está em nome de Pedro, não de Ana. O sistema percebe sobrenome em comum e marca como dependente provável. Isso é importante porque despesa de terceiro não dependente não pode ser deduzida."

Se o tempo permitir:

6. Marque a confirmação.
7. Clique em `Salvar Documento`.

### 3:15 a 4:00 | Histórico e Resumo Anual

Tela: `Histórico`

Mostre:

- documento salvo;
- agrupamento por categoria;
- resumo anual;
- deduções e economia estimada.

Fala sugerida:

> "Depois da revisão humana, o documento entra no histórico. A proposta é ajudar o contribuinte a organizar comprovantes ao longo do ano e chegar na declaração com os documentos separados por categoria."

### 4:00 a 4:35 | Base de Conhecimento

Tela: `Base de Conhecimento`

Mostre:

- arquivos da base;
- chunks indexados;
- opção de re-indexar com chunking 600/80.

Fala sugerida:

> "A base é própria e ligada ao domínio fiscal. Ela combina um guia resumido com perguntas e respostas oficiais da Receita Federal. A interface também permite ampliar a base e re-indexar os vetores."

### 4:35 a 5:00 | Avaliação e Fechamento

Tela: `Avaliação`

Mostre:

- avaliação rápida de recuperação;
- avaliação de recuperação;
- comparação entre Mistral com RAG e sem RAG;
- botão de avaliação completa.

Fala sugerida:

> "A avaliação fecha o ciclo técnico. Não é só uma interface bonita. O projeto mede recuperação, score de contexto e cobertura de palavras-chave. O Mistral com RAG teve cobertura melhor que o LLM sem recuperação, mostrando o ganho da arquitetura."

Fechamento:

> "Em resumo, o DeclarAI atende ao requisito de Agentic RAG porque o LLM não só responde perguntas. Ele participa de um fluxo com ferramentas, documentos, classificação, titularidade, justificativa e avaliação."

## 5. Comandos de Teste do Fluxo

Use estes comandos para validar a demo sem depender do navegador.

Health check:

```bash
curl -s http://localhost:8000/ | python3 -m json.tool
```

Status:

```bash
curl -s http://localhost:8000/status | python3 -m json.tool
```

Base de conhecimento:

```bash
curl -s http://localhost:8000/knowledge/files | python3 -m json.tool
```

Chat RAG:

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"pergunta":"Curso de inglês é dedutível como educação?"}' \
  | python3 -m json.tool
```

Perfil da declarante:

```bash
curl -s -X POST http://localhost:8000/declarante/perfil \
  -H "Content-Type: application/json" \
  -d '{"nome_completo":"Ana Clara Rodrigues Nascimento","cpf":"071.234.567-18"}' \
  | python3 -m json.tool
```

Upload de documento principal:

```bash
curl -s -X POST http://localhost:8000/documents/upload \
  -F "arquivo=@data/test_documents/simulation/05_recibo_dentista_pedro.txt" \
  | python3 -m json.tool
```

Titularidade:

```bash
curl -s -X POST "http://localhost:8000/declarante/verificar-titularidade?nome_beneficiario=Pedro%20Henrique%20Rodrigues%20Nascimento" \
  | python3 -m json.tool
```

Histórico:

```bash
curl -s http://localhost:8000/history | python3 -m json.tool
curl -s http://localhost:8000/history/summary | python3 -m json.tool
```

Avaliação de recuperação:

```bash
curl -s -X POST http://localhost:8000/evaluation/recuperacao \
  | python3 -m json.tool
```

## 6. Cuidados Antes da Apresentação

- Rode o aquecimento do chat antes da banca.
- Rode o upload principal uma vez no navegador antes da banca e deixe o resultado aberto.
- Deixe o navegador já aberto em `http://localhost:3000`.
- Evite executar `docker compose up --build` durante os 5 minutos.
- Evite rodar avaliação completa ao vivo, pois ela pode demorar.
- Se o chat demorar, continue mostrando Upload, Histórico e Avaliação.
- Se o Ollama estiver indisponível, mostre que a aplicação detecta isso em `Status`.
- Se o upload de imagem demorar por OCR, use o recibo de dentista em `.txt` (upload principal).
- Evite o PDF de mensalidade escolar na demo ao vivo: ele pode classificar como "Documento Não Classificado".
- O backend aceita `.txt` no upload — não é necessário converter o recibo de dentista para PDF.
- Se precisar de um caso com classificação categórica muito explícita no badge, use `07_gasto_nao_dedutivel_roupa.txt` (Nota Fiscal / Não dedutível) como contraste rápido.

## 7. Frases de Valor para Usar Durante a Demo

- "O sistema foi desenhado para rodar localmente e reduzir exposição de dados sensíveis."
- "O RAG ajuda a responder com base documental, não apenas com conhecimento geral do modelo."
- "A classificação LLM-first melhora flexibilidade, mas o fallback por regras mantém segurança."
- "A titularidade evita um erro comum: tentar deduzir despesa de alguém que não é dependente."
- "A avaliação mostra que o ganho do RAG foi medido, não apenas presumido."
- "O histórico transforma uma consulta pontual em organização contínua para a declaração."

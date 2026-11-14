# SaveToken API

O SaveToken é uma aplicação web de propósito geral que converte PDFs compatíveis para Markdown, preservando conteúdo e estrutura e oferecendo uma otimização conservadora para facilitar o processamento por ferramentas de inteligência artificial.

O backend usa FastAPI, Docling, pypdf, Pydantic e tiktoken. Não utiliza banco de dados, autenticação, filas ou armazenamento permanente de documentos no MVP.

## Modos de conversão

- `faithful` (padrão): retorna o Markdown exportado pelo Docling, sem resumo, paráfrase ou limpeza agressiva.
- `optimized`: parte do mesmo `DoclingDocument`, tenta exportar tabelas compactas e aplica normalização segura de espaço em branco. Um candidato só é aceito quando preserva todos os caracteres não brancos do Markdown fiel e reduz tokens; caso contrário, o Markdown fiel é mantido.

O SaveToken é genérico para PDFs acadêmicos, científicos, técnicos, empresariais, educacionais, jurídicos e outros documentos compatíveis com o Docling.

## Estrutura

```text
app/
├── main.py
├── api/routes/conversion.py
├── core/config.py
├── exceptions/handlers.py
├── schemas/conversion.py
└── services/
    ├── conversion_service.py
    ├── file_validation_service.py
    ├── markdown_optimization_service.py
    ├── pdf_conversion_service.py
    └── token_count_service.py
tests/
```

## Requisitos

- Docker Desktop, recomendado para o ambiente completo.
- Python 3.12 e pip, apenas se for executar testes ou a API fora do Docker.

O Docling pode carregar dependências e modelos adicionais. Por isso, o primeiro build pode ser grande e demorar. Não é necessário instalar as dependências no host quando a API for executada pelo Docker.

## Executar com Docker

Na pasta `SaveToken-api`:

```bash
docker build -t savetoken-api .
docker run --rm -p 8000:8000 savetoken-api
```

A API ficará disponível em `http://localhost:8000` e o Swagger em `http://localhost:8000/docs`.

## Configuração

As configurações podem ser definidas por variáveis de ambiente:

| Variável | Padrão | Finalidade |
|---|---:|---|
| `MAX_PDF_SIZE_MB` | `10` | Tamanho máximo do PDF |
| `MAX_PDF_PAGES` | `1000` | Número máximo de páginas |
| `MAX_CONCURRENT_CONVERSIONS` | `1` | Conversões pesadas simultâneas por instância |
| `TOKENIZER_ENCODING` | `cl100k_base` | Encoding usado na estimativa |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Origens explícitas separadas por vírgula |

Os PDFs não são armazenados permanentemente pela aplicação. O nome enviado pelo cliente é usado apenas como nome de download, depois de sanitizado; não é usado para criar caminhos no servidor.

## Endpoint

### `POST /api/v1/conversions`

Envia um formulário `multipart/form-data` com:

- `pdf`: arquivo PDF obrigatório;
- `mode`: `faithful` ou `optimized`, opcional, padrão `faithful`.

Exemplo:

```bash
curl -X POST "http://localhost:8000/api/v1/conversions" \
  -F "pdf=@documento.pdf" \
  -F "mode=optimized" \
  -o resultado.md
```

A resposta é o arquivo Markdown com `Content-Type: text/markdown` e `Content-Disposition: attachment`. Métricas são disponibilizadas nos cabeçalhos `X-SaveToken-*`, incluindo tokenizer, tokens antes/depois, diferença e percentual de redução.

`POST /convert` permanece disponível temporariamente como rota de compatibilidade, mas `/api/v1/conversions` é a rota canônica.

## Fluxo

```text
Upload → validação → Docling → Markdown fiel → otimização opcional
       → candidatos seguros → contagem de tokens → download .md
```

A validação verifica nome, extensão, MIME informado, assinatura `%PDF-`, tamanho real, integridade básica, criptografia e quantidade de páginas. O MIME é tratado como informação fornecida pelo cliente, por isso a assinatura e o parsing com pypdf também são necessários.

No modo `optimized`, o Docling é executado uma única vez. O Markdown fiel é exportado e, quando a versão instalada oferece suporte, uma segunda representação é obtida do mesmo documento com `compact_tables=True`. A normalização preserva blocos de código, fórmulas, HTML, código indentado e quebras de linha explícitas. Candidatos são comparados por uma impressão digital dos caracteres não brancos e selecionados pelo menor número de tokens.

As métricas usam `tiktoken` com o encoding configurado (`cl100k_base` por padrão). A economia varia conforme o documento e o encoding e não representa uma contagem universal para todos os modelos.

O `DocumentConverter.convert()` é síncrono e potencialmente pesado. Ele é executado em thread pool e limitado inicialmente a uma conversão simultânea por instância. Esse limite em memória não coordena múltiplos workers ou réplicas.

## Testes

Com Docker, os testes podem ser executados montando o repositório e usando a imagem de desenvolvimento, ou localmente com Python 3.12:

```bash
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
.venv\Scripts\activate          # Windows PowerShell
pip install -r requirements.txt
pytest -q
```

Os testes unitários usam mocks para o Docling quando possível. O teste de integração com o Docling real deve ser executado em um ambiente que tenha todas as dependências instaladas; ele não deve depender de serviços externos de IA.

## Limitações conhecidas

- OCR não é garantido para PDFs sem texto selecionável.
- A contagem de tokens depende do encoding configurado e não é universal para todos os modelos.
- A contagem compara o Markdown fiel com o Markdown final; não mede diretamente o tamanho do PDF original.
- O Docling pode baixar modelos ou recursos conforme a versão e o formato processado. Esse comportamento deve ser observado no primeiro build e considerado no deploy.
- Limites de memória, CPU, timeout e tamanho de requisição do proxy devem ser configurados também na infraestrutura.

## Privacidade e segurança

O MVP não envia documentos para serviços externos de IA e não registra o conteúdo integral dos arquivos. Em produção, use CORS com origens explícitas, limites de proxy e políticas de retenção compatíveis com os documentos processados.

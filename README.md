# SaveToken

> **Status:** Em desenvolvimento

## 1. Nome e apresentação do projeto

O **SaveToken** é um projeto open source voltado à conversão de documentos PDF para Markdown (`.md`) com foco em uso técnico por modelos de inteligência artificial.

## 2. Objetivo e problema que pretende resolver

Documentos jurídicos e acadêmicos extensos costumam apresentar ruído de formatação, estrutura inconsistente e alto volume de tokens, dificultando sua utilização em fluxos com IA.

O SaveToken busca oferecer um processo transparente para:

- converter PDF em Markdown;
- preservar estrutura lógica e conteúdo relevante;
- permitir contagem estimada de tokens antes e depois da otimização.

Público-alvo inicial: estudantes, pesquisadores, desenvolvedores e profissionais que trabalham com documentos longos.

## 3. Funcionalidades planejadas

- Upload de documentos PDF.
- Conversão de PDF para Markdown.
- Dois modos de conversão: `faithful` e `optimized`.
- Download do resultado em arquivo `.md`.
- Preservação de títulos, parágrafos, artigos, incisos e referências jurídicas.
- Tratamento de cabeçalhos e rodapés repetitivos.
- Suporte a documentos acadêmicos e jurídicos extensos.
- Contagem estimada de tokens.
- Suporte futuro a múltiplos arquivos por envio.
- Suporte futuro a divisão de documentos em chunks.

## 4. Tecnologias utilizadas e planejadas

### Backend (este repositório)

- Python 3.12+
- FastAPI
- Docling
- pypdf
- Pydantic
- tiktoken
- pytest
- Docker
- Microsoft Azure (hospedagem planejada)

### Frontend (repositório separado)

- Next.js
- TypeScript
- SCSS
- Cloudflare Pages

> Observação: na primeira versão, não há uso planejado de banco de dados.

## 5. Arquitetura e estrutura de diretórios

Estrutura planejada do backend:

```text
toknix-api/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── routes/
│   │       └── conversion.py
│   ├── models/
│   │   ├── document.py
│   │   └── conversion_result.py
│   ├── schemas/
│   │   └── conversion.py
│   ├── services/
│   │   ├── conversion_service.py
│   │   ├── pdf_conversion_service.py
│   │   ├── markdown_optimization_service.py
│   │   ├── file_validation_service.py
│   │   └── token_count_service.py
│   ├── core/
│   │   └── config.py
│   └── exceptions/
│       └── handlers.py
├── tests/
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

### Responsabilidade de cada módulo

- `app/main.py`: ponto de entrada da aplicação FastAPI e inicialização do app.
- `app/api/routes/conversion.py`: definição dos endpoints de conversão.
- `app/models/`: modelos de domínio usados internamente.
- `app/schemas/conversion.py`: contratos de entrada/saída para validação e serialização.
- `app/services/conversion_service.py`: orquestração do fluxo completo de conversão.
- `app/services/pdf_conversion_service.py`: extração e transformação de conteúdo PDF para Markdown.
- `app/services/markdown_optimization_service.py`: limpeza e otimização do Markdown para consumo por IA.
- `app/services/file_validation_service.py`: validação de arquivo (tipo, tamanho e regras iniciais).
- `app/services/token_count_service.py`: estimativa de tokens por tokenizer/modelo selecionado.
- `app/core/config.py`: configuração central da aplicação e variáveis de ambiente.
- `app/exceptions/handlers.py`: tratamento padronizado de erros.
- `tests/`: testes automatizados.

## 6. Fluxo de conversão

Fluxo planejado de alto nível:

1. Receber upload do arquivo PDF.
2. Validar arquivo (tipo e limites definidos).
3. Extrair conteúdo e converter para Markdown base.
4. Aplicar modo selecionado (`faithful` ou `optimized`).
5. Calcular contagem estimada de tokens (antes/depois, quando aplicável).
6. Retornar arquivo `.md` para download.

## 7. Modos `faithful` e `optimized`

### `faithful`

Conversão fiel ao documento original, priorizando preservação de conteúdo e estrutura lógica.

### `optimized`

Conversão com limpeza de ruídos e remoção de elementos redundantes para facilitar consumo por IA, sem resumir ou alterar informações relevantes.

> Importante: conversão para Markdown não garante, por si só, economia de tokens. A economia deve ser mensurada e exibida de forma transparente.

## 8. Requisitos de instalação

Requisitos planejados para desenvolvimento local:

- Python 3.12+
- pip
- Docker (opcional para execução conteinerizada)

## 9. Configuração do ambiente de desenvolvimento

Exemplo planejado de setup local:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

Configurar variáveis de ambiente a partir de `.env.example` quando o arquivo estiver disponível no projeto.

## 10. Exemplo planejado de utilização da API

Endpoint principal planejado:

- `POST /api/v1/conversions`

Entrada esperada:

- `file`: arquivo PDF
- `mode`: `faithful` ou `optimized`

Saída esperada:

- Arquivo Markdown (`.md`)

Exemplo de chamada (planejado):

```bash
curl -X POST "http://localhost:8000/api/v1/conversions" \
  -F "file=@documento.pdf" \
  -F "mode=faithful" \
  -o resultado.md
```

### Erros previstos (alto nível)

Como os contratos formais ainda não foram definidos, os erros abaixo representam categorias esperadas:

- Erros de validação de entrada (arquivo ausente, formato inválido, modo inválido, limite excedido).
- Erros de processamento/conversão (falhas ao ler PDF ou ao gerar Markdown).
- Erros internos inesperados.

## 11. Roadmap do MVP

- [ ] Estruturar backend FastAPI.
- [ ] Implementar endpoint de conversão (`/api/v1/conversions`).
- [ ] Implementar modo `faithful`.
- [ ] Implementar modo `optimized`.
- [ ] Implementar contagem estimada de tokens.
- [ ] Definir limites e estratégia de tratamento de erros.
- [ ] Adicionar testes automatizados prioritários.
- [ ] Preparar imagem Docker para execução.
- [ ] Publicar primeira versão do backend.

## 12. Testes e critérios de qualidade

Critérios planejados:

- Testes com `pytest` para serviços e rotas críticas.
- Validação de cenários de erro (arquivo inválido, limites excedidos, falhas de conversão).
- Verificação da preservação estrutural em documentos jurídicos e acadêmicos.
- Avaliação transparente da estimativa de tokens no fluxo de conversão.

## 13. Segurança e privacidade dos documentos

Diretrizes iniciais:

- Processar apenas os arquivos enviados para conversão.
- Limitar tamanho de upload e volume de processamento no MVP.
- Evitar retenção desnecessária de arquivos.
- Evoluir políticas de privacidade e retenção conforme o projeto amadurecer.

Limites iniciais propostos (provisórios):

- Até 10 MB por PDF.
- Até 1.000 páginas por arquivo (sujeito a testes de desempenho).
- Processamento sequencial inicialmente.
- OCR fora do escopo do primeiro MVP.

## 14. Contribuições

Contribuições serão bem-vindas após a publicação da base inicial do backend. Diretrizes formais de contribuição (ex.: `CONTRIBUTING.md`) serão adicionadas em etapas futuras.

## 15. Licenciamento

**A definir.**

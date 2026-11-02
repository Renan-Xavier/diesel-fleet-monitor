# ==============================================================================
# Dockerfile - Diesel Fleet Monitor API
# Boas práticas adotadas:
# 1. Imagem base slim para reduzir a superfície de ataque e o tamanho da imagem.
# 2. Cache de camadas aproveitando a instalação prévia de requirements.
# 3. Usuário não-root (appuser) por segurança (DevSecOps).
# 4. Variáveis de ambiente Python otimizadas para containers.
# 5. Healthcheck nativo para que o orquestrador monitore a saúde da API.
# ==============================================================================

FROM python:3.11-slim as base

# Evita que o Python gere arquivos .pyc e força o log em tempo real no console
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Define o diretório de trabalho
WORKDIR /app

# Cria um grupo e um usuário sem privilégios de root para rodar a aplicação
RUN groupadd -r appgroup && useradd -r -g appgroup -s /bin/false appuser

# Instala curl para uso no healthcheck e utilitários básicos
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependências primeiro (aproveita cache de camadas do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código-fonte da aplicação
COPY app/ ./app

# Transfere a propriedade dos arquivos para o usuário seguro
RUN chown -R appuser:appgroup /app

# Altera para o usuário não-privilegiado
USER appuser

# Documenta a porta que a aplicação escuta
EXPOSE 8000

# Healthcheck do container: orquestradores usam isso para saber se o container está saudável
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando de inicialização com Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

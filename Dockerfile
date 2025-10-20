# Use uma imagem base com Python 3.9
FROM python:3.9-slim

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto para o contêiner
COPY . .

# Atualiza o pip antes de instalar dependências
RUN pip install --upgrade pip

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta que o Flask usará
EXPOSE 8080

# Define o comando para iniciar o aplicativo
CMD ["python", "app.py"]

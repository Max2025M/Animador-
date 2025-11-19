# Usar Python 3.10 baseado no Debian Bullseye
FROM python:3.10-bullseye

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar arquivo de dependências
COPY requirements.txt .

# Atualizar pip e instalar pacotes Python
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do projeto
COPY . .

# Expor porta do Flask
EXPOSE 5000

# Comando para rodar a aplicação
CMD ["python", "app.py"]

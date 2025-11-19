# Base compatível
FROM python:3.10-bullseye

# Instala dependências essenciais do sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copia requirements
COPY requirements.txt .

# Atualiza pip
RUN pip install --upgrade pip setuptools wheel

# Instala dependências Python essenciais
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY . .

# Expõe porta do Flask
EXPOSE 5000

# Inicializa aplicação
CMD ["python", "app.py"]

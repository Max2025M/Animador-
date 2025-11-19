# Imagem base leve com Python 3.11
FROM python:3.11-slim

# Instala dependências do sistema para OpenCV, FFmpeg e MoviePy
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender1 \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copia requirements.txt
COPY requirements.txt .

# Atualiza pip e instala dependências Python
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY . .

# Expõe porta do Flask
EXPOSE 5000

# Comando para iniciar
CMD ["python", "app.py"]

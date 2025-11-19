# Use Python 3.11 slim
FROM python:3.11-slim

# Instala dependências do sistema para OpenCV e FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Define diretório de trabalho
WORKDIR /app

# Copia requirements.txt e instala Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY . .

# Expõe a porta usada pelo Flask
EXPOSE 5000

# Comando para rodar a aplicação
CMD ["python", "app.py"]

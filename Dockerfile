FROM python:3.11-slim

WORKDIR /app

# Copia e instala dependências leves
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cria pastas temporárias
RUN mkdir -p uploads outputs

# Expõe porta do Flask
EXPOSE 5000

# Roda o app
CMD ["python", "app.py"]

FROM python:3.11-slim

# Системные зависимости
RUN apt-get update && apt-get install -y \
    procps \
    psmisc \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Порт админки
EXPOSE 8501

# Запуск панели, из которой запускается бот
CMD ["streamlit", "run", "admin_panel.py", "--server.port", "8501"]
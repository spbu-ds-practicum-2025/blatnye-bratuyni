# services/booking-service/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Запускаем сервис
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]

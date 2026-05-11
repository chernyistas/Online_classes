FROM python:3.13-slim

WORKDIR /app

# Переменные окружения Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Установка системных зависимостей
RUN apt-get update \
    && apt-get install -y gcc libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Копирование и установка зависимостей
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Создание директории для медиа-файлов
RUN mkdir -p /app/media

# Копирование кода проекта
COPY . .

# Открытие порта
EXPOSE 8000


# Запуск Gunicorn (production сервер)
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000"]

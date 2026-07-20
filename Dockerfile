FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir discord.py

COPY . .

CMD ["python", "bot.py"]
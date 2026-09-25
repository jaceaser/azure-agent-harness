FROM python:3.12-slim

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir ".[foundry-hosting]"

ENV PYTHONUNBUFFERED=1
EXPOSE 8088
CMD ["python", "deploy/foundry/main.py"]

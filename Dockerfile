FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY capture/ capture/

RUN pip install --no-cache-dir .

EXPOSE 7199

CMD ["llmwiki-capture"]

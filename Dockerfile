# ContentGremlin API + pipeline (el editor Node corre como servicio aparte).
FROM python:3.12-slim

RUN apt-get update -qq \
    && apt-get install -y -qq --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV HOST=0.0.0.0 PORT=8000
EXPOSE 8000
CMD ["python", "main.py"]

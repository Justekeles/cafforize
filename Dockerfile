FROM python:3.12-slim

WORKDIR /srv/cafforize

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY run.py .

RUN mkdir -p /srv/cafforize/data
VOLUME ["/srv/cafforize/data"]

ENV HOST=0.0.0.0
ENV PORT=5544
ENV DATABASE_PATH=data/cafforize.db

EXPOSE 5544

CMD ["python", "run.py"]

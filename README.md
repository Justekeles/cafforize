# Cafforize ☕

A tiny, no-scroll web app for dialing in the perfect coffee-to-water ratio.
Enter how much water you're using, get a spoon suggestion, log what you
actually used, and grade the result afterwards. Cafforize watches which
ratios earn the best grades over time and starts suggesting those instead
of the hardcoded default (2 spoons per 1.5 units of water).

## Run locally with Python

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # optional, edit PORT/HOST/DATABASE_PATH as needed
python run.py
```

The app listens on port `5544` by default. Set `PORT` in `.env` (or as an
environment variable) to change it. Point your custom LAN hostname at this
machine's IP and everyone can just visit `http://<hostname>:<port>`.

## Run with Docker

```bash
cp .env.example .env   # optional, set PORT to change the host-side port
docker compose up --build -d
```

This builds the image locally, listens on the port from `.env` (falls back
to `5544`), and persists the SQLite database in `./data` on the host.

Without Compose:

```bash
docker build -t cafforize .
docker run -d --name cafforize -p 5544:5544 -v "$(pwd)/data:/srv/cafforize/data" cafforize
```

## How grading works

- Log a brew with the water and spoons you actually used.
- Once you've tasted it, tap the stars on that entry in the brew log (1-5).
- Once any ratio has at least two graded brews, Cafforize compares average
  grades across ratios and suggests whichever one is winning.

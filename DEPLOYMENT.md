# Deployment Guide

This project can be deployed as a small standalone API service.

## Docker

Build the image:

```bash
docker build -t zhilian-recruitment-fastapi .
```

Run the container:

```bash
docker run --rm -p 8010:8010 \
  -e HOST=0.0.0.0 \
  -e PORT=8010 \
  zhilian-recruitment-fastapi
```

Test:

```bash
curl "http://127.0.0.1:8010/health"
curl "http://127.0.0.1:8010/api/v1/zhilian/search?keyword=Python&city_code=530&page=1&page_size=2"
```

## Bare server

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8010
```

## Reverse proxy

If you put this behind Nginx or Caddy, proxy traffic to:

```text
http://127.0.0.1:8010
```

## Recommended production notes

- add request rate limiting on your reverse proxy
- cache search results for a short time window
- monitor upstream verification responses
- do not treat upstream field names as permanent

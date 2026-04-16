# Zhilian Recruitment FastAPI

Open-source `FastAPI` wrapper for Zhilian recruitment search and job detail endpoints.

This repository contains code only. It does **not** ship scraped job datasets.

[简体中文说明](./README.zh-CN.md)

## Features

- search jobs by keyword and city code
- fetch job detail by Zhilian job number
- normalize upstream fields into a cleaner recruitment schema
- expose both platform-native and generic recruitment API paths
- include built-in hot city code mappings and a live city metadata endpoint

## Endpoints

- `GET /health`
- `GET /api/v1/zhilian/search`
- `GET /api/v1/zhilian/jobs/{job_number}`
- `GET /api/v1/recruitment/feed`
- `GET /api/v1/recruitment/jobs/{job_number}`
- `GET /api/v1/meta/cities`
- `GET /api/v1/meta/city-codes`

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

Open:

```text
http://127.0.0.1:8010/docs
```

## Search example

```bash
curl "http://127.0.0.1:8010/api/v1/zhilian/search?keyword=Python&city_code=530&page=1&page_size=10"
```

## Detail example

```bash
curl "http://127.0.0.1:8010/api/v1/zhilian/jobs/CC000544460J40723865416"
```

## City code example

```bash
curl "http://127.0.0.1:8010/api/v1/meta/cities"
curl "http://127.0.0.1:8010/api/v1/meta/cities?include_districts=true"
```

## Notes

- this project wraps Zhilian web endpoints observed from the public site frontend
- upstream behavior may change at any time
- rate limiting or verification challenges may appear if requests are too frequent
- use responsibly and review the target platform's terms before production usage

## Environment variables

- `ZHILIAN_API_BASE` default: `https://fe-api.zhaopin.com`
- `ZHILIAN_PLATFORM` default: `13`
- `ZHILIAN_TIMEOUT_SECONDS` default: `20`
- `HOST` default: `0.0.0.0`
- `PORT` default: `8010`
- `RELOAD` default: `false`

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md).

## License

MIT

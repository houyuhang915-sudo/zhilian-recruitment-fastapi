# Zhilian Recruitment FastAPI

一个面向开源场景的 `FastAPI` 项目，用来封装智联招聘搜索与职位详情接口。

这个仓库只包含代码与接口封装，不附带任何抓取下来的招聘数据文件。

[English README](./README.md)

## 功能

- 按关键词和城市编码搜索职位
- 根据职位编号获取职位详情
- 将上游字段整理成更稳定的招聘信息结构
- 同时提供平台语义接口和通用招聘接口
- 内置热门城市编码表，并提供实时城市编码接口

## 接口

- `GET /health`
- `GET /api/v1/zhilian/search`
- `GET /api/v1/zhilian/jobs/{job_number}`
- `GET /api/v1/recruitment/feed`
- `GET /api/v1/recruitment/jobs/{job_number}`
- `GET /api/v1/meta/cities`
- `GET /api/v1/meta/city-codes`

## 快速启动

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

打开：

```text
http://127.0.0.1:8010/docs
```

## 搜索示例

```bash
curl "http://127.0.0.1:8010/api/v1/zhilian/search?keyword=Python&city_code=530&page=1&page_size=10"
```

## 详情示例

```bash
curl "http://127.0.0.1:8010/api/v1/zhilian/jobs/CC000544460J40723865416"
```

## 城市编码示例

```bash
curl "http://127.0.0.1:8010/api/v1/meta/cities"
curl "http://127.0.0.1:8010/api/v1/meta/cities?include_districts=true"
```

## 说明

- 这个项目封装的是智联前端页面使用的接口
- 上游行为和字段结构可能随时变化
- 请求频率过高时，可能会触发限流或验证
- 用于生产前，请自行评估目标平台条款与合规要求

## 环境变量

- `ZHILIAN_API_BASE` 默认：`https://fe-api.zhaopin.com`
- `ZHILIAN_PLATFORM` 默认：`13`
- `ZHILIAN_TIMEOUT_SECONDS` 默认：`20`
- `HOST` 默认：`0.0.0.0`
- `PORT` 默认：`8010`
- `RELOAD` 默认：`false`

## 部署

见 [DEPLOYMENT.md](./DEPLOYMENT.md)。

## 许可证

MIT

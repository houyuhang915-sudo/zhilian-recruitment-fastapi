# Zhilian Recruitment FastAPI

一个面向开源场景的 `FastAPI` 项目，用来封装智联招聘搜索、职位详情和城市编码接口。

这个仓库只包含代码与接口封装，不附带任何抓取下来的招聘数据文件。

[English README](./README.md)

## 项目定位

如果你在做：

- AI 求职助手
- 职位聚合平台
- 岗位匹配与简历分析
- 招聘信息可视化

那你通常需要一个“可以直接接”的招聘信息接口层，而不是一堆零散脚本。

这个项目就是在做这件事：

- 把智联网页前端使用的接口封装成 `FastAPI`
- 把原始字段整理成更适合业务消费的结构
- 让你可以把它当成一个独立服务部署，而不是临时脚本

## 提供的接口

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

## 使用示例

搜索职位：

```bash
curl "http://127.0.0.1:8010/api/v1/zhilian/search?keyword=Python&city_code=530&page=1&page_size=10"
```

职位详情：

```bash
curl "http://127.0.0.1:8010/api/v1/zhilian/jobs/CC000544460J40723865416"
```

城市编码：

```bash
curl "http://127.0.0.1:8010/api/v1/meta/cities"
curl "http://127.0.0.1:8010/api/v1/meta/cities?include_districts=true"
```

## 项目特点

- 搜索和详情接口分离，方便按需请求
- 提供通用招聘接口别名，方便接入自己的统一招聘层
- 内置热门城市编码表，也支持实时拉取城市元数据
- 支持 Docker 部署
- 文档中英双语

## 城市编码说明

项目内置了一份热门城市编码表，适合作为 fallback：

- [app/city_codes.py](./app/city_codes.py)

同时服务也支持从智联基础数据接口中获取更完整的城市信息，并可通过 `include_districts=true` 返回区县级编码。

## 部署

见 [DEPLOYMENT.md](./DEPLOYMENT.md)。

## 注意事项

- 这是对智联网页前端接口的封装，不是官方开放平台 SDK
- 上游字段和行为可能变化
- 请求过快可能触发验证或限流
- 用于生产前，请自行评估合规与平台条款

## 许可证

MIT

# Zhilian Recruitment FastAPI
## 智联招聘 FastAPI 封装

* * *

一个面向开源场景的招聘信息接口项目。  
它不是职位数据包，不预置抓取结果，而是把智联招聘网页前端实际使用的搜索与详情接口整理成一个更容易复用、部署和二次开发的 `FastAPI` 服务。

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
![FastAPI](https://img.shields.io/badge/FastAPI-API_Service-009688)
![Bilingual](https://img.shields.io/badge/Docs-Bilingual-blue)

中文 | [English](#english)

* * *

## 中文

很多人在做 AI 求职、职位聚合、岗位匹配或者招聘数据分析时，第一步就卡在“哪里能拿到比较稳定的职位数据”。  
直接爬页面，结构容易变；只存一份离线数据，又很快过时。于是就会陷入一种很别扭的状态：

- 想做真实招聘流，却没有一个干净的接口层
- 想接 AI 匹配，却还在手工清洗字段
- 想开源分享，却只有零散脚本，没法直接复用

这个项目就是为了解决这个尴尬点。

它把智联招聘的搜索接口、职位详情接口和城市基础数据接口封装成一个小而清晰的 `FastAPI` 服务，让你可以把它当成：

- AI 求职产品的职位数据源
- 招聘聚合系统的一个平台适配器
- 职位分析、薪资分析、技能抽取的上游接口
- 一个可以继续扩展到 BOSS、拉勾、51job 的基础模板

### 它适合谁

- 想做 AI 求职助手的人
- 想做职位聚合 API 的人
- 想研究招聘站点数据结构的人
- 想要一个可部署、可解释、可扩展的开源接口项目的人

### 这个项目做了什么

- 封装智联招聘职位搜索接口
- 封装智联招聘职位详情接口
- 提供城市编码与城市元数据接口
- 把上游原始字段整理成统一招聘结构
- 提供中英文文档
- 提供 Docker 部署方式

### 它不做什么

- 不内置抓取后的职位数据库
- 不承诺上游接口永久稳定
- 不绕过平台验证或限流机制
- 不替你处理目标平台合规问题

### 快速开始

别再手写零散脚本拼参数了，几条命令就能把服务跑起来：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

启动后打开：

```text
http://127.0.0.1:8010/docs
```

### 你会得到什么接口

- `GET /health`
- `GET /api/v1/zhilian/search`
- `GET /api/v1/zhilian/jobs/{job_number}`
- `GET /api/v1/recruitment/feed`
- `GET /api/v1/recruitment/jobs/{job_number}`
- `GET /api/v1/meta/cities`
- `GET /api/v1/meta/city-codes`

其中：

- `/api/v1/zhilian/*` 更贴近平台原始语义
- `/api/v1/recruitment/*` 更适合你接入自己的统一招聘系统
- `/api/v1/meta/*` 方便前端做城市选择器、编码映射和检索辅助

### 快速请求示例

搜索职位：

```bash
curl "http://127.0.0.1:8010/api/v1/zhilian/search?keyword=Python&city_code=530&page=1&page_size=10"
```

查看职位详情：

```bash
curl "http://127.0.0.1:8010/api/v1/zhilian/jobs/CC000544460J40723865416"
```

查看城市编码：

```bash
curl "http://127.0.0.1:8010/api/v1/meta/cities"
curl "http://127.0.0.1:8010/api/v1/meta/cities?include_districts=true"
```

### 用户侧流程（你会看到什么）

1. 先按关键词和城市获取职位列表
2. 返回结果里直接拿到职位编号、职位名、公司、薪资、经验、学历、技能标签和摘要
3. 如果需要更完整 JD，再按 `job_number` 拉职位详情
4. 详情结果里可以拿到职责、要求、公司介绍、地址和更多原始字段
5. 如果前端需要城市下拉框，可以直接调城市编码接口

### 设计原则

- 小接口层：先把“可用”做好，而不是一上来做成重平台
- 统一结构：上游字段变化时，尽量把变化挡在服务内部
- 部署友好：本地可跑，Docker 可起
- 双语文档：方便开源展示，也方便国内开发者直接上手
- 不附带数据：项目只负责接口封装，不分发抓下来的招聘数据

### 城市编码说明

项目内置了一份热门城市编码表，适合作为快速 fallback。  
同时也提供了实时城市元数据接口，会尽量从智联基础数据接口中返回最新城市列表；如果上游不可用，就退回到内置热门城市编码表。

相关文件：

- 城市编码表：[app/city_codes.py](./app/city_codes.py)
- 城市接口逻辑：[app/service.py](./app/service.py)

### 部署方式

如果你只是本地开发，上面的 `uvicorn` 命令就够了。  
如果你要部署到服务器或容器环境，可以直接看：

- [Deployment Guide](./DEPLOYMENT.md)
- [Dockerfile](./Dockerfile)

### 环境变量

- `ZHILIAN_API_BASE` 默认：`https://fe-api.zhaopin.com`
- `ZHILIAN_PLATFORM` 默认：`13`
- `ZHILIAN_TIMEOUT_SECONDS` 默认：`20`
- `HOST` 默认：`0.0.0.0`
- `PORT` 默认：`8010`
- `RELOAD` 默认：`false`

### 说明与边界

- 这个项目封装的是智联网页前端使用到的接口
- 上游接口和字段可能会变化
- 请求过快时，可能会遇到验证态或限流
- 在生产使用前，请自行评估目标平台规则与合规要求

### 仓库内容

- `app/main.py`: FastAPI 入口与路由
- `app/service.py`: 上游请求与字段标准化
- `app/city_codes.py`: 内置热门城市编码表
- `README.md`: 双语总览
- `README.zh-CN.md`: 中文独立说明
- `DEPLOYMENT.md`: 部署说明
- `Dockerfile`: 容器化启动配置

### 许可证

MIT

* * *

## English

`zhilian-recruitment-fastapi` is an open-source `FastAPI` wrapper around Zhilian recruitment search, job detail, and city metadata endpoints observed from the public web frontend.

This repository is intentionally focused on the interface layer:

- no bundled scraped datasets
- no heavy persistence layer
- no platform-specific UI
- no claims that upstream fields are permanently stable

Instead, it provides a small and reusable service that is easier to plug into:

- AI job matching products
- recruitment aggregation services
- salary and skills analysis pipelines
- downstream data normalization workflows

### Intended use

- search jobs by keyword and city code
- fetch detailed job information by job number
- expose city code metadata for frontend selectors
- normalize upstream fields into a cleaner recruitment schema

### What the API exposes

- `GET /health`
- `GET /api/v1/zhilian/search`
- `GET /api/v1/zhilian/jobs/{job_number}`
- `GET /api/v1/recruitment/feed`
- `GET /api/v1/recruitment/jobs/{job_number}`
- `GET /api/v1/meta/cities`
- `GET /api/v1/meta/city-codes`

### Quick start

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

### Example requests

```bash
curl "http://127.0.0.1:8010/api/v1/zhilian/search?keyword=Python&city_code=530&page=1&page_size=10"
curl "http://127.0.0.1:8010/api/v1/zhilian/jobs/CC000544460J40723865416"
curl "http://127.0.0.1:8010/api/v1/meta/cities"
```

### Repository contents

- `app/main.py`: FastAPI app and routes
- `app/service.py`: upstream client and normalization logic
- `app/city_codes.py`: built-in hot city fallback mapping
- `DEPLOYMENT.md`: deployment guide
- `Dockerfile`: container build config

### Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md).

### License

MIT

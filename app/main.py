from __future__ import annotations

import os

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .service import (
    ZhilianClient,
    ZhilianUpstreamError,
    normalize_detail_response,
    normalize_search_response,
)


app = FastAPI(
    title="Zhilian Recruitment FastAPI",
    version="0.1.0",
    description="Open-source FastAPI wrapper for Zhilian recruitment search and detail endpoints.",
)

origins = [
    origin.strip()
    for origin in os.getenv(
        "ZHILIAN_CORS_ORIGINS",
        "http://127.0.0.1:3000,http://localhost:3000,http://127.0.0.1:5173,http://localhost:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

client = ZhilianClient()


@app.get("/health")
async def health() -> dict[str, object]:
    return {
        "success": True,
        "service": "zhilian-recruitment-fastapi",
        "platform": "zhilian",
    }


@app.get("/api/v1/zhilian/search")
@app.get("/api/v1/recruitment/feed")
async def search_jobs(
    keyword: str = Query(..., min_length=1, description="Search keyword, such as Python or Java backend."),
    city_code: str = Query("530", min_length=1, description="Zhilian city code. 530 means Beijing."),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
) -> dict[str, object]:
    try:
        raw, request_id = await client.search_positions(
            keyword=keyword,
            city_code=city_code,
            page=page,
            page_size=page_size,
        )
    except ZhilianUpstreamError as error:
        raise HTTPException(status_code=error.status_code, detail=error.payload | {"message": str(error)}) from error

    return normalize_search_response(
        raw,
        keyword=keyword,
        city_code=city_code,
        page=page,
        page_size=page_size,
        request_id=request_id,
    )


@app.get("/api/v1/zhilian/jobs/{job_number}")
@app.get("/api/v1/recruitment/jobs/{job_number}")
async def job_detail(job_number: str) -> dict[str, object]:
    try:
        raw, request_id = await client.get_job_detail(job_number)
    except ZhilianUpstreamError as error:
        raise HTTPException(status_code=error.status_code, detail=error.payload | {"message": str(error)}) from error

    return normalize_detail_response(raw, request_id=request_id)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8010")),
        reload=os.getenv("RELOAD", "false").lower() in {"1", "true", "yes", "on"},
    )

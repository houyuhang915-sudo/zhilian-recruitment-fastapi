from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from .city_codes import HOT_CITY_CODES


ZHILIAN_API_BASE = os.getenv("ZHILIAN_API_BASE", "https://fe-api.zhaopin.com")
ZHILIAN_PLATFORM = int(os.getenv("ZHILIAN_PLATFORM", "13"))
ZHILIAN_TIMEOUT_SECONDS = float(os.getenv("ZHILIAN_TIMEOUT_SECONDS", "20"))
ZHILIAN_VERSION = os.getenv("ZHILIAN_VERSION", "0.0.0")

DEFAULT_HEADERS = {
    "origin": "https://www.zhaopin.com",
    "referer": "https://www.zhaopin.com/",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

JOB_FAMILY_RULES = {
    "backend_engineering": ("后端", "python", "java", "golang", "go", "服务端"),
    "frontend_engineering": ("前端", "react", "vue", "web"),
    "mobile_engineering": ("android", "ios", "移动端", "客户端"),
    "data_engineering": ("数据开发", "数据工程", "etl", "hadoop", "spark"),
    "data_analysis": ("数据分析", "分析师", "bi"),
    "ai_engineering": ("算法", "机器学习", "深度学习", "aigc", "llm", "大模型"),
    "product_management": ("产品经理", "产品运营", "产品"),
    "design": ("设计", "ui", "ux"),
    "qa": ("测试", "qa"),
    "operations": ("运维", "sre", "devops"),
}


class ZhilianUpstreamError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int = 502,
        payload: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload or {}


class ZhilianClient:
    def __init__(self) -> None:
        self.base_url = ZHILIAN_API_BASE.rstrip("/")
        self.timeout = httpx.Timeout(ZHILIAN_TIMEOUT_SECONDS)

    async def search_positions(
        self,
        *,
        keyword: str,
        city_code: str,
        page: int,
        page_size: int,
    ) -> tuple[dict[str, Any], str]:
        payload = {
            "S_SOU_FULL_INDEX": keyword,
            "S_SOU_WORK_CITY": city_code,
            "pageIndex": page,
            "pageSize": page_size,
            "platform": ZHILIAN_PLATFORM,
            "version": ZHILIAN_VERSION,
            "eventScenario": "pcSearchedSouSearch",
            "anonymous": 1,
            "clickFilterBlackCompany": False,
        }
        response = await self._post("/c/i/search/positions", json=payload)
        request_id = response.headers.get("x-zp-request-id", "")
        data = response.json()
        self._ensure_ok(data, request_id=request_id)

        upstream = data.get("data", {})
        if upstream.get("isVerification") == 1:
            raise ZhilianUpstreamError(
                "Zhilian returned a verification challenge. Retry with lower frequency.",
                status_code=429,
                payload={"request_id": request_id},
            )

        return data, request_id

    async def get_job_detail(self, number: str) -> tuple[dict[str, Any], str]:
        response = await self._get("/c/i/jobs/position-detail-new", params={"number": number})
        request_id = response.headers.get("x-zp-request-id", "")
        data = response.json()
        self._ensure_ok(data, request_id=request_id)
        return data, request_id

    async def get_base_data(self) -> tuple[dict[str, Any], str]:
        response = await self._get("/c/i/search/base/data", params={})
        request_id = response.headers.get("x-zp-request-id", "")
        data = response.json()
        self._ensure_ok(data, request_id=request_id)
        return data, request_id

    async def _post(self, path: str, *, json: dict[str, Any]) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout, headers=DEFAULT_HEADERS) as client:
            response = await client.post(f"{self.base_url}{path}", json=json)
        response.raise_for_status()
        return response

    async def _get(self, path: str, *, params: dict[str, Any]) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout, headers=DEFAULT_HEADERS) as client:
            response = await client.get(f"{self.base_url}{path}", params=params)
        response.raise_for_status()
        return response

    def _ensure_ok(self, data: dict[str, Any], *, request_id: str) -> None:
        if data.get("code") == 200:
            return

        raise ZhilianUpstreamError(
            data.get("message") or "Upstream response was not successful.",
            status_code=502,
            payload={
                "request_id": request_id,
                "upstream_code": data.get("code"),
                "upstream_api_code": data.get("apiCode"),
            },
        )


def normalize_search_response(
    raw: dict[str, Any],
    *,
    keyword: str,
    city_code: str,
    page: int,
    page_size: int,
    request_id: str,
) -> dict[str, Any]:
    data = raw.get("data", {})
    items = [normalize_job_card(item) for item in data.get("list", [])]
    total = int(data.get("count") or 0)

    return {
        "success": True,
        "platform": "zhilian",
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_more": page * page_size < total,
        },
        "filters": {
            "keyword": keyword,
            "city_code": city_code,
        },
        "request_id": request_id,
        "upstream": {
            "method": data.get("method"),
            "method_group": data.get("methodGroup"),
            "status_code": data.get("statusCode"),
            "verification_required": bool(data.get("isVerification")),
        },
    }


def normalize_detail_response(raw: dict[str, Any], *, request_id: str) -> dict[str, Any]:
    data = raw.get("data", {})
    return {
        "success": True,
        "platform": "zhilian",
        "item": normalize_job_detail(data),
        "request_id": request_id,
        "upstream": {
            "task_id": data.get("taskId"),
        },
    }


def normalize_city_codes_response(
    raw: dict[str, Any] | None,
    *,
    include_districts: bool,
    request_id: str,
) -> dict[str, Any]:
    if not raw:
        return {
            "success": True,
            "items": HOT_CITY_CODES,
            "count": len(HOT_CITY_CODES),
            "request_id": request_id,
            "source": "static_fallback",
        }

    data = raw.get("data", {})
    items = flatten_city_data(data.get("allCity") or [], include_districts=include_districts)
    hot_codes = {item["code"] for item in data.get("hotCity") or [] if item.get("code")}
    for item in items:
        item["is_hot"] = item["code"] in hot_codes

    items = merge_hot_cities(items)

    return {
        "success": True,
        "items": items,
        "count": len(items),
        "request_id": request_id,
        "source": "zhilian_base_data",
    }


def normalize_job_card(item: dict[str, Any]) -> dict[str, Any]:
    salary_text = item.get("salary60") or ""
    min_salary, max_salary, negotiable = parse_salary_range(salary_text)
    normalized_url = normalize_position_url(item.get("positionURL") or item.get("positionUrl") or "")

    return {
        "job_id": item.get("number") or item.get("jobId") or "",
        "external_id": str(item.get("jobId") or ""),
        "title": item.get("name") or item.get("positionName") or "",
        "job_family": infer_job_family(item.get("name") or item.get("positionName") or ""),
        "company": {
            "company_id": item.get("companyNumber") or item.get("companyId") or "",
            "name": item.get("companyName") or "",
            "brand_name": item.get("companyName") or "",
            "industry": item.get("industryName") or "",
            "stage": simplify_stage(item.get("financingStage")),
            "size_range": item.get("companySize") or "",
            "logo_url": item.get("companyLogo") or "",
        },
        "location": {
            "country": "CN",
            "province": "",
            "city": item.get("workCity") or "",
            "district": item.get("cityDistrict") or "",
            "address": "",
            "remote_type": infer_remote_type(item.get("jobSummary") or ""),
        },
        "employment": {
            "employment_type": normalize_employment_type(item.get("applyType"), item.get("emplType")),
            "experience_level": normalize_experience_level(item.get("workingExp") or ""),
            "education": normalize_education(item.get("education") or ""),
            "headcount": safe_int(item.get("recruitNumber")),
        },
        "compensation": {
            "currency": "CNY",
            "min_monthly_salary": min_salary,
            "max_monthly_salary": max_salary,
            "salary_months": None,
            "bonus_months": None,
            "is_negotiable": negotiable,
            "raw_salary_text": salary_text,
        },
        "tags": extract_label_values(item.get("positionCommercialLabel")),
        "skills": extract_label_values(item.get("jobSkillTags")),
        "summary": item.get("jobSummary") or "",
        "responsibilities": [],
        "requirements": [],
        "benefits": extract_label_values(item.get("jobKnowledgeWelfareFeatures")),
        "source": {
            "platform": "智联招聘",
            "source_url": normalized_url,
            "published_at": item.get("firstPublishTime") or item.get("jobPostingTime"),
            "fetched_at": now_iso(),
        },
        "status": "open",
        "analytics": {
            "apply_count": None,
            "view_count": None,
            "fit_score": None,
        },
    }


def normalize_job_detail(data: dict[str, Any]) -> dict[str, Any]:
    position = data.get("detailedPosition") or {}
    company = data.get("detailedCompany") or {}
    description = position.get("jobDescPC") or position.get("jobDesc") or ""
    responsibilities, requirements, benefits = split_description_sections(description)
    salary_text = position.get("salary60") or ""
    min_salary, max_salary, negotiable = parse_salary_range(salary_text)

    return {
        "job_id": position.get("number") or position.get("positionNumber") or "",
        "external_id": str(position.get("number") or ""),
        "title": position.get("positionName") or position.get("name") or "",
        "job_family": infer_job_family(position.get("positionName") or position.get("name") or ""),
        "company": {
            "company_id": company.get("companyNumber") or position.get("companyNumber") or "",
            "name": company.get("companyName") or position.get("companyName") or "",
            "brand_name": company.get("companyName") or position.get("companyName") or "",
            "industry": company.get("industryNameLevel") or "",
            "stage": company.get("financingStageName") or "",
            "size_range": company.get("companySize") or "",
            "logo_url": company.get("companyLogo") or "",
            "description": company.get("companyDescription") or "",
        },
        "location": {
            "country": "CN",
            "province": "",
            "city": position.get("workCity") or position.get("positionWorkCity") or "",
            "district": position.get("cityDistrict") or position.get("positionCityDistrict") or "",
            "address": position.get("workAddress") or "",
            "remote_type": infer_remote_type(description),
        },
        "employment": {
            "employment_type": normalize_employment_type(position.get("applyType"), position.get("emplType")),
            "experience_level": normalize_experience_level(position.get("workingExp") or ""),
            "education": normalize_education(position.get("education") or ""),
            "headcount": safe_int(position.get("recruitNumber")),
        },
        "compensation": {
            "currency": "CNY",
            "min_monthly_salary": min_salary,
            "max_monthly_salary": max_salary,
            "salary_months": None,
            "bonus_months": None,
            "is_negotiable": negotiable,
            "raw_salary_text": salary_text,
        },
        "tags": extract_label_values(position.get("positionCommercialLabel")),
        "skills": extract_label_values(position.get("skillLabel")),
        "summary": summarize_text(description),
        "responsibilities": responsibilities,
        "requirements": requirements,
        "benefits": benefits,
        "source": {
            "platform": "智联招聘",
            "source_url": normalize_position_url(position.get("positionUrl") or position.get("url") or ""),
            "published_at": position.get("publishTime") or position.get("positionPublishTime"),
            "fetched_at": now_iso(),
        },
        "status": "open",
        "analytics": {
            "apply_count": None,
            "view_count": None,
            "fit_score": None,
        },
        "raw": {
            "position_number": position.get("positionNumber"),
            "position_status": position.get("positionStatus"),
            "staff": position.get("staff"),
        },
    }


def parse_salary_range(value: str) -> tuple[int | None, int | None, bool]:
    text = (value or "").strip()
    if not text:
        return None, None, True
    if "面议" in text:
        return None, None, True
    if "/天" in text or "/时" in text:
        return None, None, False

    match = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)(万|千|元)?", text)
    if not match:
        return None, None, False

    low = float(match.group(1))
    high = float(match.group(2))
    unit = match.group(3) or "元"
    multiplier = {"元": 1, "千": 1000, "万": 10000}.get(unit, 1)
    return int(low * multiplier), int(high * multiplier), False


def normalize_experience_level(value: str) -> str:
    text = (value or "").strip()
    if not text or "不限" in text or "无经验" in text:
        return "open"

    numbers = [int(token) for token in re.findall(r"\d+", text)]
    years = max(numbers) if numbers else 0
    if years <= 1:
        return "junior"
    if years <= 3:
        return "mid"
    if years <= 5:
        return "senior"
    return "lead"


def normalize_education(value: str) -> str:
    text = (value or "").strip()
    mapping = {
        "不限": "open",
        "大专": "associate",
        "本科": "bachelor",
        "硕士": "master",
        "博士": "phd",
    }
    for key, mapped in mapping.items():
        if key in text:
            return mapped
    return "open"


def normalize_employment_type(apply_type: Any, empl_type: Any) -> str:
    text = f"{apply_type or ''} {empl_type or ''}".strip().lower()
    if "实习" in text:
        return "internship"
    if "兼职" in text:
        return "part_time"
    if "合同" in text or "外包" in text or "contract" in text:
        return "contract"
    return "full_time"


def infer_remote_type(text: str) -> str:
    content = (text or "").lower()
    if "远程" in content:
        return "remote"
    if "居家" in content or "混合办公" in content:
        return "hybrid"
    return "onsite"


def infer_job_family(title: str) -> str:
    lowered = (title or "").lower()
    for family, keywords in JOB_FAMILY_RULES.items():
        if any(keyword in lowered for keyword in keywords):
            return family
    return "general"


def extract_label_values(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        items: list[str] = []
        for item in value:
            if isinstance(item, dict):
                label = item.get("value") or item.get("name") or item.get("label")
                if label:
                    items.append(str(label))
            elif item:
                items.append(str(item))
        return dedupe_strings(items)
    return [str(value)]


def split_description_sections(text: str) -> tuple[list[str], list[str], list[str]]:
    cleaned = clean_multiline_text(text)
    if not cleaned:
        return [], [], []

    lines = [line.strip(" -•·\t") for line in cleaned.splitlines() if line.strip()]
    responsibilities: list[str] = []
    requirements: list[str] = []
    benefits: list[str] = []
    bucket = responsibilities

    for line in lines:
        normalized = line.replace("：", ":")
        if any(token in normalized for token in ("岗位职责", "工作职责", "职位职责", "工作内容")):
            bucket = responsibilities
            continue
        if any(token in normalized for token in ("任职要求", "岗位要求", "职位要求", "任职资格", "岗位资格")):
            bucket = requirements
            continue
        if any(token in normalized for token in ("福利待遇", "员工福利", "薪酬福利", "福利")):
            bucket = benefits
            continue
        bucket.append(line)

    return (
        dedupe_strings(responsibilities[:12]),
        dedupe_strings(requirements[:12]),
        dedupe_strings(benefits[:12]),
    )


def summarize_text(text: str, limit: int = 240) -> str:
    cleaned = " ".join(clean_multiline_text(text).split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def clean_multiline_text(text: str) -> str:
    content = (text or "").replace("\r", "\n")
    content = re.sub(r"<br\s*/?>", "\n", content, flags=re.IGNORECASE)
    content = re.sub(r"<[^>]+>", "\n", content)
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip()


def dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def safe_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def simplify_stage(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("code") or "")
    return str(value or "")


def normalize_position_url(url: str) -> str:
    if not url:
        return ""
    normalized = url.replace("http://", "https://")
    return normalized.replace("jobs.zhaopin.com", "www.zhaopin.com/jobdetail")


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def flatten_city_data(groups: list[dict[str, Any]], *, include_districts: bool) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    for group in groups:
        province_name = group.get("name") or ""
        for city in group.get("sublist") or []:
            name = str(city.get("name") or "").strip()
            code = str(city.get("code") or "").strip()
            en_name = str(city.get("en_name") or "").strip()
            if not name or not code:
                continue
            if not include_districts and looks_like_district(name):
                continue
            items.append(
                {
                    "code": code,
                    "name": name,
                    "en_name": en_name,
                    "province": province_name,
                }
            )

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        if item["code"] in seen:
            continue
        seen.add(item["code"])
        deduped.append(item)
    return deduped


def merge_hot_cities(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged = list(items)
    existing_codes = {item["code"] for item in merged}
    for item in HOT_CITY_CODES:
        if item["code"] not in existing_codes:
            merged.append(
                {
                    "code": item["code"],
                    "name": item["name"],
                    "en_name": item["en_name"],
                    "province": item["name"],
                    "is_hot": True,
                }
            )
    merged.sort(key=lambda item: (0 if item.get("is_hot") else 1, item["code"]))
    return merged


def looks_like_district(name: str) -> bool:
    suffixes = ("区", "县", "新区", "自治县", "旗", "群岛")
    return name.endswith(suffixes)

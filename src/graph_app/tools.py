import ast
import csv
import json
import operator
import os
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[[dict[str, Any]], str]

    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_HIGH_VALUE_KEYWORDS = [
    "医美",
    "牙科",
    "装修",
    "留学",
    "移民",
    "法律",
    "企业",
    "B2B",
    "SaaS",
]
_URGENT_KEYWORDS = ["今天", "明天", "本周", "尽快", "马上", "急", "近期", "1周"]
_CONTACT_KEYWORDS = ["@", "微信", "电话", "手机", "邮箱", "weChat", "whatsapp"]


def run_tool(name: str, args: dict) -> str:
    tool = TOOL_REGISTRY.get(name)
    if not tool:
        return f"未知工具：{name}"

    return tool.handler(args)


def get_tool_schemas() -> list[dict[str, Any]]:
    return [tool.schema() for tool in TOOL_REGISTRY.values()]


def _run_calculator(args: dict[str, Any]) -> str:
    expression = str(args.get("expression", "")).strip()
    return str(safe_calculate(expression))


def _run_text_stats(args: dict[str, Any]) -> str:
    text = str(args.get("text", ""))
    return text_stats(text)


def _run_current_time(args: dict[str, Any]) -> str:
    timezone = str(args.get("timezone", "Asia/Shanghai")).strip() or "Asia/Shanghai"
    return current_time(timezone)


def _run_qualify_lead(args: dict[str, Any]) -> str:
    return qualify_lead(
        industry=str(args.get("industry", "")),
        need=str(args.get("need", "")),
        budget=str(args.get("budget", "")),
        timeline=str(args.get("timeline", "")),
        city=str(args.get("city", "")),
        contact=str(args.get("contact", "")),
        source=str(args.get("source", "")),
    )


def _run_record_lead(args: dict[str, Any]) -> str:
    return record_lead(
        customer_name=str(args.get("customer_name", "")),
        contact=str(args.get("contact", "")),
        industry=str(args.get("industry", "")),
        need=str(args.get("need", "")),
        budget=str(args.get("budget", "")),
        timeline=str(args.get("timeline", "")),
        city=str(args.get("city", "")),
        source=str(args.get("source", "")),
        grade=str(args.get("grade", "")),
        notes=str(args.get("notes", "")),
    )


def _run_draft_sales_reply(args: dict[str, Any]) -> str:
    return draft_sales_reply(
        customer_message=str(args.get("customer_message", "")),
        industry=str(args.get("industry", "")),
        lead_grade=str(args.get("lead_grade", "")),
        missing_fields=list(args.get("missing_fields", []) or []),
    )


def _run_create_followup_plan(args: dict[str, Any]) -> str:
    return create_followup_plan(
        customer_name=str(args.get("customer_name", "")),
        need=str(args.get("need", "")),
        lead_grade=str(args.get("lead_grade", "")),
        owner=str(args.get("owner", "销售")),
    )


def _run_generate_sales_report(args: dict[str, Any]) -> str:
    return generate_sales_report(
        date=str(args.get("date", "")),
        owner=str(args.get("owner", "老板")),
    )


def _run_list_hot_leads(args: dict[str, Any]) -> str:
    return list_hot_leads(limit=int(args.get("limit", 5)))


def _run_import_leads(args: dict[str, Any]) -> str:
    return import_leads(
        file_path=str(args.get("file_path", "")),
        max_rows=int(args.get("max_rows", 100)),
    )


def _run_sync_lead_to_feishu(args: dict[str, Any]) -> str:
    lead = {
        "created_at": str(args.get("created_at", "")),
        "customer_name": str(args.get("customer_name", "")),
        "contact": str(args.get("contact", "")),
        "industry": str(args.get("industry", "")),
        "need": str(args.get("need", "")),
        "budget": str(args.get("budget", "")),
        "timeline": str(args.get("timeline", "")),
        "city": str(args.get("city", "")),
        "source": str(args.get("source", "")),
        "grade": str(args.get("grade", "")),
        "notes": str(args.get("notes", "")),
    }
    if not lead["created_at"]:
        lead["created_at"] = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")

    return sync_lead_to_feishu(lead)


def _run_test_feishu_sync(args: dict[str, Any]) -> str:
    customer_name = str(args.get("customer_name", "飞书测试客户")).strip() or "飞书测试客户"
    return create_feishu_test_lead(customer_name)


def _run_inspect_feishu_fields(args: dict[str, Any]) -> str:
    return inspect_feishu_fields()


def _run_list_feishu_tables(args: dict[str, Any]) -> str:
    return list_feishu_tables()


def safe_calculate(expression: str) -> float | int:
    tree = ast.parse(expression, mode="eval")
    return _eval_node(tree.body)


def text_stats(text: str) -> str:
    chars = len(text)
    non_space_chars = len("".join(text.split()))
    words = len(text.split())
    lines = text.count("\n") + 1 if text else 0

    return (
        f"字符数：{chars}；"
        f"非空白字符数：{non_space_chars}；"
        f"按空白分隔的词数：{words}；"
        f"行数：{lines}"
    )


def current_time(timezone: str) -> str:
    try:
        tz = ZoneInfo(timezone)
    except Exception:
        tz = ZoneInfo("Asia/Shanghai")
        timezone = "Asia/Shanghai"

    now = datetime.now(tz)
    return f"{timezone} 当前时间：{now:%Y-%m-%d %H:%M:%S}"


def qualify_lead(
    industry: str,
    need: str,
    budget: str,
    timeline: str,
    city: str,
    contact: str,
    source: str,
) -> str:
    facts = " ".join([industry, need, budget, timeline, city, contact, source])
    score = 0
    reasons: list[str] = []
    missing: list[str] = []

    if any(keyword.lower() in facts.lower() for keyword in _HIGH_VALUE_KEYWORDS):
        score += 25
        reasons.append("行业或需求客单价较高")

    if need.strip():
        score += 20
        reasons.append("已说明具体需求")
    else:
        missing.append("需求")

    if budget.strip():
        score += 20
        reasons.append("已提供预算")
    else:
        missing.append("预算")

    if timeline.strip():
        score += 15
        reasons.append("已提供时间计划")
        if any(keyword in timeline for keyword in _URGENT_KEYWORDS):
            score += 10
            reasons.append("时间紧迫，跟进优先级高")
    else:
        missing.append("时间计划")

    if city.strip():
        score += 10
        reasons.append("已提供城市/区域")
    else:
        missing.append("城市/区域")

    if contact.strip() or any(keyword.lower() in facts.lower() for keyword in _CONTACT_KEYWORDS):
        score += 10
        reasons.append("已提供联系方式")
    else:
        missing.append("联系方式")

    score = min(score, 100)
    if score >= 75:
        grade = "A-高意向"
        next_action = "10分钟内由销售人工跟进，并直接推进预约/报价。"
    elif score >= 45:
        grade = "B-需培育"
        next_action = "继续追问缺失信息，24小时内二次跟进。"
    else:
        grade = "C-低意向/信息不足"
        next_action = "先自动补问需求、预算、时间和联系方式。"

    return (
        f"线索评分：{score}/100\n"
        f"线索等级：{grade}\n"
        f"判断依据：{'；'.join(reasons) if reasons else '信息不足'}\n"
        f"缺失信息：{', '.join(missing) if missing else '无'}\n"
        f"建议动作：{next_action}"
    )


def record_lead(
    customer_name: str,
    contact: str,
    industry: str,
    need: str,
    budget: str,
    timeline: str,
    city: str,
    source: str,
    grade: str,
    notes: str,
) -> str:
    raw_path = os.getenv("LEADS_DB", "").strip()
    if raw_path:
        env_path = Path(raw_path)
        path = env_path if env_path.is_absolute() else Path.cwd() / env_path
    else:
        path = Path.cwd() / "data" / "leads.jsonl"

    path.parent.mkdir(parents=True, exist_ok=True)
    lead = {
        "created_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds"),
        "customer_name": customer_name or "未命名客户",
        "contact": contact,
        "industry": industry,
        "need": need,
        "budget": budget,
        "timeline": timeline,
        "city": city,
        "source": source,
        "grade": grade,
        "notes": notes,
    }
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(lead, ensure_ascii=False) + "\n")

    sync_result = sync_lead_to_feishu_if_enabled(lead)
    return (
        f"已记录线索：{lead['customer_name']}；等级：{grade or '未评级'}；位置：{path}"
        f"\n飞书同步：{sync_result}"
    )


def import_leads(file_path: str, max_rows: int = 100) -> str:
    path = resolve_import_path(file_path)
    if not path.exists():
        return f"导入失败：文件不存在：{path}"
    if not path.is_file():
        return f"导入失败：不是文件：{path}"

    try:
        rows = read_lead_import_file(path)
    except Exception as exc:
        return f"导入失败：{exc}"

    imported = 0
    skipped = 0
    feishu_success = 0
    examples: list[str] = []
    limit = max(1, max_rows)

    for raw_row in rows[:limit]:
        lead = normalize_imported_lead(raw_row, default_source=path.stem)
        if not any(lead[key] for key in ("customer_name", "contact", "need")):
            skipped += 1
            continue

        if not lead["grade"]:
            lead["grade"] = extract_lead_grade(
                qualify_lead(
                    industry=lead["industry"],
                    need=lead["need"],
                    budget=lead["budget"],
                    timeline=lead["timeline"],
                    city=lead["city"],
                    contact=lead["contact"],
                    source=lead["source"],
                )
            )

        result = record_lead(
            customer_name=lead["customer_name"],
            contact=lead["contact"],
            industry=lead["industry"],
            need=lead["need"],
            budget=lead["budget"],
            timeline=lead["timeline"],
            city=lead["city"],
            source=lead["source"],
            grade=lead["grade"],
            notes=lead["notes"],
        )
        imported += 1
        if "飞书同步：成功" in result:
            feishu_success += 1
        if len(examples) < 5:
            examples.append(f"- {lead['customer_name'] or '未命名客户'}：{lead['grade'] or '未评级'}")

    remaining = max(0, len(rows) - limit)
    lines = [
        "批量导入完成：",
        f"  文件：{path}",
        f"  读取：{len(rows)} 条",
        f"  导入：{imported} 条",
        f"  跳过：{skipped} 条",
        f"  超出上限未处理：{remaining} 条",
        f"  飞书同步成功：{feishu_success} 条",
    ]
    if examples:
        lines.append("  示例：")
        lines.extend(f"  {item}" for item in examples)

    return "\n".join(lines)


def resolve_import_path(file_path: str) -> Path:
    raw_path = file_path.strip().strip('"').strip("'")
    if not raw_path:
        return Path("__missing_import_file__")

    path = Path(raw_path)
    return path if path.is_absolute() else Path.cwd() / path


def read_lead_import_file(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            return [dict(row) for row in csv.DictReader(file)]

    if suffix == ".jsonl":
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows

    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
        if isinstance(data, dict):
            items = data.get("leads") or data.get("rows") or data.get("data")
            if isinstance(items, list):
                return [row for row in items if isinstance(row, dict)]
            return [data]

    raise ValueError("仅支持 .csv、.jsonl、.json 线索文件")


def normalize_imported_lead(row: dict[str, Any], default_source: str) -> dict[str, str]:
    return {
        "customer_name": pick_lead_value(row, "customer_name", "客户名称", "客户", "姓名", "name"),
        "contact": pick_lead_value(row, "contact", "联系方式", "手机", "电话", "微信", "phone", "wechat"),
        "industry": pick_lead_value(row, "industry", "行业", "业务", "服务", "service"),
        "need": pick_lead_value(row, "need", "需求", "咨询内容", "客户需求", "message", "content"),
        "budget": pick_lead_value(row, "budget", "预算", "价格预算"),
        "timeline": pick_lead_value(row, "timeline", "时间计划", "预约时间", "期望时间"),
        "city": pick_lead_value(row, "city", "城市", "地区", "区域"),
        "source": pick_lead_value(row, "source", "来源", "渠道") or default_source,
        "grade": pick_lead_value(row, "grade", "线索等级", "等级"),
        "notes": pick_lead_value(row, "notes", "备注", "补充信息"),
    }


def pick_lead_value(row: dict[str, Any], *names: str) -> str:
    normalized = {str(key).strip().lower(): value for key, value in row.items()}
    for name in names:
        value = normalized.get(name.lower())
        if value is not None:
            return str(value).strip()

    return ""


def extract_lead_grade(qualification: str) -> str:
    for line in qualification.splitlines():
        if line.startswith("线索等级："):
            return line.removeprefix("线索等级：").strip()

    return ""


def sync_lead_to_feishu_if_enabled(lead: dict[str, Any]) -> str:
    if os.getenv("FEISHU_SYNC_ENABLED", "").strip().lower() not in {"1", "true", "yes", "on"}:
        return "未开启"

    return sync_lead_to_feishu(lead)


def sync_lead_to_feishu(lead: dict[str, Any]) -> str:
    config = feishu_config()
    missing = [name for name, value in config.items() if name != "base_url" and not value]
    if missing:
        return "配置缺失：" + ", ".join(missing)

    try:
        token = get_feishu_tenant_access_token(
            app_id=config["app_id"],
            app_secret=config["app_secret"],
            base_url=config["base_url"],
        )
        record_id = create_feishu_bitable_record(
            token=token,
            app_token=config["app_token"],
            table_id=config["table_id"],
            fields=feishu_lead_fields(lead),
            base_url=config["base_url"],
        )
    except Exception as exc:
        return f"失败：{exc}"

    return f"成功：record_id={record_id}"


def feishu_config_status() -> str:
    config = feishu_config()
    required = ["app_id", "app_secret", "app_token", "table_id"]
    missing = [name for name in required if not config[name]]
    sync_enabled = os.getenv("FEISHU_SYNC_ENABLED", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    lines = [
        "飞书配置状态：",
        f"  FEISHU_SYNC_ENABLED: {sync_enabled}",
        f"  FEISHU_APP_ID: {mask_secret(config['app_id'])}",
        f"  FEISHU_APP_SECRET: {mask_secret(config['app_secret'])}",
        f"  FEISHU_BITABLE_APP_TOKEN: {mask_secret(config['app_token'])}",
        f"  FEISHU_BITABLE_TABLE_ID: {mask_secret(config['table_id'])}",
        f"  FEISHU_BASE_URL: {config['base_url']}",
        "  需要权限：bitable:app 或 base:record:create",
    ]
    if looks_like_feishu_view_id(config["table_id"]):
        lines.append("  警告：FEISHU_BITABLE_TABLE_ID 看起来是视图 ID（vew...），请改成表 ID（通常是 tbl...）。")
    if missing:
        lines.append("  缺失配置：" + ", ".join(missing))
    else:
        lines.append("  必要配置：完整")

    return "\n".join(lines)


def mask_secret(value: str) -> str:
    if not value:
        return "(not set)"
    if len(value) <= 8:
        return value[:2] + "***"
    return value[:4] + "..." + value[-4:]


def looks_like_feishu_view_id(value: str) -> bool:
    return value.strip().lower().startswith("vew")


def feishu_test_lead(customer_name: str = "飞书测试客户") -> dict[str, Any]:
    return {
        "created_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds"),
        "customer_name": customer_name,
        "contact": "test-contact",
        "industry": "测试行业",
        "need": "验证 LangGraph Agent 写入飞书多维表格",
        "budget": "测试预算",
        "timeline": "今天",
        "city": "测试城市",
        "source": "v22 飞书同步测试",
        "grade": "A-高意向",
        "notes": "这是一条由 /feishu test 创建的测试记录，可在验收后删除。",
    }


def create_feishu_test_lead(customer_name: str = "飞书测试客户") -> str:
    return sync_lead_to_feishu(feishu_test_lead(customer_name))


def feishu_test_payload_preview() -> str:
    fields = feishu_lead_fields(feishu_test_lead())
    return json.dumps({"fields": fields}, ensure_ascii=False, indent=2)


def inspect_feishu_fields() -> str:
    config = feishu_config()
    missing = [name for name, value in config.items() if name != "base_url" and not value]
    if missing:
        return "配置缺失：" + ", ".join(missing)

    try:
        token = get_feishu_tenant_access_token(
            app_id=config["app_id"],
            app_secret=config["app_secret"],
            base_url=config["base_url"],
        )
        data = get_json(
            f"{config['base_url']}/open-apis/bitable/v1/apps/"
            f"{config['app_token']}/tables/{config['table_id']}/fields?page_size=100",
            headers={"Authorization": f"Bearer {token}"},
        )
    except Exception as exc:
        return f"读取字段失败：{exc}"

    items = data.get("data", {}).get("items", [])
    if not items:
        return "没有读取到字段。请确认 table_id 是否正确。"

    lines = ["飞书多维表字段："]
    remote_field_names = []
    for item in items:
        remote_field_names.append(str(item.get("field_name", "")))
        lines.append(
            f"- {item.get('field_name')} | id={item.get('field_id')} | type={item.get('type')}"
        )

    expected_field_names = list(feishu_lead_fields(feishu_test_lead()).keys())
    missing_field_names = [
        field_name for field_name in expected_field_names if field_name not in remote_field_names
    ]
    if missing_field_names:
        lines.append("")
        lines.append("当前写入 payload 中缺少这些飞书字段：")
        for field_name in missing_field_names:
            lines.append(f"- {field_name}")
        lines.append("请在飞书多维表中创建同名字段，或用 FEISHU_FIELD_* 环境变量映射到已有字段。")

    return "\n".join(lines)


def list_feishu_tables() -> str:
    config = feishu_config()
    missing = [name for name in ("app_id", "app_secret", "app_token") if not config[name]]
    if missing:
        return "配置缺失：" + ", ".join(missing)

    try:
        token = get_feishu_tenant_access_token(
            app_id=config["app_id"],
            app_secret=config["app_secret"],
            base_url=config["base_url"],
        )
        data = get_json(
            f"{config['base_url']}/open-apis/bitable/v1/apps/"
            f"{config['app_token']}/tables?page_size=100",
            headers={"Authorization": f"Bearer {token}"},
        )
    except Exception as exc:
        return f"读取表列表失败：{exc}"

    items = data.get("data", {}).get("items", [])
    if not items:
        return "没有读取到表。请确认 FEISHU_BITABLE_APP_TOKEN 是否正确，且应用有访问该多维表格的权限。"

    lines = ["飞书多维表格表列表："]
    for item in items:
        lines.append(f"- {item.get('name')} | table_id={item.get('table_id')}")

    return "\n".join(lines)


def feishu_config() -> dict[str, str]:
    return {
        "app_id": os.getenv("FEISHU_APP_ID", "").strip(),
        "app_secret": os.getenv("FEISHU_APP_SECRET", "").strip(),
        "app_token": os.getenv("FEISHU_BITABLE_APP_TOKEN", "").strip(),
        "table_id": os.getenv("FEISHU_BITABLE_TABLE_ID", "").strip(),
        "base_url": os.getenv("FEISHU_BASE_URL", "https://open.feishu.cn").rstrip("/"),
    }


def get_feishu_tenant_access_token(app_id: str, app_secret: str, base_url: str) -> str:
    payload = {"app_id": app_id, "app_secret": app_secret}
    data = post_json(
        f"{base_url}/open-apis/auth/v3/tenant_access_token/internal",
        payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    token = data.get("tenant_access_token")
    if not token:
        raise RuntimeError(f"tenant_access_token 获取失败：{data}")

    return str(token)


def create_feishu_bitable_record(
    token: str,
    app_token: str,
    table_id: str,
    fields: dict[str, Any],
    base_url: str,
) -> str:
    data = post_json(
        f"{base_url}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records",
        {"fields": fields},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )
    record = data.get("data", {}).get("record", {})
    return str(record.get("record_id") or data.get("record_id") or "unknown")


def get_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(url=url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(format_feishu_http_error(exc.code, body)) from exc

    data = json.loads(raw)
    if data.get("code") not in {None, 0}:
        raise RuntimeError(format_feishu_api_error(data))

    return data


def post_json(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(
        url=url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(format_feishu_http_error(exc.code, body)) from exc

    data = json.loads(raw)
    if data.get("code") not in {None, 0}:
        raise RuntimeError(format_feishu_api_error(data))

    return data


def format_feishu_api_error(data: dict[str, Any]) -> str:
    if data.get("code") == 91403:
        return format_feishu_http_error(403, json.dumps(data, ensure_ascii=False))

    if str(data.get("msg", "")).lower() == "wrongrequestbody":
        return "\n".join(
            [
                "WrongRequestBody：飞书拒绝了写入记录的请求体。",
                "常见原因：多维表字段名不匹配，或字段类型和写入值不匹配。",
                "请优先检查：创建时间 是否为日期字段；日期字段需要毫秒时间戳。",
                "如果仍失败，可以先在 .env 中设置 FEISHU_FIELD_CREATED_AT=__skip__ 跳过创建时间字段，再运行 /feishu test。",
            ]
        )

    if str(data.get("msg", "")).lower() == "textfieldconvfail":
        return "\n".join(
            [
                "TextFieldConvFail：飞书文本字段收到了无法转换成文本的值。",
                "常见原因：把创建时间写入了文本字段。日期字段需要飞书日期/时间类型，文本字段应写字符串。",
                "最快修复：在 .env 中设置 FEISHU_FIELD_CREATED_AT=__skip__ 跳过创建时间字段，再运行 /feishu payload 和 /feishu test。",
            ]
        )

    if str(data.get("msg", "")).lower() == "wrongtableid":
        return "\n".join(
            [
                "WrongTableId：飞书找不到这个 table_id。",
                "你很可能把视图 ID（通常以 vew 开头）填进了 FEISHU_BITABLE_TABLE_ID。",
                "请打开飞书多维表格，从 URL 或开发者信息里复制真正的表 ID（通常以 tbl 开头），然后重新运行 /feishu fields。",
            ]
        )

    message = data.get("msg") or data.get("message") or data
    return str(message)


def format_feishu_http_error(status_code: int, body: str) -> str:
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return f"HTTP {status_code}: {body}"

    if data.get("code") == 99991672:
        auth_url = extract_feishu_auth_url(data)
        parts = [
            f"HTTP {status_code}: 飞书应用缺少多维表格写入权限。",
            "需要在飞书开放平台为当前自建应用开通以下任一权限：bitable:app 或 base:record:create。",
            "开通权限后，需要发布/生效应用权限，再重新运行 /feishu test。",
        ]
        if auth_url:
            parts.append(f"权限开通链接：{auth_url}")
        return "\n".join(parts)

    if data.get("code") == 91403:
        return "\n".join(
            [
                f"HTTP {status_code}: 飞书拒绝访问这个多维表格。",
                "应用接口权限已经基本通过，但当前应用没有目标多维表格的文件访问权限，或 app_token/table_id 不属于这个应用可访问范围。",
                "请在飞书多维表格中把当前自建应用添加为协作者/授权应用，或确认 app_token 和 table_id 来自同一个目标多维表格。",
                "处理后重新运行 /feishu test。",
            ]
        )

    message = data.get("msg") or data.get("message") or body
    return f"HTTP {status_code}: {message}"


def extract_feishu_auth_url(data: dict[str, Any]) -> str:
    message = str(data.get("msg", ""))
    match = __import__("re").search(r"https://\S+", message)
    if not match:
        return ""

    return match.group(0)


def feishu_lead_fields(lead: dict[str, Any]) -> dict[str, Any]:
    field_names = {
        "created_at": feishu_field_name("FEISHU_FIELD_CREATED_AT", "创建时间"),
        "customer_name": feishu_field_name("FEISHU_FIELD_CUSTOMER_NAME", "客户名称"),
        "contact": feishu_field_name("FEISHU_FIELD_CONTACT", "联系方式"),
        "industry": feishu_field_name("FEISHU_FIELD_INDUSTRY", "行业"),
        "need": feishu_field_name("FEISHU_FIELD_NEED", "需求"),
        "budget": feishu_field_name("FEISHU_FIELD_BUDGET", "预算"),
        "timeline": feishu_field_name("FEISHU_FIELD_TIMELINE", "时间计划"),
        "city": feishu_field_name("FEISHU_FIELD_CITY", "城市"),
        "source": feishu_field_name("FEISHU_FIELD_SOURCE", "来源"),
        "grade": feishu_field_name("FEISHU_FIELD_GRADE", "线索等级"),
        "notes": feishu_field_name("FEISHU_FIELD_NOTES", "备注"),
    }
    fields = {}
    for key, field_name in field_names.items():
        if not field_name:
            continue

        value = lead.get(key, "")
        if key == "created_at" and value:
            value = to_feishu_datetime_millis(str(value))
        fields[field_name] = value

    return fields


def feishu_field_name(env_name: str, default: str) -> str:
    value = os.getenv(env_name)
    if value is None:
        return default

    value = value.strip()
    if value.lower() in {"", "__skip__", "skip", "none", "null", "-"}:
        return ""

    return value


def to_feishu_datetime_millis(value: str) -> int | str:
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return value

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo("Asia/Shanghai"))

    return int(parsed.timestamp() * 1000)


def lead_db_path() -> Path:
    raw_path = os.getenv("LEADS_DB", "").strip()
    if raw_path:
        env_path = Path(raw_path)
        return env_path if env_path.is_absolute() else Path.cwd() / env_path

    return Path.cwd() / "data" / "leads.jsonl"


def load_leads() -> list[dict[str, Any]]:
    path = lead_db_path()
    if not path.exists():
        return []

    leads = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            leads.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    return leads


def generate_sales_report(date: str, owner: str) -> str:
    leads = load_leads()
    if date.strip():
        leads = [lead for lead in leads if str(lead.get("created_at", "")).startswith(date)]

    if not leads:
        scope = date or "全部日期"
        return f"{scope} 暂无线索记录。"

    total = len(leads)
    a_leads = [lead for lead in leads if str(lead.get("grade", "")).startswith("A")]
    b_leads = [lead for lead in leads if str(lead.get("grade", "")).startswith("B")]
    c_leads = [lead for lead in leads if str(lead.get("grade", "")).startswith("C")]
    ungraded = total - len(a_leads) - len(b_leads) - len(c_leads)
    hot_items = [
        f"{lead.get('customer_name', '未命名客户')}（{lead.get('industry', '未知行业')}，{lead.get('need', '需求待补充')}）"
        for lead in a_leads[:5]
    ]
    sources: dict[str, int] = {}
    for lead in leads:
        source = str(lead.get("source") or "未知来源")
        sources[source] = sources.get(source, 0) + 1

    source_summary = "；".join(
        f"{source} {count}条"
        for source, count in sorted(sources.items(), key=lambda item: item[1], reverse=True)
    )
    owner_name = owner or "老板"

    return (
        f"销售线索日报\n"
        f"汇报对象：{owner_name}\n"
        f"统计日期：{date or '全部日期'}\n"
        f"总线索：{total} 条\n"
        f"A级高意向：{len(a_leads)} 条\n"
        f"B级需培育：{len(b_leads)} 条\n"
        f"C级低意向/信息不足：{len(c_leads)} 条\n"
        f"未评级：{ungraded} 条\n"
        f"来源分布：{source_summary}\n"
        f"今日优先跟进：{'; '.join(hot_items) if hot_items else '暂无 A 级线索'}\n"
        f"建议动作：A级线索 10 分钟内人工跟进；B级线索补问预算/时间/联系方式；C级线索自动培育。"
    )


def list_hot_leads(limit: int) -> str:
    leads = [
        lead for lead in load_leads()
        if str(lead.get("grade", "")).startswith("A")
    ]
    leads = leads[-max(1, limit):]

    if not leads:
        return "暂无 A 级高意向线索。"

    lines = []
    for index, lead in enumerate(reversed(leads), start=1):
        lines.append(
            f"{index}. {lead.get('customer_name', '未命名客户')} | "
            f"{lead.get('industry', '未知行业')} | "
            f"{lead.get('need', '需求待补充')} | "
            f"{lead.get('contact', '联系方式待补充')} | "
            f"{lead.get('timeline', '时间待补充')}"
        )

    return "A 级高意向线索：\n" + "\n".join(lines)


def draft_sales_reply(
    customer_message: str,
    industry: str,
    lead_grade: str,
    missing_fields: list[Any],
) -> str:
    missing = [str(item) for item in missing_fields if str(item).strip()]
    questions = []
    field_questions = {
        "需求": "您主要想解决什么问题，或者想了解哪项服务？",
        "预算": "方便说一下大概预算范围吗？我好给您匹配更合适的方案。",
        "时间计划": "您希望什么时候开始或预约？",
        "城市/区域": "您在哪个城市或区域？",
        "联系方式": "方便留一个微信或手机号吗？我让顾问继续跟进。",
    }
    for field in missing[:3]:
        questions.append(field_questions.get(field, f"方便补充一下{field}吗？"))

    if not questions:
        questions.append("我先帮您整理需求，并安排顾问给您一个更具体的方案。")

    urgency = "我会优先转给销售顾问。" if lead_grade.startswith("A") else "我先帮您把关键信息整理完整。"
    return (
        f"客户原话：{customer_message or '未提供'}\n"
        f"建议回复：您好，您咨询的{industry or '服务'}我收到了。{urgency}"
        f"{' '.join(questions)}"
    )


def create_followup_plan(
    customer_name: str,
    need: str,
    lead_grade: str,
    owner: str,
) -> str:
    name = customer_name or "该客户"
    owner_name = owner or "销售"
    if lead_grade.startswith("A"):
        cadence = [
            "T+0 10分钟内：电话/微信跟进，确认预算、时间和预约意向。",
            "T+0 30分钟内：发送针对性方案或报价区间。",
            "T+1：如果未回复，发送案例/优惠/档期提醒。",
        ]
    elif lead_grade.startswith("B"):
        cadence = [
            "T+0：自动补问缺失信息。",
            "T+1：发送服务介绍、案例和常见问题。",
            "T+3：询问是否需要顾问进一步沟通。",
        ]
    else:
        cadence = [
            "T+0：只收集基础需求和联系方式。",
            "T+2：发送一条轻量提醒。",
            "T+7：无回复则归档为低优先级。",
        ]

    return (
        f"跟进对象：{name}\n"
        f"需求摘要：{need or '待补充'}\n"
        f"负责人：{owner_name}\n"
        f"跟进节奏：\n- " + "\n- ".join(cadence)
    )


def _eval_node(node: ast.AST) -> float | int:
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return node.value

    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return _OPERATORS[type(node.op)](left, right)

    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        operand = _eval_node(node.operand)
        return _OPERATORS[type(node.op)](operand)

    raise ValueError("Only simple arithmetic expressions are supported.")


TOOL_REGISTRY = {
    "calculator": ToolSpec(
        name="calculator",
        description="计算只包含数字、括号和 + - * / // % ** 运算符的数学表达式。",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "需要计算的数学表达式，例如：1 + 2 * (3 + 4)",
                }
            },
            "required": ["expression"],
        },
        handler=_run_calculator,
    ),
    "text_stats": ToolSpec(
        name="text_stats",
        description="统计文本的字符数、非空白字符数、按空白分隔的词数和行数。",
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "需要统计的文本。",
                }
            },
            "required": ["text"],
        },
        handler=_run_text_stats,
    ),
    "current_time": ToolSpec(
        name="current_time",
        description="获取指定 IANA 时区的当前时间。",
        parameters={
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "IANA 时区名，例如 Asia/Shanghai 或 America/New_York。",
                }
            },
            "required": ["timezone"],
        },
        handler=_run_current_time,
    ),
    "qualify_lead": ToolSpec(
        name="qualify_lead",
        description="根据行业、需求、预算、时间、城市和联系方式判断销售线索等级。",
        parameters={
            "type": "object",
            "properties": {
                "industry": {"type": "string", "description": "客户所属行业或商家类型。"},
                "need": {"type": "string", "description": "客户需求描述。"},
                "budget": {"type": "string", "description": "客户预算或价格敏感度。"},
                "timeline": {"type": "string", "description": "客户期望开始/预约/成交时间。"},
                "city": {"type": "string", "description": "客户所在城市或服务区域。"},
                "contact": {"type": "string", "description": "微信、手机号、邮箱等联系方式。"},
                "source": {"type": "string", "description": "线索来源，例如表单、飞书、微信。"},
            },
            "required": ["industry", "need", "budget", "timeline", "city", "contact", "source"],
        },
        handler=_run_qualify_lead,
    ),
    "record_lead": ToolSpec(
        name="record_lead",
        description="把销售线索写入本地 JSONL 台账，后续可替换为飞书多维表格或 CRM。",
        parameters={
            "type": "object",
            "properties": {
                "customer_name": {"type": "string", "description": "客户姓名或称呼。"},
                "contact": {"type": "string", "description": "客户联系方式。"},
                "industry": {"type": "string", "description": "客户行业。"},
                "need": {"type": "string", "description": "客户需求。"},
                "budget": {"type": "string", "description": "预算。"},
                "timeline": {"type": "string", "description": "时间计划。"},
                "city": {"type": "string", "description": "城市/区域。"},
                "source": {"type": "string", "description": "线索来源。"},
                "grade": {"type": "string", "description": "线索等级，例如 A-高意向。"},
                "notes": {"type": "string", "description": "补充备注。"},
            },
            "required": [
                "customer_name",
                "contact",
                "industry",
                "need",
                "budget",
                "timeline",
                "city",
                "source",
                "grade",
                "notes",
            ],
        },
        handler=_run_record_lead,
    ),
    "draft_sales_reply": ToolSpec(
        name="draft_sales_reply",
        description="根据客户原话、行业、线索等级和缺失信息生成销售前台回复草稿。",
        parameters={
            "type": "object",
            "properties": {
                "customer_message": {"type": "string", "description": "客户原始咨询内容。"},
                "industry": {"type": "string", "description": "行业或服务类型。"},
                "lead_grade": {"type": "string", "description": "线索等级。"},
                "missing_fields": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "还需要追问的信息字段。",
                },
            },
            "required": ["customer_message", "industry", "lead_grade", "missing_fields"],
        },
        handler=_run_draft_sales_reply,
    ),
    "create_followup_plan": ToolSpec(
        name="create_followup_plan",
        description="根据线索等级生成销售跟进计划。",
        parameters={
            "type": "object",
            "properties": {
                "customer_name": {"type": "string", "description": "客户姓名或称呼。"},
                "need": {"type": "string", "description": "客户需求摘要。"},
                "lead_grade": {"type": "string", "description": "线索等级，例如 A-高意向。"},
                "owner": {"type": "string", "description": "跟进负责人。"},
            },
            "required": ["customer_name", "need", "lead_grade", "owner"],
        },
        handler=_run_create_followup_plan,
    ),
    "generate_sales_report": ToolSpec(
        name="generate_sales_report",
        description="从本地线索台账生成老板可读的销售线索日报。",
        parameters={
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "可选统计日期，格式 YYYY-MM-DD；为空表示全部线索。",
                },
                "owner": {
                    "type": "string",
                    "description": "日报汇报对象，例如老板、店长、销售主管。",
                },
            },
            "required": ["date", "owner"],
        },
        handler=_run_generate_sales_report,
    ),
    "import_leads": ToolSpec(
        name="import_leads",
        description="从本地 CSV、JSONL 或 JSON 文件批量导入销售线索，自动评分、记录，并按配置同步飞书。",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "本地线索文件路径。支持 .csv、.jsonl、.json。"},
                "max_rows": {"type": "integer", "description": "本次最多导入多少条，默认 100。"},
            },
            "required": ["file_path"],
        },
        handler=_run_import_leads,
    ),
    "list_hot_leads": ToolSpec(
        name="list_hot_leads",
        description="列出最近的 A 级高意向线索，方便销售优先跟进。",
        parameters={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "最多返回多少条 A 级线索。",
                },
            },
            "required": ["limit"],
        },
        handler=_run_list_hot_leads,
    ),
    "sync_lead_to_feishu": ToolSpec(
        name="sync_lead_to_feishu",
        description="把一条销售线索同步到飞书多维表格。需要先配置飞书应用和多维表格参数。",
        parameters={
            "type": "object",
            "properties": {
                "created_at": {"type": "string", "description": "线索创建时间。"},
                "customer_name": {"type": "string", "description": "客户姓名或称呼。"},
                "contact": {"type": "string", "description": "客户联系方式。"},
                "industry": {"type": "string", "description": "客户行业。"},
                "need": {"type": "string", "description": "客户需求。"},
                "budget": {"type": "string", "description": "预算。"},
                "timeline": {"type": "string", "description": "时间计划。"},
                "city": {"type": "string", "description": "城市/区域。"},
                "source": {"type": "string", "description": "线索来源。"},
                "grade": {"type": "string", "description": "线索等级。"},
                "notes": {"type": "string", "description": "补充备注。"},
            },
            "required": [
                "created_at",
                "customer_name",
                "contact",
                "industry",
                "need",
                "budget",
                "timeline",
                "city",
                "source",
                "grade",
                "notes",
            ],
        },
        handler=_run_sync_lead_to_feishu,
    ),
    "test_feishu_sync": ToolSpec(
        name="test_feishu_sync",
        description="向飞书多维表格写入一条测试线索，用于验收飞书同步配置。",
        parameters={
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "测试线索的客户名称。",
                },
            },
            "required": ["customer_name"],
        },
        handler=_run_test_feishu_sync,
    ),
    "inspect_feishu_fields": ToolSpec(
        name="inspect_feishu_fields",
        description="读取飞书多维表格字段名、字段 ID 和字段类型，用于排查 WrongRequestBody。",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        handler=_run_inspect_feishu_fields,
    ),
    "list_feishu_tables": ToolSpec(
        name="list_feishu_tables",
        description="读取飞书多维表格文件下的表名和 table_id，用于排查 WrongTableId 或误填 view_id。",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        handler=_run_list_feishu_tables,
    ),
}

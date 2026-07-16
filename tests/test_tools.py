import json

from graph_app.tools import (
    TOOL_REGISTRY,
    create_feishu_test_lead,
    draft_sales_reply,
    feishu_lead_fields,
    feishu_config_status,
    feishu_test_payload_preview,
    format_feishu_http_error,
    format_feishu_api_error,
    generate_sales_report,
    import_leads,
    inspect_feishu_fields,
    get_tool_schemas,
    list_hot_leads,
    list_feishu_tables,
    looks_like_feishu_view_id,
    feishu_field_name,
    qualify_lead,
    record_lead,
    run_tool,
    safe_calculate,
    sync_lead_to_feishu,
    text_stats,
    to_feishu_datetime_millis,
)


def test_safe_calculate_supports_basic_arithmetic():
    assert safe_calculate("1 + 2 * (3 + 4)") == 15


def test_safe_calculate_rejects_function_calls():
    try:
        safe_calculate("__import__('os').system('echo bad')")
    except ValueError as exc:
        assert "Only simple arithmetic" in str(exc)
    else:
        raise AssertionError("unsafe expression should fail")


def test_text_stats_counts_text_shape():
    result = text_stats("hello world\nhi")

    assert "14" in result
    assert "12" in result
    assert "3" in result
    assert "2" in result


def test_run_tool_dispatches_tools():
    assert run_tool("calculator", {"expression": "2 ** 5"}) == "32"
    assert "Asia/Shanghai" in run_tool("current_time", {"timezone": "Asia/Shanghai"})


def test_tool_schemas_are_derived_from_registry():
    schema_names = {schema["function"]["name"] for schema in get_tool_schemas()}

    assert schema_names == set(TOOL_REGISTRY)


def test_qualify_lead_scores_high_intent_lead():
    result = qualify_lead(
        industry="牙科",
        need="想做牙齿矫正",
        budget="2万左右",
        timeline="本周想预约",
        city="上海",
        contact="微信 abc123",
        source="表单",
    )

    assert "A-高意向" in result
    assert "10分钟内" in result


def test_draft_sales_reply_asks_missing_fields():
    result = draft_sales_reply(
        customer_message="想了解装修报价",
        industry="装修",
        lead_grade="B-需培育",
        missing_fields=["预算", "时间计划"],
    )

    assert "预算" in result
    assert "什么时候" in result


def test_record_lead_writes_jsonl(monkeypatch, tmp_path):
    lead_db = tmp_path / "leads.jsonl"
    monkeypatch.setenv("LEADS_DB", str(lead_db))

    result = record_lead(
        customer_name="张三",
        contact="13800000000",
        industry="留学",
        need="咨询英国硕士申请",
        budget="5万",
        timeline="今年",
        city="北京",
        source="网页表单",
        grade="A-高意向",
        notes="想尽快沟通",
    )

    assert "已记录线索" in result
    rows = lead_db.read_text(encoding="utf-8").splitlines()
    assert len(rows) == 1
    saved = json.loads(rows[0])
    assert saved["customer_name"] == "张三"
    assert saved["grade"] == "A-高意向"


def test_generate_sales_report_summarizes_leads(monkeypatch, tmp_path):
    lead_db = tmp_path / "leads.jsonl"
    monkeypatch.setenv("LEADS_DB", str(lead_db))

    record_lead("张三", "微信1", "牙科", "牙齿矫正", "2万", "本周", "上海", "网页表单", "A-高意向", "")
    record_lead("李四", "微信2", "装修", "旧房翻新", "待确认", "下月", "杭州", "微信", "B-需培育", "")
    record_lead("王五", "", "未知", "随便看看", "", "", "", "网页表单", "C-低意向/信息不足", "")

    report = generate_sales_report(date="", owner="老板")

    assert "总线索：3 条" in report
    assert "A级高意向：1 条" in report
    assert "B级需培育：1 条" in report
    assert "网页表单 2条" in report
    assert "张三" in report


def test_list_hot_leads_only_returns_a_grade(monkeypatch, tmp_path):
    lead_db = tmp_path / "leads.jsonl"
    monkeypatch.setenv("LEADS_DB", str(lead_db))

    record_lead("张三", "微信1", "牙科", "牙齿矫正", "2万", "本周", "上海", "网页表单", "A-高意向", "")
    record_lead("李四", "微信2", "装修", "旧房翻新", "待确认", "下月", "杭州", "微信", "B-需培育", "")

    hot_leads = list_hot_leads(limit=5)

    assert "张三" in hot_leads
    assert "李四" not in hot_leads


def test_import_leads_from_csv_scores_and_records(monkeypatch, tmp_path):
    lead_db = tmp_path / "leads.jsonl"
    import_file = tmp_path / "leads.csv"
    import_file.write_text(
        "\n".join(
            [
                "客户名称,联系方式,行业,需求,预算,时间计划,城市,来源",
                "张三,微信 abc123,牙科,想做牙齿矫正,2万左右,本周,上海,网页表单",
                "李四,13800000000,装修,旧房翻新,待确认,下月,杭州,广告投放",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("LEADS_DB", str(lead_db))
    monkeypatch.setenv("FEISHU_SYNC_ENABLED", "false")

    result = import_leads(str(import_file))

    assert "批量导入完成" in result
    assert "导入：2 条" in result
    rows = [json.loads(line) for line in lead_db.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 2
    assert rows[0]["customer_name"] == "张三"
    assert rows[0]["grade"].startswith("A")


def test_import_leads_from_jsonl_supports_alias_fields(monkeypatch, tmp_path):
    lead_db = tmp_path / "leads.jsonl"
    import_file = tmp_path / "leads.jsonl"
    import_file.write_text(
        json.dumps(
            {
                "姓名": "王五",
                "手机": "13900000000",
                "业务": "留学",
                "咨询内容": "咨询英国硕士申请",
                "渠道": "手工导入",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("LEADS_DB", str(lead_db))
    monkeypatch.setenv("FEISHU_SYNC_ENABLED", "false")

    result = import_leads(str(import_file))

    assert "导入：1 条" in result
    saved = json.loads(lead_db.read_text(encoding="utf-8").splitlines()[0])
    assert saved["customer_name"] == "王五"
    assert saved["industry"] == "留学"
    assert saved["source"] == "手工导入"


def test_feishu_lead_fields_uses_default_column_names():
    fields = feishu_lead_fields(
        {
            "created_at": "2026-07-17T00:00:00+08:00",
            "customer_name": "张三",
            "contact": "微信1",
            "industry": "牙科",
            "need": "牙齿矫正",
            "grade": "A-高意向",
        }
    )

    assert isinstance(fields["创建时间"], int)
    assert fields["客户名称"] == "张三"
    assert fields["联系方式"] == "微信1"
    assert fields["线索等级"] == "A-高意向"


def test_feishu_lead_fields_can_skip_created_at(monkeypatch):
    monkeypatch.setenv("FEISHU_FIELD_CREATED_AT", "__skip__")

    fields = feishu_lead_fields(
        {
            "created_at": "2026-07-17T00:00:00+08:00",
            "customer_name": "张三",
        }
    )

    assert feishu_field_name("FEISHU_FIELD_CREATED_AT", "创建时间") == ""
    assert "创建时间" not in fields
    assert fields["客户名称"] == "张三"


def test_to_feishu_datetime_millis_parses_iso_datetime():
    result = to_feishu_datetime_millis("2026-07-17T00:00:00+08:00")

    assert result == 1784217600000


def test_format_feishu_wrong_request_body_is_actionable():
    message = format_feishu_api_error({"code": 1254000, "msg": "WrongRequestBody"})

    assert "WrongRequestBody" in message
    assert "字段名不匹配" in message
    assert "FEISHU_FIELD_CREATED_AT=" in message


def test_sync_lead_to_feishu_reports_missing_config(monkeypatch):
    for name in [
        "FEISHU_APP_ID",
        "FEISHU_APP_SECRET",
        "FEISHU_BITABLE_APP_TOKEN",
        "FEISHU_BITABLE_TABLE_ID",
    ]:
        monkeypatch.delenv(name, raising=False)

    result = sync_lead_to_feishu({"customer_name": "张三"})

    assert "配置缺失" in result
    assert "app_id" in result


def test_sync_lead_to_feishu_posts_record(monkeypatch):
    requests = []

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return json.dumps(self.payload).encode("utf-8")

    def fake_urlopen(request, timeout):
        requests.append(request)
        if "tenant_access_token" in request.full_url:
            return FakeResponse({"code": 0, "tenant_access_token": "tenant-token"})
        return FakeResponse(
            {
                "code": 0,
                "data": {"record": {"record_id": "rec_123"}},
            }
        )

    monkeypatch.setenv("FEISHU_APP_ID", "app-id")
    monkeypatch.setenv("FEISHU_APP_SECRET", "app-secret")
    monkeypatch.setenv("FEISHU_BITABLE_APP_TOKEN", "app-token")
    monkeypatch.setenv("FEISHU_BITABLE_TABLE_ID", "tbl_123")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    result = sync_lead_to_feishu(
        {
            "customer_name": "张三",
            "contact": "微信1",
            "industry": "牙科",
            "need": "牙齿矫正",
            "grade": "A-高意向",
        }
    )

    assert result == "成功：record_id=rec_123"
    assert len(requests) == 2
    assert requests[0].full_url.endswith("/open-apis/auth/v3/tenant_access_token/internal")
    assert "/open-apis/bitable/v1/apps/app-token/tables/tbl_123/records" in requests[1].full_url
    assert requests[1].headers["Authorization"] == "Bearer tenant-token"


def test_feishu_config_status_masks_secrets(monkeypatch):
    monkeypatch.setenv("FEISHU_SYNC_ENABLED", "true")
    monkeypatch.setenv("FEISHU_APP_ID", "cli_abcdef123456")
    monkeypatch.setenv("FEISHU_APP_SECRET", "secret_abcdef123456")
    monkeypatch.setenv("FEISHU_BITABLE_APP_TOKEN", "appabcdef123456")
    monkeypatch.setenv("FEISHU_BITABLE_TABLE_ID", "tblabcdef123456")

    status = feishu_config_status()

    assert "FEISHU_SYNC_ENABLED: True" in status
    assert "cli_...3456" in status
    assert "secret_abcdef123456" not in status
    assert "必要配置：完整" in status


def test_feishu_config_status_warns_about_view_id(monkeypatch):
    monkeypatch.setenv("FEISHU_SYNC_ENABLED", "true")
    monkeypatch.setenv("FEISHU_APP_ID", "cli_abcdef123456")
    monkeypatch.setenv("FEISHU_APP_SECRET", "secret_abcdef123456")
    monkeypatch.setenv("FEISHU_BITABLE_APP_TOKEN", "appabcdef123456")
    monkeypatch.setenv("FEISHU_BITABLE_TABLE_ID", "vewabcdef123456")

    status = feishu_config_status()

    assert looks_like_feishu_view_id("vewabcdef123456")
    assert "视图 ID" in status
    assert "表 ID" in status


def test_create_feishu_test_lead_posts_record(monkeypatch):
    requests = []

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return json.dumps(self.payload).encode("utf-8")

    def fake_urlopen(request, timeout):
        requests.append(request)
        if "tenant_access_token" in request.full_url:
            return FakeResponse({"code": 0, "tenant_access_token": "tenant-token"})
        return FakeResponse({"code": 0, "data": {"record": {"record_id": "rec_test"}}})

    monkeypatch.setenv("FEISHU_APP_ID", "app-id")
    monkeypatch.setenv("FEISHU_APP_SECRET", "app-secret")
    monkeypatch.setenv("FEISHU_BITABLE_APP_TOKEN", "app-token")
    monkeypatch.setenv("FEISHU_BITABLE_TABLE_ID", "tbl_123")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    result = create_feishu_test_lead("测试客户")

    assert result == "成功：record_id=rec_test"
    assert len(requests) == 2


def test_feishu_test_payload_preview_contains_fields():
    payload = json.loads(feishu_test_payload_preview())

    assert "fields" in payload
    assert payload["fields"]["客户名称"] == "飞书测试客户"
    assert payload["fields"]["来源"] == "v22 飞书同步测试"


def test_inspect_feishu_fields_lists_remote_fields(monkeypatch):
    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return json.dumps(self.payload).encode("utf-8")

    def fake_urlopen(request, timeout):
        if "tenant_access_token" in request.full_url:
            return FakeResponse({"code": 0, "tenant_access_token": "tenant-token"})
        return FakeResponse(
            {
                "code": 0,
                "data": {
                    "items": [
                        {"field_name": "客户名称", "field_id": "fld1", "type": 1},
                        {"field_name": "创建时间", "field_id": "fld2", "type": 5},
                    ]
                },
            }
        )

    monkeypatch.setenv("FEISHU_APP_ID", "app-id")
    monkeypatch.setenv("FEISHU_APP_SECRET", "app-secret")
    monkeypatch.setenv("FEISHU_BITABLE_APP_TOKEN", "app-token")
    monkeypatch.setenv("FEISHU_BITABLE_TABLE_ID", "tbl_123")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    result = inspect_feishu_fields()

    assert "客户名称 | id=fld1 | type=1" in result
    assert "创建时间 | id=fld2 | type=5" in result
    assert "当前写入 payload 中缺少这些飞书字段" in result
    assert "联系方式" in result


def test_list_feishu_tables_lists_remote_table_ids(monkeypatch):
    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return json.dumps(self.payload).encode("utf-8")

    def fake_urlopen(request, timeout):
        if "tenant_access_token" in request.full_url:
            return FakeResponse({"code": 0, "tenant_access_token": "tenant-token"})
        return FakeResponse(
            {
                "code": 0,
                "data": {
                    "items": [
                        {"name": "线索表", "table_id": "tbl_123"},
                        {"name": "日报表", "table_id": "tbl_456"},
                    ]
                },
            }
        )

    monkeypatch.setenv("FEISHU_APP_ID", "app-id")
    monkeypatch.setenv("FEISHU_APP_SECRET", "app-secret")
    monkeypatch.setenv("FEISHU_BITABLE_APP_TOKEN", "app-token")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    result = list_feishu_tables()

    assert "线索表 | table_id=tbl_123" in result
    assert "日报表 | table_id=tbl_456" in result


def test_format_feishu_permission_error_is_actionable():
    body = json.dumps(
        {
            "code": 99991672,
            "msg": (
                "Access denied. One of the following scopes is required: "
                "[bitable:app, base:record:create]."
                "https://open.feishu.cn/app/cli_xxx/auth?q=bitable:app,base:record:create"
            ),
        }
    )

    message = format_feishu_http_error(400, body)

    assert "缺少多维表格写入权限" in message
    assert "bitable:app" in message
    assert "base:record:create" in message
    assert "https://open.feishu.cn/app/cli_xxx/auth" in message


def test_format_feishu_forbidden_error_is_actionable():
    body = json.dumps({"code": 91403, "msg": "Forbidden", "data": {}})

    message = format_feishu_http_error(403, body)

    assert "拒绝访问这个多维表格" in message
    assert "协作者" in message
    assert "app_token" in message
    assert "/feishu test" in message


def test_format_feishu_wrong_table_id_error_is_actionable():
    message = format_feishu_api_error({"code": 1254003, "msg": "WrongTableId"})

    assert "WrongTableId" in message
    assert "视图 ID" in message
    assert "FEISHU_BITABLE_TABLE_ID" in message

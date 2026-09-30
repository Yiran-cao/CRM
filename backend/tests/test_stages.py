"""阶段流转与操作日志测试"""


def _create_project(client, token, name="阶段测试项目"):
    resp = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "customer_name": name, "province": "广东", "city": "广州",
            "product": "MRI", "stage": 1, "budget": 50,
            "decision_makers": [
                {"department_name": "影像科", "contact_name": "王医生", "contact_info": "13900000000"}
            ],
        },
    )
    assert resp.status_code == 200
    return resp.json()["id"]


def test_stage_transition_creates_log(client, test_dealer):
    token = test_dealer["token"]
    pid = _create_project(client, token)

    # 阶段 1 → 2
    resp = client.put(
        f"/api/projects/{pid}",
        headers={"Authorization": f"Bearer {token}"},
        json={"stage": 2, "version": 0},
    )
    assert resp.status_code == 200
    assert resp.json()["stage"] == 2

    # 详情中的操作日志应包含：创建 + 阶段变更
    detail = client.get(f"/api/projects/{pid}", headers={"Authorization": f"Bearer {token}"}).json()
    field_names = [log["field_name"] for log in detail["operation_logs"]]
    assert "创建" in field_names
    assert "阶段" in field_names


def test_stage_log_contains_formatted_values(client, test_dealer):
    """阶段日志应包含【阶段1-潜在客户】修改为【阶段2-初步接触】格式"""
    token = test_dealer["token"]
    pid = _create_project(client, token)

    client.put(
        f"/api/projects/{pid}",
        headers={"Authorization": f"Bearer {token}"},
        json={"stage": 2, "version": 0},
    )

    detail = client.get(f"/api/projects/{pid}", headers={"Authorization": f"Bearer {token}"}).json()
    stage_log = [l for l in detail["operation_logs"] if l["field_name"] == "阶段"][0]
    assert "阶段1-潜在客户" in stage_log["old_value"]
    assert "阶段2-初步接触" in stage_log["new_value"]


def test_optimistic_lock_conflict(client, test_dealer):
    """版本号不符时返回 409，防止旧数据覆盖新数据"""
    token = test_dealer["token"]
    pid = _create_project(client, token)

    # 用错误版本号（99）更新，应返回 409
    resp = client.put(
        f"/api/projects/{pid}",
        headers={"Authorization": f"Bearer {token}"},
        json={"stage": 3, "version": 99},
    )
    assert resp.status_code == 409


def test_admin_read_only(client):
    """管理员不可编辑项目"""
    admin = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert admin.status_code == 200
    token = admin.json()["access_token"]

    # 管理员创建的项目（用 dealer 创建后管理员尝试编辑会先403）
    resp = client.put(
        "/api/projects/999",
        headers={"Authorization": f"Bearer {token}"},
        json={"stage": 2, "version": 0},
    )
    # 管理员直接返回 403（角色检查在项目存在性检查之前）
    assert resp.status_code == 403

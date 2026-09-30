"""报表提交校验测试"""


def _create_project(client, token, name):
    resp = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "customer_name": name, "province": "上海", "city": "浦东新区",
            "product": "监护仪", "stage": 1, "budget": 10,
            "decision_makers": [
                {"department_name": "ICU", "contact_name": "赵医生", "contact_info": "13700000000"}
            ],
        },
    )
    assert resp.status_code == 200
    return resp.json()["id"]


def test_cannot_submit_with_insufficient_points(client, test_dealer):
    token = test_dealer["token"]
    _create_project(client, token, "低积分项目")
    resp = client.post("/api/reports/submit", headers={"Authorization": f"Bearer {token}"}, json={})
    assert resp.status_code == 400
    assert "至少 5 分" in resp.json()["detail"]


def test_can_submit_with_enough_points(client, test_dealer):
    token = test_dealer["token"]
    # 创建5个项目并逐个确认无变化，累计5分
    for i in range(5):
        pid = _create_project(client, token, f"项目{i}")
        client.post(f"/api/projects/{pid}/confirm", headers={"Authorization": f"Bearer {token}"})

    status = client.get("/api/reports/status", headers={"Authorization": f"Bearer {token}"}).json()
    assert status["total_points"] >= 5
    assert status["can_submit"] is True

    resp = client.post("/api/reports/submit", headers={"Authorization": f"Bearer {token}"}, json={})
    assert resp.status_code == 200


def test_duplicate_submit_rejected(client, test_dealer):
    token = test_dealer["token"]
    for i in range(5):
        pid = _create_project(client, token, f"重复提交项目{i}")
        client.post(f"/api/projects/{pid}/confirm", headers={"Authorization": f"Bearer {token}"})

    # 第一次提交成功
    assert client.post("/api/reports/submit", headers={"Authorization": f"Bearer {token}"}, json={}).status_code == 200
    # 第二次提交被拒
    resp = client.post("/api/reports/submit", headers={"Authorization": f"Bearer {token}"}, json={})
    assert resp.status_code == 400
    assert "已提交过" in resp.json()["detail"]

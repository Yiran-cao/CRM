"""积分计算测试"""
import pytest


def _create_project(client, token, name="测试项目"):
    resp = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "customer_name": name, "province": "北京", "city": "朝阳区",
            "product": "CT", "stage": 1, "budget": 100,
            "decision_makers": [
                {"department_name": "影像科", "contact_name": "李医生", "contact_info": "13800000000"}
            ],
        },
    )
    assert resp.status_code == 200
    return resp.json()["id"]


def _get_status(client, token):
    return client.get("/api/reports/status", headers={"Authorization": f"Bearer {token}"}).json()


@pytest.fixture()
def dealer(client, test_dealer):
    return test_dealer


def test_confirm_no_change_adds_one_point(client, dealer):
    token = dealer["token"]
    pid = _create_project(client, token)
    assert _get_status(client, token)["total_points"] == 0

    resp = client.post(f"/api/projects/{pid}/confirm", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert _get_status(client, token)["total_points"] == 1


def test_stage_update_adds_one_point(client, dealer):
    token = dealer["token"]
    pid = _create_project(client, token)
    assert _get_status(client, token)["total_points"] == 0

    resp = client.put(
        f"/api/projects/{pid}",
        headers={"Authorization": f"Bearer {token}"},
        json={"stage": 2, "version": 0},
    )
    assert resp.status_code == 200
    assert _get_status(client, token)["total_points"] == 1


def test_non_stage_update_also_adds_point(client, dealer):
    """编辑任意字段均触发积分+1（每完成1项更新+1分）"""
    token = dealer["token"]
    pid = _create_project(client, token)

    resp = client.put(
        f"/api/projects/{pid}",
        headers={"Authorization": f"Bearer {token}"},
        json={"remark": "修改备注", "version": 0},
    )
    assert resp.status_code == 200
    assert _get_status(client, token)["total_points"] == 1


def test_create_project_no_points(client, dealer):
    """新建项目不加分（仅更新操作加分）"""
    token = dealer["token"]
    _create_project(client, token)
    assert _get_status(client, token)["total_points"] == 0

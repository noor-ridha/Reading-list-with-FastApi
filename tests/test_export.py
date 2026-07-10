def test_export_job_lifecycle(client, register_and_login):
    headers = register_and_login("henry@test.com")

    list_resp = client.post("/lists", json={"name": "Export test list"}, headers=headers)
    list_id = list_resp.json()["id"]

    client.post(
        f"/lists/{list_id}/items",
        json={"title": "Book One", "status": "reading"},
        headers=headers,
    )

    export_resp = client.post(
        f"/lists/{list_id}/export", json={"format": "json"}, headers=headers
    )
    assert export_resp.status_code == 202
    job_id = export_resp.json()["id"]
    assert export_resp.json()["status"] == "pending"

    status_resp = client.get(f"/exports/{job_id}", headers=headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] in ("pending", "processing", "completed")


def test_export_job_forbidden_for_other_user(client, register_and_login):
    headers_a = register_and_login("iris@test.com")
    headers_b = register_and_login("jack@test.com")

    list_resp = client.post("/lists", json={"name": "Iris's list"}, headers=headers_a)
    list_id = list_resp.json()["id"]

    export_resp = client.post(
        f"/lists/{list_id}/export", json={"format": "json"}, headers=headers_a
    )
    job_id = export_resp.json()["id"]

    forbidden_resp = client.get(f"/exports/{job_id}", headers=headers_b)
    assert forbidden_resp.status_code == 404
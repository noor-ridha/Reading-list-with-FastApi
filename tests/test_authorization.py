def test_user_cannot_access_another_users_list(client, register_and_login):
    headers_a = register_and_login("usera@test.com")
    headers_b = register_and_login("userb@test.com")

    create_resp = client.post(
        "/lists", json={"name": "A's private list"}, headers=headers_a
    )
    list_id = create_resp.json()["id"]

    get_resp = client.get(f"/lists/{list_id}", headers=headers_b)
    assert get_resp.status_code == 404

    delete_resp = client.delete(f"/lists/{list_id}", headers=headers_b)
    assert delete_resp.status_code == 404

    owner_get = client.get(f"/lists/{list_id}", headers=headers_a)
    assert owner_get.status_code == 200


def test_user_cannot_add_item_to_others_list(client, register_and_login):
    headers_a = register_and_login("frank@test.com")
    headers_b = register_and_login("grace@test.com")

    list_resp = client.post("/lists", json={"name": "Frank's list"}, headers=headers_a)
    list_id = list_resp.json()["id"]

    add_item_resp = client.post(
        f"/lists/{list_id}/items",
        json={"title": "Intruder book", "status": "want_to_read"},
        headers=headers_b,
    )
    assert add_item_resp.status_code == 404


def test_unauthenticated_access_rejected(client):
    resp = client.get("/lists")
    assert resp.status_code == 401
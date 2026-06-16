def test_admin_login(client):
    register_response = client.post(
        "/auth/register",
        json={
            "name": "Admin User",
            "email": "admin@lms.com",
            "password": "admin123",
            "role": "admin",
        },
    )

    assert register_response.status_code == 200

    response = client.post(
        "/auth/login",
        json={
            "email": "admin@lms.com",
            "password": "admin123",
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["role"] == "admin"

import httpx

BASE_URL = "http://127.0.0.1:8000"

def test_admin_login():
    response = httpx.post(
        f"{BASE_URL}/auth/login",
        params={
            "email": "admin@lms.com",
            "password": "admin123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
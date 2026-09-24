"""Đăng nhập / đăng xuất — ca A-19 → A-22 của 05-API.md §10."""
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class AuthTests(APITestCase):
    PASSWORD = "doi-mat-khau-nay"   # mật khẩu seed ở users/migrations/0002_seed_users.py

    def login(self, username, password):
        return self.client.post("/api/auth/login", {"username": username, "password": password},
                                format="json")

    def test_A19_login_returns_token_and_user(self):
        response = self.login("admin", self.PASSWORD)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["token"]), 40)
        self.assertEqual(response.data["user"],
                         {"id": 1, "username": "admin", "full_name": "Lưu Đức Anh", "role": "ADMIN"})

    def test_login_twice_returns_same_token(self):
        first = self.login("admin", self.PASSWORD).data["token"]
        second = self.login("admin", self.PASSWORD).data["token"]
        self.assertEqual(first, second)

    def test_A20_wrong_password_and_unknown_user_share_one_message(self):
        wrong_password = self.login("admin", "sai")
        unknown_user = self.login("khong-ton-tai", self.PASSWORD)
        for response in (wrong_password, unknown_user):
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.data["error"]["code"], "INVALID_CREDENTIALS")
        self.assertEqual(wrong_password.data["error"]["message"], unknown_user.data["error"]["message"])

    def test_login_missing_field_is_validation_error(self):
        response = self.client.post("/api/auth/login", {"username": "admin"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("password", response.data["error"]["details"])

    def test_login_ignores_revoked_token_in_header(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + "0" * 40)
        self.assertEqual(self.login("admin", self.PASSWORD).status_code, 200)

    def test_A21_missing_token_is_401_not_403(self):
        response = self.client.get("/api/sensors")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error"]["code"], "UNAUTHENTICATED")
        self.assertEqual(response["WWW-Authenticate"], "Token")

    def test_A22_logout_revokes_token(self):
        token = self.login("admin", self.PASSWORD).data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

        self.assertEqual(self.client.post("/api/auth/logout").status_code, 204)
        self.assertFalse(Token.objects.filter(key=token).exists())
        self.assertEqual(self.client.get("/api/devices").status_code, 401)

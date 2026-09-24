"""Tiện ích dùng chung cho các file tests.py."""
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.users.models import User


class LoggedInAPITestCase(APITestCase):
    """Mọi request mặc định gửi kèm token của `admin` — đúng quy ước 05-API.md §10.

    Hai tài khoản `admin` và `operator` có sẵn nhờ migration seed (users/0002).
    """

    def setUp(self):
        self.admin = User.objects.get(username="admin")
        self.operator = User.objects.get(username="operator")
        self.login_as(self.admin)

    def login_as(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def logout(self):
        self.client.credentials()

    def assertError(self, response, status_code, code):
        """Kiểm mã HTTP và hình dạng lỗi thống nhất {error:{code,message,details}}."""
        self.assertEqual(response.status_code, status_code, response.content)
        self.assertEqual(set(response.data), {"error"})
        self.assertEqual(response.data["error"]["code"], code)
        self.assertTrue(response.data["error"]["message"])
        return response.data["error"]

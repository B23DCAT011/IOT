"""Đăng nhập / đăng xuất bằng token của DRF — 05-API.md §4.8, §4.9, §7.7."""
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.schema import error_responses
from config.exceptions import InvalidCredentials

from .serializers import LoginRequestSerializer, LoginResponseSerializer, LoginUserSerializer


class LoginView(APIView):
    permission_classes = [AllowAny]
    # Không xác thực ở view này: trình duyệt còn giữ token đã thu hồi mà vẫn gửi kèm
    # thì TokenAuthentication trả 401 trước khi view chạy → không đăng nhập lại được.
    authentication_classes = []

    @extend_schema(
        request=LoginRequestSerializer,
        responses={200: LoginResponseSerializer, **error_responses(400)},
        examples=[OpenApiExample("Tài khoản admin",
                                 value={"username": "admin", "password": "doi-mat-khau-nay"},
                                 request_only=True)],
        auth=[],
        tags=["Auth"],
    )
    def post(self, request):
        credentials = LoginRequestSerializer(data=request.data)
        credentials.is_valid(raise_exception=True)                    # 400 VALIDATION_ERROR

        # None khi sai tên, sai mật khẩu, HOẶC tài khoản bị khoá — cùng một thông báo
        # cho cả ba để người ngoài không dò ra tên tài khoản nào tồn tại.
        user = authenticate(request, **credentials.validated_data)
        if user is None:
            raise InvalidCredentials()                                # 400 INVALID_CREDENTIALS

        # Mỗi người dùng MỘT token dùng chung mọi tab/máy → đăng xuất một nơi là mất ở mọi nơi.
        token, _ = Token.objects.get_or_create(user=user)
        update_last_login(None, user)
        return Response({"token": token.key, "user": LoginUserSerializer(user).data})


class LogoutView(APIView):
    """Thu hồi token đang dùng. Thiếu/sai token thì IsAuthenticated trả 401 trước khi vào hàm."""

    @extend_schema(request=None, responses={204: None, **error_responses(401)}, tags=["Auth"])
    def post(self, request):
        request.auth.delete()          # request.auth chính là đối tượng Token
        return Response(status=status.HTTP_204_NO_CONTENT)

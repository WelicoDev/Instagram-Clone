from tokenize import TokenError

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from shared.utility import send_email, send_phone, check_email_or_phone
from .serializers import SignUpSerializers, ChangeUserInformation, ChangeUserPhotoSerializers, LoginSerializers,\
    LoginRefreshSerializer, LogoutSerializer, ForgetPasswordSerializer, ResetPasswordSerializer

from .models import User,  NEW, CODE_VERIFIED, DONE ,PHOTO_STEP, VIA_EMAIL, VIA_PHONE
from datetime import datetime
from rest_framework.views import APIView
from .tasks import send_email_task, send_phone_task


class CreateUserView(CreateAPIView):
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = SignUpSerializers

class VerifyApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = self.request.user
        code = self.request.data.get("code")

        # Kodni tekshirish
        check_result = self.check_verify(user, code)
        if isinstance(check_result, ValidationError):
            # Agar xato bo'lsa, xato ma'lumotni qaytaramiz
            raise check_result  # ValidationError'ni raise qilamiz

        data = {
            "success": True,
            "auth_status": user.auth_status,
            "access": user.token()["access"] if user.token() else None,
            "refresh": user.token()["refresh_token"] if user.token() else None
        }

        return Response(data)

    @staticmethod
    def check_verify(user, code):
        # Noto'g'ri yoki muddati o'tgan kodni tekshirish
        verifies = user.verify_codes.filter(expiration_time__gte=datetime.now(), code=code, is_confirmed=False)
        if not verifies.exists():
            data = {
                "success": False,
                "message": "Your verification code is invalid or out of date."
            }

            raise ValidationError(data)  # Xatolikni raise qilish

        # Kod tasdiqlangan bo'lsa, uni yangilash
        verify = verifies.first()
        if verify.is_confirmed:
            # Agar kod allaqachon tasdiqlangan bo'lsa, xato qaytarish
            data = {
                "success": False,
                "message": "Your verification code has already been used."
            }
            raise ValidationError(data)  # Xatolikni raise qilish

        # Kodni tasdiqlash
        verify.is_confirmed = True
        verify.save()

        # Foydalanuvchi statusini yangilash
        if user.auth_status == NEW:
            user.auth_status = CODE_VERIFIED
            user.save()

        return True


class GetNewVerification(APIView):

    def get(self, request, *args, **kwargs):
        user = self.request.user
        self.check_verification(user)
        if user.auth_type == VIA_EMAIL:
            code = user.create_verify_code(VIA_EMAIL)
            send_email_task.delay(user.email, code)
        elif user.auth_type == VIA_PHONE:
            code = user.create_verify_code(VIA_PHONE)
            send_phone_task.delay(user.phone, code)
        else:
            data = {
                "success":False,
                "message":"email or phone number is invalid."
            }

            raise ValidationError(data)

        data = {
            "success":True,
            "message":"Your verification code has been resent."
        }
        return Response(data)

    @staticmethod
    def check_verification(user):
        verifies = user.verify_codes.filter(expiration_time__gte = datetime.now(), is_confirmed=False)
        if verifies.exists():
            data = {
                "success":False,
                "message":"Your code is valid . Wait for server !"
            }

            raise ValidationError(data)


class ChangeUserInformationView(UpdateAPIView):
    permission_classes = [IsAuthenticated,]
    queryset = User.objects.all()
    serializer_class = ChangeUserInformation
    http_method_names = ['patch', 'put']

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        super(ChangeUserInformationView, self).update(request, *args, **kwargs)

        data = {
            "success":True,
            "message":"User updated successfully!",
            "auth_status":self.request.user.auth_status,
        }
        return Response(data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        super(ChangeUserInformationView, self).partial_update(request, *args, **kwargs)

        data = {
            "success":True,
            "message":"User updated successfully!",
            "auth_status":self.request.user.auth_status,
        }
        return Response(data, status=status.HTTP_200_OK)

class ChangeUserPhotoView(APIView):
    permission_classes = [IsAuthenticated,]

    def put(self, request, *args, **kwargs):
        serializer = ChangeUserPhotoSerializers(data=request.data)
        if serializer.is_valid():
            user = request.user
            serializer.update(user, serializer.validated_data)

            data = {
                "success":True,
                "message":"Picture successfully changed."
            }
            return Response(data, status=status.HTTP_200_OK)

        error = {
            "success":False,
            "message":serializer.errors
        }
        return Response(error, status=status.HTTP_400_BAD_REQUEST)


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializers


class LoginRefreshView(TokenRefreshView):
    serializer_class = LoginRefreshSerializer

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, refresh, *args, **kwargs):
        serializer = self.serializer_class(data=self.request.data)

        serializer.is_valid(raise_exception=True)
        try:
            refresh_token = self.request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            data = {
                "success":True,
                "message":"You are successfully logout."
            }
            return Response(data, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class ForgetPasswordView(APIView):
    permission_classes = [AllowAny,]
    serializer_class = ForgetPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=self.request.data)

        serializer.is_valid(raise_exception=True)
        email_or_phone = serializer.validated_data.get("email_or_phone")
        user = serializer.validated_data.get("user")
        if check_email_or_phone(email_or_phone) == "phone":
            code = user.create_verify_code(VIA_PHONE)
            send_phone(email_or_phone, code)
        elif check_email_or_phone(email_or_phone) == "email":
            code = user.create_verify_code(VIA_EMAIL)
            send_email(email_or_phone, code)

        data = {
            "success":True,
            "message":"Your confirmed code successfully send.",
            "access":user.token()["access"],
            "refresh":user.token()["refresh_token"],
            "user_status": user.auth_status
        }
        return Response(data, status=status.HTTP_200_OK)

class ResetPasswordView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ResetPasswordSerializer
    http_method_names = ['patch', 'put']

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        response = super(ResetPasswordView, self).update(request, *args, **kwargs)
        try:
            user = User.objects.get(id=response.data.get('id'))
        except ObjectDoesNotExist as e:
            raise NotFound(detail="User Not Found.")

        data = {
            "success":True,
            "message":"Password successfully updated",
            "access":user.token()['access'],
            "refresh":user.token()["refresh_token"]
        }
        return Response(data)

from typing import Dict, Any

from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken

from .models import User, VIA_EMAIL, VIA_PHONE, NEW, CODE_VERIFIED, DONE, PHOTO_STEP
from .tasks import send_email_task, send_phone_task
from rest_framework.validators import ValidationError
from shared.utility import check_email_or_phone, check_user_type
from django.core.validators import FileExtensionValidator


class UserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = User
        fields = ('id', 'username', 'photo')


class SignUpSerializers(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    def __init__(self, *args, **kwargs):
        super(SignUpSerializers, self).__init__(*args, **kwargs)
        self.fields["email_phone_number"] = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'auth_type',
            'auth_status',
        )
        extra_kwargs = {
            "auth_type":{
                "read_only":True,
                "required":False
            },
            "auth_status":{
                "read_only":True,
                "required":False
            },
        }
    def create(self, validated_data):
        user = super(SignUpSerializers, self).create(validated_data)
        if user.auth_type == VIA_EMAIL:
            code = user.create_verify_code(VIA_EMAIL)
            send_email_task.delay(user.email, code)
        elif user.auth_type == VIA_PHONE:
            code = user.create_verify_code(VIA_PHONE)
            send_phone_task.delay(user.phone, code)
        user.save()

        return user


    def validate(self, data):
        super(SignUpSerializers, self).validate(data)
        data = self.auth_validate(data)

        return data


    @staticmethod
    def auth_validate(data):
        user_input = str(data.get("email_phone_number")).lower()
        input_type = check_email_or_phone(user_input)
        if input_type == "email":
            data = {
                "email":user_input,
                "auth_type":VIA_EMAIL
            }
        elif input_type == "phone":
            data = {
                "phone":user_input,
                "auth_type":VIA_PHONE
            }
        else:
            data = {
                "success":False,
                "message":"You must sent email or phone number"
            }
            raise ValidationError(data)

        return data

    def validate_email_phone_number(self, value):
        value = value.lower()
        if value and User.objects.filter(email=value).exists():
            data = {
                "success":False,
                "message":"Email already use."
            }
            raise ValidationError(data)
        elif value and User.objects.filter(phone=value).exists():
            data = {
                "success": False,
                "message": "Phone number already use."
            }
            raise ValidationError(data)

        return value

    def to_representation(self, instance):
        data = super(SignUpSerializers, self).to_representation(instance)
        data.update(instance.token())

        return data



class ChangeUserInformation(serializers.Serializer):
    first_name = serializers.CharField(write_only=True, required=True)
    last_name = serializers.CharField(write_only=True, required=True)
    username = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True,required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        if password != confirm_password:
            error = {
                "success":False,
                "message":"passwords do not match."
            }
            raise ValidationError(error)

        if password:
            validate_password(password)
            validate_password(confirm_password)

        return data

    def validate_username(self, username):
        if len(username) <= 4 or len(username) >= 32:
            error = {
                "success":False,
                "message": "Username length cannot be less than 4 or greater than 32."
            }
            raise ValidationError(error)

        if username.isdigit():
            error = {
                "success": False,
                "message": "This username is entirely numeric."
            }
            raise ValidationError(error)

        return username

    def validate_last_name(self, last_name):
        if len(last_name) <= 4 or len(last_name) >= 32:
            error = {
                "success":False,
                "message": "Last name length cannot be less than 4 or greater than 32."
            }
            raise ValidationError(error)

        if last_name.isdigit():
            error = {
                "success": False,
                "message": "This last name is entirely numeric."
            }
            raise ValidationError(error)

        if last_name[0].islower():
            last_name = last_name.capitalize()

        return last_name

    def validate_first_name(self, first_name):
        if len(first_name) <= 4 or len(first_name) >= 32:
            error = {
                "success": False,
                "message": "First Name length cannot be less than 4 or greater than 32."
            }
            raise ValidationError(error)

        if first_name.isdigit():
            error = {
                "success": False,
                "message": "This first name is entirely numeric."
            }
            raise ValidationError(error)

        if first_name[0].islower():
            first_name = first_name.capitalize()

        return first_name

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.username = validated_data.get('username', instance.username)
        instance.password = validated_data.get('password', instance.password)

        if validated_data.get('password'):
            instance.set_password(validated_data.get('password'))

        if instance.auth_status == CODE_VERIFIED:
            instance.auth_status = DONE

        instance.save()
        return instance

class ChangeUserPhotoSerializers(serializers.Serializer):
    photo = serializers.ImageField(validators=[FileExtensionValidator(allowed_extensions=['jpg' , 'jpeg' , 'png' , 'heic' ,'heif' , 'webp' ,'svg'])])

    def update(self, instance, validated_data):
        photo = validated_data.get('photo')
        if photo:
            instance.photo = photo
            instance.auth_status = PHOTO_STEP
            instance.save()
        return instance

class LoginSerializers(TokenObtainPairSerializer):

    def __init__(self, *args, **kwargs):
        super(LoginSerializers, self).__init__(*args, **kwargs)
        self.fields['userinput'] = serializers.CharField(required=True)
        self.fields['username'] = serializers.CharField(required=False, read_only=True)

    def auth_validate(self, data):
        user_input = data.get('userinput')
        if check_user_type(user_input) == "username":
            username  = user_input
        elif check_user_type(user_input) == "email":
            user = self.get_user(email__iexact=user_input)
            username = user.username
        elif check_user_type(user_input) == "phone":
            # Telefon raqami bo'yicha foydalanuvchini tekshirish
            user = self.get_user(phone=user_input)
            username = user.username  # Telefon raqami bilan username olish
        else:
            error = {
                "success": False,
                "message": "You need to enter email, phone number, or username."
            }
            raise ValidationError(error)

        authentication_kwargs = {
            self.username_field: username,
            "password": data["password"]
        }

        # Foydalanuvchini tekshirish
        current_user = User.objects.filter(username__exact=username).first()
        if current_user is not None and current_user.auth_status in [NEW, CODE_VERIFIED]:
            error = {
                "success": False,
                "message": "You are not fully registered."
            }
            raise ValidationError(error)

        user = authenticate(**authentication_kwargs)

        if user is not None:
            self.user = user
        else:
            error = {
                "success": False,
                "message": "Sorry, login or password you entered is incorrect. Please check and try again."
            }
            raise ValidationError(error)

    def validate(self, data):
        self.auth_validate(data)
        if self.user.auth_status not in [DONE, PHOTO_STEP]:
            raise PermissionDenied("You cannot login! You don't have permission.")

        data = self.user.token()
        data["auth_status"] = self.user.auth_status
        data["full_name"] = self.user.full_name

        return data

    def get_user(self, **kwargs):
        users = User.objects.filter(**kwargs)
        if not users.exists():
            error = {
                "success": False,
                "message": "No active account found."
            }
            raise ValidationError(error)

        return users.first()

class LoginRefreshSerializer(TokenRefreshSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        access_token_instance = AccessToken(data["access"])
        user_id = access_token_instance['user_id']
        user = get_object_or_404(User, id=user_id)
        update_last_login(None, user)

        return data

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ForgetPasswordSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email_or_phone = attrs.get("email_or_phone", None)

        if email_or_phone is None:
            error = {
                "success":False,
                "message":"Email or phone number required."
            }

            raise ValidationError(error)

        user = User.objects.filter(Q(phone=email_or_phone) | Q(email=email_or_phone))
        if not user.exists():
            raise NotFound(detail="User Not Found.")
        attrs['user'] = user.first()

        return attrs

class ResetPasswordSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    password = serializers.CharField(min_length=8, required=True, write_only=True)
    confirm_password = serializers.CharField(min_length=8, required=True, write_only=True)

    class Meta:
        model = User
        fields = ("id",
                  "password",
                  "confirm_password"
                  )

        def validate(self, data):
            password = data.get("password", None)
            confirm_password = data.get("confirm_password", None)
            if password != confirm_password:
                error = {
                    "success":False,
                    "message":"The passwords do not match."
                }
                raise ValidationError(error)

            if password:
                validate_password(password)
            return data

        def update(self, instance, validated_data):
            password = validated_data.pop('password')
            instance.set_password(password)

            return super(ResetPasswordSerializer, self).update(instance, validated_data)

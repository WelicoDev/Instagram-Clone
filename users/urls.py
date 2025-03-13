from django.urls import path
from .views import CreateUserView, VerifyApiView, GetNewVerification, ChangeUserInformationView, \
    ChangeUserPhotoView, LoginView, LoginRefreshView, LogoutView, ForgetPasswordView, ResetPasswordView


urlpatterns = [
    path('login/', LoginView.as_view(), name="login"),
    path('login/refresh/', LoginRefreshView.as_view(),name="login_refresh"),
    path('logout/', LogoutView.as_view(), name="logout"),
    path('forget/password/', ForgetPasswordView.as_view(), name="forget_password"),
    path('reset/password/',ResetPasswordView.as_view(), name="reset_password"),
    path('signup/', CreateUserView.as_view(), name="create_users"),
    path('verify/', VerifyApiView.as_view(), name="verify_users"),
    path('verify/resent/', GetNewVerification.as_view(), name="verify_resent"),
    path('change/', ChangeUserInformationView.as_view(), name="change_user"),
    path('change/photo/', ChangeUserPhotoView.as_view(), name="change_photo"),
]
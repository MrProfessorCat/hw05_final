from django.contrib.auth import views as django_views
from django.urls import path, reverse_lazy

from . import views


app_name = 'users'


urlpatterns = [
    path('login/',
         django_views.LoginView.as_view(template_name='users/login.html'),
         name='login'),

    path('logout/', django_views.LogoutView.as_view(
        template_name='users/logged_out.html'),
        name='logout'),

    path('signup/', views.SignUp.as_view(), name='signup'),

    path(
        'password_reset/',
        django_views.PasswordResetView.as_view(
            template_name='users/password_reset_form.html',
            success_url=reverse_lazy('users:password_reset_done')),
        name='password_reset_form'),

    path(
        'password_reset/done/',
        django_views.PasswordResetDoneView.as_view(
            template_name='users/password_reset_done.html'),
        name='password_reset_done'),

    path(
        'reset/<uidb64>/<token>/',
        django_views.PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html',
            success_url=reverse_lazy('users:password_reset_complete')),
        name='password_reset_confirm'
    ),

    path(
        'reset/done/',
        django_views.PasswordResetCompleteView.as_view(
            template_name='users/password_reset_complete.html'),
        name='password_reset_complete'),

    path(
        'password_change/',
        django_views.PasswordChangeView.as_view(
            template_name='users/password_change_form.html',
            success_url=reverse_lazy('users:password_change_done')),
        name='password_change'),

    path(
        'password_change/done/',
        django_views.PasswordChangeDoneView.as_view(
            template_name='users/password_change_done.html'),
        name='password_change_done'),
]

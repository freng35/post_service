from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path
from .views import *
from django.contrib.auth import views as au_views


urlpatterns = [
    path('', index),
    path('create/', create_voting),
    path('voting/<int:voting_id>/', voting),
    path('vote/<int:answer>/', vote),
    path('like/<int:voting_id>/', like),
    path('login/', au_views.LoginView.as_view()),
    path('logout/', au_views.LogoutView.as_view()),
    path('register/', RegisterFormView.as_view()),
    path('profile/<int:user_id>/', profile),
    path('profile/<int:user_id>/edit/', edit_profile),
    path('voting/<int:voting_id>/edit/', voting_edit),
    path('delete/<int:voting_id>/', delete_voting),
    path('voting/<int:voting_id>/send_report/', send_report),
    path('reports/', reports),
    path('reports/<int:report_id>/delete/', close_report),
    path('login/pass-reset/', au_views.PasswordResetView.as_view(template_name='pass_reset.html'), name='pass-reset'),
    path('password_reset_confirm/<uidb64>/<token>/',
         au_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password_reset/done/',
         au_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'),
         name='password_reset_done'),
    path('password_reset_complete/',
         au_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),
         name='password_reset_complete'),
]


if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns() + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

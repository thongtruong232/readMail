from django.urls import path
from mail.views import home_view, get_code_view

urlpatterns = [
    path('', home_view, name='home'),
    path('get_code/', get_code_view, name='get_code'),
] 
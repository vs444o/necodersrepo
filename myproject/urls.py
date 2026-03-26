"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from offers import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('find/', views.find, name='find'),
    path('post/', views.post_offer, name='post_offer'),
    path('offer/<int:pk>/accept/', views.accept_offer, name='accept_offer'),  
    path('offer/<int:pk>/complete/', views.complete_offer, name='complete_offer'),
    path('offer/<int:pk>/apply/', views.apply_offer, name='apply_offer'),
    path('signup/', views.signup_view, name='signup'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('my-posts/', views.my_posts, name='my_posts'),
    path('application/<int:pk>/accept/', views.accept_application, name='accept_application'),
    path('my-jobs/', views.my_jobs, name='my_jobs'),
]

from django.urls import path,include
from .views import SendOTPView, VerifyOTPView,TaskCreateView, TaskListView, TaskUpdateView,TestView,AuditLogViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')

urlpatterns = [
    path('send-otp/', SendOTPView.as_view()),
    path('verify-otp/', VerifyOTPView.as_view()),
    path('tasks/create/', TaskCreateView.as_view()),
    path('tasks/', TaskListView.as_view()),
    path('tasks/<int:pk>/', TaskUpdateView.as_view()),
    path('test/', TestView.as_view()),
    path('', include(router.urls)),
 
]

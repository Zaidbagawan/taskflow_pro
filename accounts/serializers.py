from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import AuditLog
from django.utils import timezone
from .models import Task

class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower()
    
class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        if not data['otp'].isdigit():
            raise serializers.ValidationError("OTP must be numeric")
        return data
    
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'is_verified']

class TaskSerializer(serializers.ModelSerializer):
    assigned_to_email = serializers.ReadOnlyField(source='assigned_to.email')

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['created_by']

    #  Validation (ONLY assign to employee)
    def validate_assigned_to(self, value):
        if value.role != 'user':
            raise serializers.ValidationError("Can only assign to employees")
        return value
    
class AuditLogSerializer(serializers.ModelSerializer):
    formatted_time = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'user_email',
            'action',
            'action_type',
            'model_name',
            'object_id',
            'field_name',
            'old_value',
            'new_value',
            'formatted_time'
        ]

    def get_formatted_time(self, obj):
        from django.utils import timezone
        local_time = timezone.localtime(obj.timestamp)
        return local_time.strftime("%d-%m-%Y %I:%M %p")
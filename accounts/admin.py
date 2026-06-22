from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import User, OTP, Task, AuditLog

User = get_user_model()


#  Custom User Admin
class CustomUserAdmin(UserAdmin):

    list_display = ('username', 'email', 'role', 'is_verified')

    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('role', 'is_verified'),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {
            'fields': ('role', 'is_verified'),
        }),
    )

    # CREATE / UPDATE
    def save_model(self, request, obj, form, change):
        obj._current_user = request.user

        if not change:
            existing_user = User.objects.filter(email=obj.email).first()
            if existing_user:
                obj.id = existing_user.id

        super().save_model(request, obj, form, change)

    #  DELETE
    def delete_model(self, request, obj):
        obj._current_user = request.user
        super().delete_model(request, obj)


admin.site.register(User, CustomUserAdmin)


#  OTP Admin
admin.site.register(OTP)


#  Task Admin
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'assigned_to', 'created_by', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('title', 'assigned_to__email')

    #  DELETE (FIXED HERE)
    def delete_model(self, request, obj):
        obj._current_user = request.user
        super().delete_model(request, obj)


admin.site.register(Task, TaskAdmin)


#  Audit Log Admin
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'action_type',
        'model_name',
        'object_id',
        'field_name',
        'old_value',
        'new_value',
        'timestamp'
    )

    list_filter = (
        'action_type',
        'model_name',
        'timestamp'
    )

    search_fields = (
        'user__email',
        'action',
        'model_name'
    )

    ordering = ('-timestamp',)

    #  DISABLE DELETE
    def has_delete_permission(self, request, obj=None):
        return False

    #  DISABLE EDIT
    def has_change_permission(self, request, obj=None):
        return False

    #  DISABLE ADD (optional but recommended)
    def has_add_permission(self, request):
        return False
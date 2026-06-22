import json
import os
from datetime import datetime
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from .models import AuditLog
from django.db.models.signals import post_delete
from django.utils import timezone

from .middleware import get_current_user
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB


TRACK_MODELS = ['Task', 'User']

MODEL_FIELDS = {
    "Task": ['title', 'description', 'status'],
    "User": ['email', 'username', 'is_verified', 'role']
}

#  Fields to always skip
EXCLUDED_FIELDS = [
    'id', 'password', 'token', 'created_at', 'updated_at',
    'last_login', 'date_joined', 'is_staff', 'is_superuser',
    'is_active',  'user_permissions', 'groups',
]

EXCLUDED_APPS = ['admin', 'sessions', 'contenttypes', 'auth']
EXCLUDED_MODELS = ['OTP', 'Session', 'LogEntry']

#  JSON logs folder path
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')


#  JSON writer function
def write_to_json(log_entry):
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)

        today = datetime.now().strftime('%Y-%m-%d')

        #  base filename
        base_filename = f"audit_{today}"

        #  find latest file index
        file_index = 1
        while True:
            json_file_path = os.path.join(LOGS_DIR, f"{base_filename}_{file_index}.json")

            # if file doesn't exist → use it
            if not os.path.exists(json_file_path):
                break

            # if file exists but size < limit → use it
            if os.path.getsize(json_file_path) < MAX_FILE_SIZE:
                break

            # else go next file
            file_index += 1

        #  read existing data
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
        else:
            data = []

        #  append data
        if isinstance(log_entry, list):
            data.extend(log_entry)
        else:
            data.append(log_entry)

        #  write file
        with open(json_file_path, 'w') as f:
            json.dump(data, f, indent=4, default=str)

    except Exception as e:
        print(f"[AuditLog] JSON write error: {e}")

def get_readable_value(value):
    if hasattr(value, 'email'):
        return value.email
    if hasattr(value, 'username'):
        return value.username
    return str(value) if value is not None else None


@receiver(pre_save)
def capture_old_data(sender, instance, **kwargs):
    if sender._meta.app_label in EXCLUDED_APPS:
        return
    if sender.__name__ in EXCLUDED_MODELS:
        return
    if sender == AuditLog:
        return

    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_data = model_to_dict(old_instance)
        except sender.DoesNotExist:
            instance._old_data = {}
    else:
        instance._old_data = {}


@receiver(post_delete)
def create_delete_log(sender, instance, **kwargs):

    if sender.__name__ not in ['Task', 'User']:
        return

    from .middleware import get_current_user

    user = getattr(instance, '_current_user', None)

    if not user:
        user = get_current_user()

    user_email = user.email if user else None

    deleted_info = None

    if hasattr(instance, 'email'):
        deleted_info = instance.email
    elif hasattr(instance, 'title'):
        deleted_info = instance.title

    #  DB LOG
    AuditLog.objects.create(
        user=user,
        user_email=user_email,
        action=f"{sender.__name__} deleted",
        action_type="DELETE",
        model_name=sender.__name__,
        object_id=str(instance.pk),
        field_name="deleted_object",
        old_value=deleted_info,
        new_value=None,
    )

    #  JSON LOG 
    json_data = [{
        "timestamp": timezone.localtime().strftime("%d-%m-%Y %I:%M %p"),
        "user": user_email,
        "action_type": "DELETE",
        "model_name": sender.__name__,
        "object_id": str(instance.pk),
        "field_name": "deleted_object",
        "old_value": deleted_info,
        "new_value": None,
    }]

    write_to_json(json_data)

@receiver(post_save)
def create_audit_log(sender, instance, created, **kwargs):
    if sender._meta.app_label in EXCLUDED_APPS:
        return
    if sender.__name__ not in TRACK_MODELS:
       return
    if sender.__name__ in EXCLUDED_MODELS:
        return
    if sender == AuditLog:
        return

    old_data = getattr(instance, '_old_data', {})
    new_data = model_to_dict(instance)

    user = getattr(instance, '_current_user', None)
    if not user:
        if hasattr(instance, 'created_by'):
            user = instance.created_by
        elif hasattr(instance, 'user'):
            user = instance.user

    user_email = user.email if user else None
    action_type = "CREATE" if created else "UPDATE"

    logs = []
    json_logs = []  #  separate list for JSON

    allowed_fields = MODEL_FIELDS.get(sender.__name__, [])

    for field in allowed_fields:

        if field in EXCLUDED_FIELDS:
            continue

        old_value = old_data.get(field)
        new_value = new_data.get(field)

        if not created and old_value == new_value:
            continue

        if created and not new_value:
            continue

        # Handle FK fields
        try:
            field_object = sender._meta.get_field(field)
            if field_object.is_relation:
                if new_value:
                    try:
                        new_value = field_object.related_model.objects.get(pk=new_value)
                    except:
                        pass
                if old_value:
                    try:
                        old_value = field_object.related_model.objects.get(pk=old_value)
                    except:
                        pass
        except Exception:
            pass

        old_val = get_readable_value(old_value) if not created else None
        new_val = get_readable_value(new_value)

        #  DB log entry
        logs.append(AuditLog(
            user=user,
            user_email=user_email,
            action=f"{sender.__name__} {action_type.lower()}",
            action_type=action_type,
            model_name=sender.__name__,
            object_id=str(instance.pk),
            field_name=field,
            old_value=old_val,
            new_value=new_val,
        ))

        #  JSON log entry
        json_logs.append({
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "user": user_email,
            "action_type": action_type,
            "model_name": sender.__name__,
            "object_id": str(instance.pk),
            "field_name": field,
            "old_value": old_val,
            "new_value": new_val,
        })

    #  Save to SQLite
    if logs:
        AuditLog.objects.bulk_create(logs)

    #  Save to JSON file
    for entry in json_logs:
        write_to_json(entry)

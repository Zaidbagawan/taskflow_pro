from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from .models import timedelta,OTP,Task
from .utils import generate_otp
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


#  SEND OTP SERVICE
def send_otp_service(email):
    user, _ = User.objects.get_or_create(
        email=email,
        defaults={"username": email}
    )

    otp_code = generate_otp()
    OTP.objects.create(user=user, otp=otp_code)

    send_mail(
        subject='TaskFlow Pro - OTP Verification',
        message=f'Your OTP is {otp_code}. It is valid for 5 minutes.',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
    )


#  VERIFY OTP SERVICE

def verify_otp_service(email, otp):
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return {"error": "User not found"}

    #  STEP 1: Check if user is blocked
    if user.blocked_until and timezone.now() < user.blocked_until:
        return {"error": "Too many failed attempts. Try again after 1 hour."}

    #  STEP 2: Get OTP
    otp_obj = OTP.objects.filter(user=user, otp=otp).last()

    #  STEP 3: Invalid OTP
    if not otp_obj:
        user.failed_attempts += 1

        if user.failed_attempts >= 5:
            user.blocked_until = timezone.now() + timedelta(hours=1)
            user.failed_attempts = 0

        user.save()

        return {"error": "Invalid OTP"}

    #  STEP 4: Expired OTP
    if otp_obj.is_expired():
        user.failed_attempts += 1

        if user.failed_attempts >= 5:
            user.blocked_until = timezone.now() + timedelta(hours=1)
            user.failed_attempts = 0

        user.save()

        otp_obj.delete()
        return {"error": "OTP expired"}

    # STEP 5: Success
    user.is_verified = True
    user.failed_attempts = 0
    user.blocked_until = None
    user.save()

    OTP.objects.filter(user=user).delete()

    refresh = RefreshToken.for_user(user)

    return {
        "message": "Login successful",
        "access": str(refresh.access_token),
        "refresh": str(refresh)
    }


#  CREATE TASK SERVICE
def create_task_service(validated_data, user):
    task = Task(**validated_data, created_by=user)

    #  IMPORTANT (attach user for signals)
    task._current_user = user

    task.save()

    try:
        send_mail(
            subject='New Task Assigned - TaskFlow Pro',
            message=f"""
Hello,

You have been assigned a new task.

Title: {task.title}
Description: {task.description}
Status: {task.status}
""",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[task.assigned_to.email],
        )
    except Exception as e:
        print("Email failed:", e)

    return task

#  UPDATE TASK SERVICE
def update_task_service(task, data, user):
    old_status = task.status

    assigned_to_id = data.pop("assigned_to", None)

    for key, value in data.items():
        setattr(task, key, value)

    if assigned_to_id:
        task.assigned_to = User.objects.get(id=assigned_to_id)

    #  IMPORTANT (MISSING IN YOUR CODE)
    task._current_user = user

    task.save()

    # email logic 
    if old_status != task.status:
        try:
            send_mail(
                subject='Task Status Updated - TaskFlow Pro',
                message=f"""Hello,

You have given task Below the status is there Please check,
               
Title: {task.title}

Old Status: {old_status}

New Status: {task.status}

Updated by: {user.username}
""",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[task.created_by.email],
            )
        except Exception as e:
            print("Email failed:", e)

    return task
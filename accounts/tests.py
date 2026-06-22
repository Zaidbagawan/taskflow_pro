from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import OTP

User = get_user_model()


class TestTaskFlow(TestCase):

    def setUp(self):
        self.client = APIClient()

    # ✅ TEST OTP SEND
    def test_send_otp(self):
        response = self.client.post('/api/send-otp/', {
            "email": "test@gmail.com"
        }, format='json')

        self.assertEqual(response.status_code, 200)

    # ✅ TEST OTP VERIFY
    def test_verify_otp(self):
        self.client.post('/api/send-otp/', {
            "email": "test@gmail.com"
        }, format='json')

        otp_obj = OTP.objects.last()
        self.assertIsNotNone(otp_obj)

        response = self.client.post('/api/verify-otp/', {
            "email": "test@gmail.com",
            "otp": otp_obj.otp
        }, format='json')

        self.assertEqual(response.status_code, 200)

    # ✅ TEST TASK CREATE
    def test_create_task(self):
        admin = User.objects.create_user(
            email="admin@gmail.com",
            username="admin",
            password="1234",
            role="admin"
        )

        user = User.objects.create_user(
            email="user@gmail.com",
            username="user",
            password="1234",
            role="user"
        )

        self.client.force_authenticate(user=admin)

        response = self.client.post('/api/tasks/create/', {
            "title": "Test Task",
            "description": "Testing task",
            "assigned_to": user.id
        }, format='json')

        self.assertEqual(response.status_code, 201)
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class AuthViewsTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='alex', email='alex@example.com', password='password123')

    def test_index_view(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base_login.html')

    def test_register_get(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

    def test_register_post_success(self):
        response = self.client.post(reverse('register'), {
            'alias': 'nuevo',
            'email': 'nuevo@example.com',
            'password': 'segura123',
            'password2': 'segura123',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='nuevo').exists())
        self.assertContains(response, "Cuenta creada con ")

    def test_register_post_password_mismatch(self):
        response = self.client.post(reverse('register'), {
            'alias': 'nuevo',
            'email': 'nuevo@example.com',
            'password': '1234',
            'password2': '4321',
        })
        self.assertContains(response, "Las contraseñas no coinciden")

    def test_register_post_email_taken(self):
        response = self.client.post(reverse('register'), {
            'alias': 'otro',
            'email': 'alex@example.com',
            'password': 'pass',
            'password2': 'pass',
        })
        self.assertContains(response, "Ese correo ya está en uso")

    def test_register_post_alias_taken(self):
        response = self.client.post(reverse('register'), {
            'alias': 'alex',
            'email': 'otro@example.com',
            'password': 'pass',
            'password2': 'pass',
        })
        self.assertContains(response, "Ese Alias ya está en uso")

    def test_login_success(self):
        response = self.client.post(reverse('login'), {
            'username': 'alex@example.com',
            'password': 'password123'
        })
        self.assertRedirects(response, reverse('user_profile'))

    def test_login_failure(self):
        response = self.client.post(reverse('login'), {
            'username': 'asd@asd.com',
            'password': 'asd'
        })
        self.assertEqual(response.status_code, 401)  

    def test_logout(self):
        self.client.login(username='alex', password='password123')
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('explore'))


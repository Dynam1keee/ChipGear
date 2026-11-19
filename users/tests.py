from django.test import TestCase
from django.urls import reverse

from users.models import User


class LoginRedirectTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='alice', password='pass12345')

    def login(self, next_url=None):
        data = {'username': 'alice', 'password': 'pass12345'}
        if next_url is not None:
            data['next'] = next_url
        return self.client.post(reverse('user:login'), data)

    def test_login_redirects_to_local_next_page(self):
        response = self.login(reverse('user:profile'))

        self.assertRedirects(
            response, reverse('user:profile'), fetch_redirect_response=False
        )

    def test_login_ignores_external_next_page(self):
        for external in ['https://evil.example/', '//evil.example/', 'http://evil.example']:
            with self.subTest(next=external):
                response = self.login(external)

                self.assertRedirects(
                    response, reverse('main:index'), fetch_redirect_response=False
                )
                self.client.logout()

    def test_login_without_next_goes_to_home_page(self):
        response = self.login()

        self.assertRedirects(
            response, reverse('main:index'), fetch_redirect_response=False
        )

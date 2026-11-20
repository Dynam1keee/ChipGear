from django.test import TestCase


class ErrorPageTests(TestCase):
    def test_unknown_page_returns_404_status(self):
        response = self.client.get('/no-such-page/')

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'Page not found', status_code=404)

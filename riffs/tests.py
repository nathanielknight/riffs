from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class LoginRedirectTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("user", password="pw")

    def login(self, next_url=None):
        url = reverse("login")
        data = {"username": "user", "password": "pw"}
        if next_url is not None:
            data["next"] = next_url
        return self.client.post(url, data)

    def test_protected_view_redirects_to_login_with_next(self):
        target = reverse("timetrack:index")
        response = self.client.get(target)
        self.assertRedirects(response, f"{reverse('login')}?next={target}")

    def test_login_page_carries_next_through_the_form(self):
        target = reverse("timetrack:index")
        response = self.client.get(reverse("login"), {"next": target})
        self.assertContains(
            response, f'<input type="hidden" name="next" value="{target}">', html=True
        )

    def test_login_returns_to_next(self):
        target = reverse("timetrack:index")
        response = self.login(target)
        self.assertRedirects(response, target, fetch_redirect_response=False)

    def test_login_without_next_goes_home(self):
        self.assertRedirects(self.login(), "/")

    def test_login_ignores_offsite_next(self):
        for evil in (
            "https://evil.example/",
            "//evil.example/",
            "/\\evil.example/",
            "javascript:alert(1)",
        ):
            with self.subTest(next=evil):
                self.client.logout()
                self.assertRedirects(self.login(evil), "/")

    def test_next_is_escaped_in_login_page(self):
        response = self.client.get(reverse("login"), {"next": '"><script>x</script>'})
        self.assertNotContains(response, "<script>x</script>")

    def test_bad_password_does_not_log_in(self):
        response = self.client.post(
            reverse("login"), {"username": "user", "password": "nope"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_requires_post(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)
        self.assertRedirects(self.client.post(reverse("logout")), "/")
        self.assertNotIn("_auth_user_id", self.client.session)

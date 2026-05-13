from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import VizqouteClient, VizqoutePreview, VizqouteQuotation, VizqouteRoofingSpec, VizqouteUser


class AuthAndIsolationTests(TestCase):
    def setUp(self):
        self.web = Client()

        self.user1 = User.objects.create_user(username="c1", password="pw1")
        self.profile1 = self.user1.vizqoute_profile
        self.profile1.name = "C1"
        self.profile1.phone = "-"
        self.profile1.role = "contractor"
        self.profile1.save()

        self.user2 = User.objects.create_user(username="c2", password="pw2")
        self.profile2 = self.user2.vizqoute_profile
        self.profile2.name = "C2"
        self.profile2.phone = "-"
        self.profile2.role = "contractor"
        self.profile2.save()

        self.client1 = VizqouteClient.objects.create(contractor=self.profile1, name="Client A", phone="-")
        self.client2 = VizqouteClient.objects.create(contractor=self.profile2, name="Client B", phone="-")

        self.quote1 = VizqouteQuotation.objects.create(contractorid=self.profile1, clientid=self.client1, status="draft")
        self.quote2 = VizqouteQuotation.objects.create(contractorid=self.profile2, clientid=self.client2, status="draft")

    def test_dashboard_requires_login(self):
        res = self.web.get(reverse("dashboard"))
        self.assertEqual(res.status_code, 302)

    def test_api_isolated_by_contractor(self):
        self.web.login(username="c1", password="pw1")
        res = self.web.get("/api/quotations/")
        self.assertEqual(res.status_code, 200)
        # should include only contractor1 quotes
        body = res.json()
        ids = {q["id"] for q in body}
        self.assertIn(self.quote1.id, ids)
        self.assertNotIn(self.quote2.id, ids)


class PublicApprovalFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="c1", password="pw1")
        self.profile = self.user.vizqoute_profile
        self.profile.name = "C1"
        self.profile.phone = "-"
        self.profile.role = "contractor"
        self.profile.save()
        self.client = VizqouteClient.objects.create(contractor=self.profile, name="Client A", phone="-")
        self.quote = VizqouteQuotation.objects.create(contractorid=self.profile, clientid=self.client, status="sent")
        self.preview = VizqoutePreview.objects.create(
            quotationid=self.quote,
            sharelink="tok123",
            expirydate=timezone.now() + timedelta(days=7),
        )
        self.web = Client()

    def test_public_preview_renders(self):
        res = self.web.get(reverse("quote_preview_public", kwargs={"token": "tok123"}))
        self.assertEqual(res.status_code, 200)

    def test_public_approval_changes_status(self):
        res = self.web.post(reverse("quote_decision_public", kwargs={"token": "tok123"}), data={"decision": "approved"})
        self.assertEqual(res.status_code, 200)
        self.quote.refresh_from_db()
        self.assertEqual(self.quote.status, "approved")


class MaterialsCalcTests(TestCase):
    def setUp(self):
        self.web = Client()
        self.user = User.objects.create_user(username="c1", password="pw1")
        self.profile = self.user.vizqoute_profile
        self.profile.name = "C1"
        self.profile.phone = "-"
        self.profile.role = "contractor"
        self.profile.save()
        self.client = VizqouteClient.objects.create(contractor=self.profile, name="Client A", phone="-")
        self.quote = VizqouteQuotation.objects.create(contractorid=self.profile, clientid=self.client, status="draft")
        VizqouteRoofingSpec.objects.create(
            quotationid=self.quote,
            roofarea=1000,
            pitchangle=6,
            materialtype="Architectural Shingles",
            laborhours=10,
            wastefactor=10,
        )

    def test_materials_calc_requires_login(self):
        res = self.web.get(reverse("materials_calc", kwargs={"quote_id": self.quote.id}))
        self.assertEqual(res.status_code, 302)

    def test_materials_calc_returns_data(self):
        self.web.login(username="c1", password="pw1")
        res = self.web.get(reverse("materials_calc", kwargs={"quote_id": self.quote.id}))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("shingle_bundles", data)

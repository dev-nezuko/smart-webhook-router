import uuid
from types import SimpleNamespace
from django.test import TestCase
from rest_framework.test import APIClient

class OperatorPermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.reads = ["/api/entities/state/?entity_type=SHIPMENT&entity_id=synthetic", "/api/normalization/low-confidence/"]
        self.replay = f"/api/webhooks/{uuid.uuid4()}/replay/"
    def test_anonymous_cannot_read_operational_data_or_replay(self):
        for url in self.reads:
            self.assertIn(self.client.get(url).status_code, [401,403])
        self.assertIn(self.client.post(self.replay, {}, format="json").status_code, [401,403])
    def test_nonstaff_account_cannot_read_operational_data_or_replay(self):
        self.client.force_authenticate(SimpleNamespace(is_authenticated=True,is_staff=False))
        for url in self.reads:
            self.assertEqual(self.client.get(url).status_code,403)
        self.assertEqual(self.client.post(self.replay, {}, format="json").status_code,403)
    def test_staff_can_read_empty_review_queue(self):
        self.client.force_authenticate(SimpleNamespace(is_authenticated=True,is_staff=True))
        response=self.client.get("/api/normalization/low-confidence/")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json(),{"count":0,"results":[]})
    def test_staff_receives_404_for_unknown_entity_or_webhook(self):
        self.client.force_authenticate(SimpleNamespace(is_authenticated=True,is_staff=True))
        self.assertEqual(self.client.get(self.reads[0]).status_code,404)
        self.assertEqual(self.client.post(self.replay, {}, format="json").status_code,404)
    def test_bad_review_threshold_is_a_client_error(self):
        self.client.force_authenticate(SimpleNamespace(is_authenticated=True,is_staff=True))
        for value in ["not-a-number","NaN","Infinity","-0.1","1.1"]:
            self.assertEqual(self.client.get("/api/normalization/low-confidence/", {"threshold":value}).status_code,400)

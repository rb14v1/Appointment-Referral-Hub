from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from common.test_utils import make_clinic, make_patient, make_provider
from waitlist.models import Waitlist, WaitlistOffer
from waitlist.tasks import expire_offer, find_and_offer_match, respond_to_offer


class WaitlistMatchingTests(TestCase):
    def setUp(self):
        self.clinic = make_clinic("Main Clinic")
        self.provider = make_provider("doc@example.com", self.clinic)
        self.patient1 = make_patient("pat1@example.com", primary_clinic=self.clinic)
        self.patient2 = make_patient("pat2@example.com", primary_clinic=self.clinic)

        now = timezone.now()
        self.slot_start = now + timedelta(days=3)
        self.slot_end = self.slot_start + timedelta(minutes=30)

    def _entry(self, patient, priority=0, provider=None, days_start=1, days_end=10):
        now = timezone.now()
        return Waitlist.objects.create(
            patient=patient,
            clinic=self.clinic,
            provider=provider,
            desired_date_range_start=(now + timedelta(days=days_start)).date(),
            desired_date_range_end=(now + timedelta(days=days_end)).date(),
            priority=priority,
        )

    def test_matches_highest_priority_first(self):
        low = self._entry(self.patient1, priority=0)
        high = self._entry(self.patient2, priority=10)

        offer = find_and_offer_match(
            clinic_id=self.clinic.id, provider_id=self.provider.id,
            start_time=self.slot_start, end_time=self.slot_end,
        )
        self.assertIsNotNone(offer)
        self.assertEqual(offer.waitlist_entry_id, high.id)

        high.refresh_from_db()
        low.refresh_from_db()
        self.assertEqual(high.status, Waitlist.Status.OFFERED)
        self.assertEqual(low.status, Waitlist.Status.WAITING)

    def test_ties_broken_fifo(self):
        first = self._entry(self.patient1, priority=5)
        self._entry(self.patient2, priority=5)

        offer = find_and_offer_match(
            clinic_id=self.clinic.id, provider_id=self.provider.id,
            start_time=self.slot_start, end_time=self.slot_end,
        )
        self.assertEqual(offer.waitlist_entry_id, first.id)

    def test_no_match_outside_date_range(self):
        self._entry(self.patient1, days_start=100, days_end=110)
        offer = find_and_offer_match(
            clinic_id=self.clinic.id, provider_id=self.provider.id,
            start_time=self.slot_start, end_time=self.slot_end,
        )
        self.assertIsNone(offer)

    def test_decline_advances_to_next_candidate(self):
        self._entry(self.patient1, priority=10)
        second = self._entry(self.patient2, priority=0)

        offer = find_and_offer_match(
            clinic_id=self.clinic.id, provider_id=self.provider.id,
            start_time=self.slot_start, end_time=self.slot_end,
        )
        respond_to_offer(offer, accept=False)

        offers = WaitlistOffer.objects.filter(waitlist_entry=second)
        self.assertEqual(offers.count(), 1)
        self.assertEqual(offers.first().response, WaitlistOffer.Response.PENDING)

    def test_expired_offer_advances_to_next_candidate(self):
        self._entry(self.patient1, priority=10)
        second = self._entry(self.patient2, priority=0)

        offer = find_and_offer_match(
            clinic_id=self.clinic.id, provider_id=self.provider.id,
            start_time=self.slot_start, end_time=self.slot_end,
        )
        offer.expires_at = timezone.now() - timedelta(minutes=1)
        offer.save(update_fields=["expires_at"])

        expire_offer(offer)

        self.assertTrue(WaitlistOffer.objects.filter(waitlist_entry=second, response=WaitlistOffer.Response.PENDING).exists())

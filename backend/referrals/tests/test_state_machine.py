from django.test import TestCase

from common.test_utils import make_clinic, make_patient, make_provider
from referrals.models import Referral
from referrals.services import state_machine


class ReferralStateMachineTests(TestCase):
    def setUp(self):
        self.clinic_a = make_clinic("Clinic A")
        self.clinic_b = make_clinic("Clinic B")
        self.provider_a = make_provider("doc.a@example.com", self.clinic_a)
        self.patient = make_patient("pat@example.com", primary_clinic=self.clinic_a)
        self.referral = Referral.objects.create(
            patient=self.patient,
            referring_clinic=self.clinic_a,
            referring_provider=self.provider_a,
            receiving_clinic=self.clinic_b,
            reason="Needs specialist",
        )

    def test_pending_to_accepted_is_legal(self):
        state_machine.accept(self.referral, actor=self.provider_a.user)
        self.referral.refresh_from_db()
        self.assertEqual(self.referral.status, Referral.Status.ACCEPTED)

    def test_pending_to_scheduled_is_illegal(self):
        with self.assertRaises(state_machine.IllegalTransitionError):
            state_machine.transition(self.referral, Referral.Status.SCHEDULED, actor=self.provider_a.user)

    def test_accepted_to_scheduled_is_legal(self):
        state_machine.accept(self.referral, actor=self.provider_a.user)
        state_machine.mark_scheduled(self.referral, actor=self.provider_a.user)
        self.referral.refresh_from_db()
        self.assertEqual(self.referral.status, Referral.Status.SCHEDULED)

    def test_terminal_states_reject_all_transitions(self):
        state_machine.reject(self.referral, actor=self.provider_a.user)
        self.referral.refresh_from_db()
        self.assertEqual(self.referral.status, Referral.Status.REJECTED)
        with self.assertRaises(state_machine.IllegalTransitionError):
            state_machine.transition(self.referral, Referral.Status.ACCEPTED, actor=self.provider_a.user)

    def test_scheduled_to_completed_sets_resolved_at(self):
        state_machine.accept(self.referral, actor=self.provider_a.user)
        state_machine.mark_scheduled(self.referral, actor=self.provider_a.user)
        state_machine.transition(self.referral, Referral.Status.COMPLETED, actor=self.provider_a.user)
        self.referral.refresh_from_db()
        self.assertIsNotNone(self.referral.resolved_at)

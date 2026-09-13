from django.contrib.auth import get_user_model
from django.test import TestCase

from complaints.models import (
    Complaint,
    ComplaintAnalysis,
    ComplaintAssignment,
)
from complaints.services.assignment_service import (
    ComplaintAssignmentError,
    assign_complaint,
)
from complaints.services.officer_assignment_service import (
    OfficerAssignmentError,
    get_officer_workload,
    select_officer_for_department,
)
from complaints.services.routing_service import (
    RoutingError,
    route_complaint,
)
from organizations.models import Category, Department


User = get_user_model()


class ComplaintRoutingServiceTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(
            name="Public Works",
        )

        self.other_department = Department.objects.create(
            name="Water Supply",
        )

        self.category = Category.objects.create(
            name="Road Repair",
            department=self.department,
        )

        self.user = User.objects.create_user(
            email="citizen@test.com",
            password="testpassword",
            role=User.Role.USER,
        )

        self.complaint = Complaint.objects.create(
            user=self.user,
            category=self.category,
            title="Damaged road",
            description="There is a large pothole on the main road.",
            status=Complaint.Status.AI_ANALYZING,
            priority=Complaint.Priority.MEDIUM,
        )

    def create_analysis(
        self,
        *,
        predicted_category=None,
        predicted_department=None,
    ):
        return ComplaintAnalysis.objects.create(
            complaint=self.complaint,
            summary="Road damage complaint.",
            predicted_category=(
                predicted_category
                if predicted_category is not None
                else self.category
            ),
            predicted_department=(
                predicted_department
                if predicted_department is not None
                else self.department
            ),
            predicted_priority=Complaint.Priority.MEDIUM,
            urgency_score=60,
            confidence_score=95,
            model_name="Day25-Test-AI",
            explanation="The complaint concerns road infrastructure.",
        )

    def test_route_uses_category_department_relationship(self):
        analysis = self.create_analysis()

        result = route_complaint(self.complaint)

        self.assertEqual(
            result["category"],
            analysis.predicted_category,
        )

        self.assertEqual(
            result["department"],
            self.department,
        )

    def test_route_rejects_ai_department_category_mismatch(self):
        self.create_analysis(
            predicted_category=self.category,
            predicted_department=self.other_department,
        )

        with self.assertRaises(RoutingError):
            route_complaint(self.complaint)

    def test_route_rejects_inactive_category(self):
        self.category.is_active = False
        self.category.save(update_fields=["is_active"])

        self.create_analysis()

        with self.assertRaises(RoutingError):
            route_complaint(self.complaint)

    def test_route_rejects_inactive_department(self):
        self.department.is_active = False
        self.department.save(update_fields=["is_active"])

        self.create_analysis()

        with self.assertRaises(RoutingError):
            route_complaint(self.complaint)

    def test_route_rejects_missing_ai_analysis(self):
        with self.assertRaises(RoutingError):
            route_complaint(self.complaint)

    def test_route_rejects_missing_predicted_category(self):
        ComplaintAnalysis.objects.create(
            complaint=self.complaint,
            summary="Road damage complaint.",
            predicted_category=None,
            predicted_department=None,
            predicted_priority=Complaint.Priority.MEDIUM,
            urgency_score=60,
            confidence_score=95,
            model_name="Day25-Test-AI",
            explanation="The complaint concerns road infrastructure.",
        )

        with self.assertRaises(RoutingError):
            route_complaint(self.complaint)


class OfficerSelectionServiceTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(
            name="Public Works",
        )

        self.other_department = Department.objects.create(
            name="Water Supply",
        )

        self.officer1 = User.objects.create_user(
            email="officer1@test.com",
            password="testpassword",
            role=User.Role.OFFICER,
            department=self.department,
        )

        self.officer2 = User.objects.create_user(
            email="officer2@test.com",
            password="testpassword",
            role=User.Role.OFFICER,
            department=self.department,
        )

        self.other_department_officer = User.objects.create_user(
            email="water-officer@test.com",
            password="testpassword",
            role=User.Role.OFFICER,
            department=self.other_department,
        )

        self.citizen = User.objects.create_user(
            email="citizen@test.com",
            password="testpassword",
            role=User.Role.USER,
        )

        self.system_user = User.objects.create_user(
            email="system@civicresolve.local",
            password="testpassword",
            role=User.Role.ADMIN,
        )

    def create_complaint(self, title):
        return Complaint.objects.create(
            user=self.citizen,
            category=Category.objects.create(
                name=f"Category {title}",
                department=self.department,
            ),
            title=title,
            description="A complaint created for officer workload testing.",
            status=Complaint.Status.ASSIGNED,
            priority=Complaint.Priority.MEDIUM,
        )

    def create_active_assignment(self, officer, title):
        complaint = self.create_complaint(title)

        return ComplaintAssignment.objects.create(
            complaint=complaint,
            department=self.department,
            officer=officer,
            assigned_by=self.system_user,
            reason="Day 25 workload test.",
        )

    def test_selects_least_loaded_officer(self):
        self.create_active_assignment(
            self.officer1,
            "Officer one workload",
        )

        selected_officer = select_officer_for_department(
            self.department
        )

        self.assertEqual(
            selected_officer,
            self.officer2,
        )

    def test_workload_counts_only_active_assignments(self):
        active_assignment = self.create_active_assignment(
            self.officer1,
            "Active assignment",
        )

        self.create_active_assignment(
            self.officer1,
            "Second active assignment",
        )

        inactive_complaint = self.create_complaint(
            "Completed assignment"
        )

        inactive_assignment = ComplaintAssignment.objects.create(
            complaint=inactive_complaint,
            department=self.department,
            officer=self.officer1,
            assigned_by=self.system_user,
            reason="Completed workload test.",
        )

        inactive_assignment.unassigned_at = inactive_assignment.assigned_at
        inactive_assignment.save(
            update_fields=["unassigned_at"]
        )

        self.assertEqual(
            get_officer_workload(self.officer1),
            2,
        )

        self.assertIsNotNone(active_assignment)
        self.assertIsNotNone(inactive_assignment)

    def test_tie_is_broken_deterministically_by_user_id(self):
        selected_officer = select_officer_for_department(
            self.department
        )

        expected_officer = min(
            self.officer1,
            self.officer2,
            key=lambda officer: officer.id,
        )

        self.assertEqual(
            selected_officer,
            expected_officer,
        )

    def test_inactive_officer_is_not_selected(self):
        self.officer1.is_active = False
        self.officer1.save(update_fields=["is_active"])

        selected_officer = select_officer_for_department(
            self.department
        )

        self.assertEqual(
            selected_officer,
            self.officer2,
        )

    def test_officer_from_another_department_is_not_selected(self):
        selected_officer = select_officer_for_department(
            self.department
        )

        self.assertIn(
            selected_officer,
            [self.officer1, self.officer2],
        )

        self.assertNotEqual(
            selected_officer,
            self.other_department_officer,
        )

    def test_no_active_officer_raises_error(self):
        self.officer1.is_active = False
        self.officer1.save(update_fields=["is_active"])

        self.officer2.is_active = False
        self.officer2.save(update_fields=["is_active"])

        with self.assertRaises(OfficerAssignmentError):
            select_officer_for_department(
                self.department
            )


class ComplaintRoutingAssignmentIntegrationTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(
            name="Public Works",
        )

        self.other_department = Department.objects.create(
            name="Water Supply",
        )

        self.category = Category.objects.create(
            name="Road Repair",
            department=self.department,
        )

        self.user = User.objects.create_user(
            email="citizen@test.com",
            password="testpassword",
            role=User.Role.USER,
        )

        self.officer = User.objects.create_user(
            email="officer@test.com",
            password="testpassword",
            role=User.Role.OFFICER,
            department=self.department,
        )

        self.system_user = User.objects.create_user(
            email="system@civicresolve.local",
            password="testpassword",
            role=User.Role.ADMIN,
        )

        self.complaint = Complaint.objects.create(
            user=self.user,
            category=self.category,
            title="Road repair required",
            description="The road near the entrance is badly damaged.",
            status=Complaint.Status.AI_ANALYZING,
            priority=Complaint.Priority.HIGH,
        )

        ComplaintAnalysis.objects.create(
            complaint=self.complaint,
            summary="Road damage requires public works attention.",
            predicted_category=self.category,
            predicted_department=self.department,
            predicted_priority=Complaint.Priority.HIGH,
            urgency_score=80,
            confidence_score=96,
            model_name="Day25-Test-AI",
            explanation="The complaint describes damaged public road infrastructure.",
        )

    def test_assignment_uses_ai_category_to_route_to_department(self):
        assignment = assign_complaint(self.complaint)

        self.assertEqual(
            assignment.department,
            self.department,
        )

        self.assertEqual(
            assignment.officer,
            self.officer,
        )

        self.complaint.refresh_from_db()

        self.assertEqual(
            self.complaint.status,
            Complaint.Status.ASSIGNED,
        )

    def test_assignment_fails_when_no_officer_is_available(self):
        self.officer.is_active = False
        self.officer.save(update_fields=["is_active"])

        with self.assertRaises(ComplaintAssignmentError):
            assign_complaint(self.complaint)

        self.complaint.refresh_from_db()

        self.assertEqual(
            self.complaint.status,
            Complaint.Status.AI_ANALYZING,
        )

    def test_assignment_fails_when_ai_department_does_not_match_category(self):
        analysis = self.complaint.analysis

        analysis.predicted_department = self.other_department
        analysis.save(
            update_fields=["predicted_department"]
        )

        with self.assertRaises(ComplaintAssignmentError):
            assign_complaint(self.complaint)

        self.complaint.refresh_from_db()

        self.assertEqual(
            self.complaint.status,
            Complaint.Status.AI_ANALYZING,
        )
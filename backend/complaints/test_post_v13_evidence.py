from io import BytesIO
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image

from complaints.services.ai_provider import AIProviderError
from complaints.services.evidence_ai_service import (
    EvidenceAIAnalysisError,
    analyze_evidence,
    build_evidence_prompt,
)
from complaints.services.evidence_ai_validator import (
    EvidenceAIValidationError,
    validate_evidence_ai_output,
)
from complaints.services.evidence_service import (
    MAX_EVIDENCE_SIZE,
    validate_evidence_image,
)


class EvidenceImageValidationTests(SimpleTestCase):
    """
    Tests for uploaded complaint evidence image validation.
    """

    def test_valid_png_is_accepted(self):
        uploaded_file = SimpleUploadedFile(
            "test.png",
            self._image_bytes("PNG"),
            content_type="image/png",
        )

        self.assertTrue(
            validate_evidence_image(uploaded_file)
        )

    def test_valid_jpeg_is_accepted(self):
        uploaded_file = SimpleUploadedFile(
            "test.jpg",
            self._image_bytes("JPEG"),
            content_type="image/jpeg",
        )

        self.assertTrue(
            validate_evidence_image(uploaded_file)
        )

    def test_valid_webp_is_accepted(self):
        uploaded_file = SimpleUploadedFile(
            "test.webp",
            self._image_bytes("WEBP"),
            content_type="image/webp",
        )

        self.assertTrue(
            validate_evidence_image(uploaded_file)
        )

    def test_unsupported_content_type_is_rejected(self):
        uploaded_file = SimpleUploadedFile(
            "test.txt",
            b"this is not an image",
            content_type="text/plain",
        )

        with self.assertRaises(ValidationError):
            validate_evidence_image(uploaded_file)

    def test_fake_png_file_is_rejected(self):
        uploaded_file = SimpleUploadedFile(
            "fake.png",
            b"this is not really a PNG image",
            content_type="image/png",
        )

        with self.assertRaises(ValidationError):
            validate_evidence_image(uploaded_file)

    def test_file_larger_than_5_mb_is_rejected(self):
        oversized_file = SimpleUploadedFile(
            "large.png",
            b"x" * (MAX_EVIDENCE_SIZE + 1),
            content_type="image/png",
        )

        with self.assertRaises(ValidationError):
            validate_evidence_image(oversized_file)

    @staticmethod
    def _image_bytes(image_format):
        """
        Generate a real valid 1x1 image using Pillow.
        """
        image = Image.new(
            "RGB",
            (1, 1),
        )

        buffer = BytesIO()

        image.save(
            buffer,
            format=image_format,
        )

        return buffer.getvalue()


class EvidenceAIValidatorTests(SimpleTestCase):
    """
    Tests for validation of Gemini evidence-analysis output.
    """

    def _valid_output(self):
        return {
            "evidence_type": "ROAD_DAMAGE",
            "observations": "A visible pothole is present.",
            "severity_score": 75,
            "confidence_score": 92,
            "complaint_consistency": True,
            "analysis_explanation": (
                "The image visibly supports the reported "
                "road damage."
            ),
        }

    def test_valid_ai_output_is_accepted(self):
        result = validate_evidence_ai_output(
            self._valid_output()
        )

        self.assertEqual(
            result["evidence_type"],
            "ROAD_DAMAGE",
        )

        self.assertEqual(
            result["observations"],
            "A visible pothole is present.",
        )

        self.assertEqual(
            result["severity_score"],
            75,
        )

        self.assertEqual(
            result["confidence_score"],
            92,
        )

        self.assertTrue(
            result["complaint_consistency"]
        )

    def test_missing_required_field_is_rejected(self):
        data = self._valid_output()

        del data["evidence_type"]

        with self.assertRaises(
            EvidenceAIValidationError
        ):
            validate_evidence_ai_output(data)

    def test_invalid_evidence_type_is_rejected(self):
        data = self._valid_output()

        data["evidence_type"] = "FAKE_CATEGORY"

        with self.assertRaises(
            EvidenceAIValidationError
        ):
            validate_evidence_ai_output(data)

    def test_negative_severity_score_is_rejected(self):
        data = self._valid_output()

        data["severity_score"] = -1

        with self.assertRaises(
            EvidenceAIValidationError
        ):
            validate_evidence_ai_output(data)

    def test_severity_score_above_100_is_rejected(self):
        data = self._valid_output()

        data["severity_score"] = 101

        with self.assertRaises(
            EvidenceAIValidationError
        ):
            validate_evidence_ai_output(data)

    def test_confidence_score_above_100_is_rejected(self):
        data = self._valid_output()

        data["confidence_score"] = 101

        with self.assertRaises(
            EvidenceAIValidationError
        ):
            validate_evidence_ai_output(data)

    def test_non_boolean_consistency_is_rejected(self):
        data = self._valid_output()

        data["complaint_consistency"] = "true"

        with self.assertRaises(
            EvidenceAIValidationError
        ):
            validate_evidence_ai_output(data)

    def test_non_string_observations_are_rejected(self):
        data = self._valid_output()

        data["observations"] = 123

        with self.assertRaises(
            EvidenceAIValidationError
        ):
            validate_evidence_ai_output(data)

    def test_non_string_explanation_is_rejected(self):
        data = self._valid_output()

        data["analysis_explanation"] = 123

        with self.assertRaises(
            EvidenceAIValidationError
        ):
            validate_evidence_ai_output(data)


class EvidencePromptTests(SimpleTestCase):
    """
    Tests for construction of the multimodal evidence prompt.
    """

    def test_prompt_contains_complaint_context(self):
        complaint = MagicMock()

        complaint.ticket_number = "CR-TEST-001"
        complaint.title = "Road damage near Block A"
        complaint.description = (
            "There is a large pothole near Block A."
        )

        complaint.category.name = "Road Damage"
        complaint.category.department.name = (
            "Roads and Infrastructure Department"
        )

        evidence = MagicMock()

        prompt = build_evidence_prompt(
            complaint,
            evidence,
        )

        self.assertIn(
            "CR-TEST-001",
            prompt,
        )

        self.assertIn(
            "Road damage near Block A",
            prompt,
        )

        self.assertIn(
            "There is a large pothole near Block A.",
            prompt,
        )

        self.assertIn(
            "Road Damage",
            prompt,
        )

        self.assertIn(
            "Roads and Infrastructure Department",
            prompt,
        )

    def test_prompt_requires_structured_json(self):
        complaint = MagicMock()

        complaint.ticket_number = "CR-TEST-002"
        complaint.title = "Water leakage"
        complaint.description = (
            "Water is leaking near Block B."
        )

        complaint.category.name = "Water Leakage"
        complaint.category.department.name = (
            "Water Supply Department"
        )

        evidence = MagicMock()

        prompt = build_evidence_prompt(
            complaint,
            evidence,
        )

        self.assertIn(
            "Return ONLY valid JSON.",
            prompt,
        )

        self.assertIn(
            "severity_score",
            prompt,
        )

        self.assertIn(
            "confidence_score",
            prompt,
        )

        self.assertIn(
            "complaint_consistency",
            prompt,
        )


class EvidenceAIServiceTests(SimpleTestCase):
    """
    Tests for the evidence AI analysis service.

    Gemini is mocked here so automated tests never call the
    real external AI service.
    """

    def _mock_evidence(self):
        evidence = MagicMock()

        evidence.content_type = "image/png"

        evidence.complaint.ticket_number = (
            "CR-TEST-003"
        )

        evidence.complaint.title = (
            "Road damage near Block A"
        )

        evidence.complaint.description = (
            "There is a large pothole near Block A."
        )

        evidence.complaint.category.name = (
            "Road Damage"
        )

        evidence.complaint.category.department.name = (
            "Roads and Infrastructure Department"
        )

        evidence.image.open = MagicMock()

        evidence.image.read.return_value = (
            b"fake-image-bytes"
        )

        evidence.image.close = MagicMock()

        evidence.save = MagicMock()

        return evidence

    def _valid_ai_json(self):
        return """
        {
          "evidence_type": "ROAD_DAMAGE",
          "observations": "A large pothole is visible.",
          "severity_score": 82,
          "confidence_score": 94,
          "complaint_consistency": true,
          "analysis_explanation": "The visible pothole supports the reported road damage."
        }
        """

    @patch(
        "complaints.services.evidence_ai_service.GeminiProvider"
    )
    def test_successful_ai_analysis_updates_evidence(
        self,
        provider_class,
    ):
        evidence = self._mock_evidence()

        provider = provider_class.return_value

        provider.model_name = (
            "gemini-test-model"
        )

        provider.analyze_image.return_value = (
            self._valid_ai_json()
        )

        result = analyze_evidence(
            evidence
        )

        self.assertIs(
            result,
            evidence,
        )

        self.assertTrue(
            evidence.analysis_completed
        )

        self.assertEqual(
            evidence.evidence_type,
            "ROAD_DAMAGE",
        )

        self.assertEqual(
            evidence.observations,
            "A large pothole is visible.",
        )

        self.assertEqual(
            evidence.severity_score,
            82,
        )

        self.assertEqual(
            evidence.confidence_score,
            94,
        )

        self.assertTrue(
            evidence.complaint_consistency
        )

        self.assertEqual(
            evidence.analysis_model,
            "gemini-test-model",
        )

        provider.analyze_image.assert_called_once()

        evidence.save.assert_called_once()

        update_fields = (
            evidence.save.call_args.kwargs[
                "update_fields"
            ]
        )

        self.assertNotIn(
            "updated_at",
            update_fields,
        )

        self.assertIn(
            "analysis_completed",
            update_fields,
        )

        self.assertIn(
            "evidence_type",
            update_fields,
        )

        self.assertIn(
            "analysis_model",
            update_fields,
        )

    @patch(
        "complaints.services.evidence_ai_service.GeminiProvider"
    )
    def test_invalid_json_raises_analysis_error(
        self,
        provider_class,
    ):
        evidence = self._mock_evidence()

        provider = provider_class.return_value

        provider.model_name = (
            "gemini-test-model"
        )

        provider.analyze_image.return_value = (
            "this is not valid JSON"
        )

        with self.assertRaises(
            EvidenceAIAnalysisError
        ):
            analyze_evidence(evidence)

        evidence.save.assert_not_called()

    @patch(
        "complaints.services.evidence_ai_service.GeminiProvider"
    )
    def test_invalid_ai_output_raises_analysis_error(
        self,
        provider_class,
    ):
        evidence = self._mock_evidence()

        provider = provider_class.return_value

        provider.model_name = (
            "gemini-test-model"
        )

        provider.analyze_image.return_value = """
        {
          "evidence_type": "INVALID",
          "observations": "Something",
          "severity_score": 50,
          "confidence_score": 90,
          "complaint_consistency": true,
          "analysis_explanation": "Test"
        }
        """

        with self.assertRaises(
            EvidenceAIAnalysisError
        ):
            analyze_evidence(evidence)

        evidence.save.assert_not_called()

    @patch(
        "complaints.services.evidence_ai_service.GeminiProvider"
    )
    def test_ai_provider_failure_raises_analysis_error(
        self,
        provider_class,
    ):
        evidence = self._mock_evidence()

        provider = provider_class.return_value

        provider.analyze_image.side_effect = (
            AIProviderError(
                "Gemini unavailable"
            )
        )

        with self.assertRaises(
            EvidenceAIAnalysisError
        ):
            analyze_evidence(evidence)

        evidence.save.assert_not_called()

    def test_image_read_failure_raises_analysis_error(self):
        evidence = self._mock_evidence()

        evidence.image.open.side_effect = (
            OSError("Unable to open image")
        )

        with self.assertRaises(
            EvidenceAIAnalysisError
        ):
            analyze_evidence(evidence)
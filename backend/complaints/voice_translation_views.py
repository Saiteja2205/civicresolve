from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsCitizenUser
from complaints.services.ai_provider import AIProviderError
from complaints.services.voice_translation_service import (
    translate_voice_complaint,
)


class VoiceComplaintTranslationView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsCitizenUser,
    ]

    def post(self, request):
        text = request.data.get(
            "text",
            "",
        )

        try:
            result = translate_voice_complaint(
                text
            )
        except AIProviderError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )
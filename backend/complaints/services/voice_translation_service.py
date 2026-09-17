import json

from complaints.services.ai_provider import (
    AIProviderError,
    GeminiProvider,
)


def parse_voice_translation_response(response_text):
    if not isinstance(response_text, str):
        raise AIProviderError(
            "AI response must be text."
        )

    response_text = response_text.strip()

    if not response_text:
        raise AIProviderError(
            "AI response is empty."
        )

    if response_text.startswith("```"):
        lines = response_text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        response_text = "\n".join(
            lines
        ).strip()

    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise AIProviderError(
            "AI returned invalid JSON."
        ) from exc

    if not isinstance(data, dict):
        raise AIProviderError(
            "AI response must be a JSON object."
        )

    detected_language = data.get(
        "detected_language"
    )

    english_title = data.get(
        "english_title"
    )

    english_description = data.get(
        "english_description"
    )

    if not isinstance(
        detected_language,
        str,
    ):
        raise AIProviderError(
            "AI did not return a valid detected language."
        )

    if not isinstance(
        english_title,
        str,
    ):
        raise AIProviderError(
            "AI did not return a valid English title."
        )

    if not isinstance(
        english_description,
        str,
    ):
        raise AIProviderError(
            "AI did not return a valid English description."
        )

    detected_language = detected_language.strip()
    english_title = english_title.strip()
    english_description = english_description.strip()

    if not detected_language:
        raise AIProviderError(
            "Detected language cannot be empty."
        )

    if not english_title:
        raise AIProviderError(
            "English title cannot be empty."
        )

    if not english_description:
        raise AIProviderError(
            "English description cannot be empty."
        )

    if len(english_title) > 200:
        raise AIProviderError(
            "English title cannot exceed 200 characters."
        )

    if len(english_description) > 5000:
        raise AIProviderError(
            "English description cannot exceed 5000 characters."
        )

    return {
        "detected_language": detected_language,
        "english_title": english_title,
        "english_description": english_description,
    }


def translate_voice_complaint(text):
    if not isinstance(text, str):
        raise AIProviderError(
            "Voice transcript must be text."
        )

    text = text.strip()

    if not text:
        raise AIProviderError(
            "Voice transcript cannot be empty."
        )

    if len(text) < 5:
        raise AIProviderError(
            "Voice transcript is too short."
        )

    if len(text) > 10000:
        raise AIProviderError(
            "Voice transcript cannot exceed 10000 characters."
        )

    prompt = f"""
You are the multilingual voice processing engine for CivicResolve.

The citizen has spoken a complaint using voice.

The speech transcript may be in English, Telugu, Hindi,
Tamil, Kannada, Malayalam, Bengali, Marathi, Urdu, or another
language.

Your job is to understand the transcript and produce a clean
English complaint that can be submitted to CivicResolve.

Detect the primary language of the transcript.

Create:
1. A concise English complaint title.
2. A clear English complaint description.

Preserve the meaning of what the citizen said.

Do not invent facts, locations, people, dates, causes,
severity, or other information that was not stated.

The English title should be short and suitable as a complaint
title.

The English description should preserve all useful details
from the transcript.

If the transcript is already English, clean up obvious speech
recognition errors while preserving its meaning.

If the transcript contains transliterated Indian-language
speech written using English characters, interpret the
intended language and meaning before producing the English
version.

Do not include markdown.

Return ONLY valid JSON.

The JSON must contain exactly these fields:

{{
    "detected_language": "English",
    "english_title": "Short English complaint title",
    "english_description": "Clear English complaint description"
}}

VOICE TRANSCRIPT:
{text}

Return only the JSON object.
"""

    provider = GeminiProvider()

    response_text = provider.analyze_complaint(
        prompt
    )

    return parse_voice_translation_response(
        response_text
    )
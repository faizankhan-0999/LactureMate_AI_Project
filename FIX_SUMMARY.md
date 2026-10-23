# LectureMate AI — Gemini MCQ error fix

## What was confirmed
The previous `src/gemini_service.py` retried most exceptions without distinguishing permanent errors, then replaced the original cause with `Gemini request failed after retries`. That code defect is confirmed by inspection. The screenshot alone does not reveal the original live Gemini API error, so the underlying provider/account/network cause cannot honestly be named without a new server log from the user's deployment.

## Changes
- Classifies authentication, permission, missing-model, quota, rate-limit, invalid-request, server, and network failures.
- Retries only transient failures with bounded exponential backoff; permanent failures stop immediately.
- Uses the official `google-genai` SDK pattern: `genai.Client(api_key=...)` and `client.models.generate_content(model=..., contents=..., config=...)`.
- Uses JSON MIME mode and a larger explicit output-token ceiling for structured study content.
- Logs category, exception type, status, configured model, safe diagnostic text, and traceback frames without intentionally logging prompts or API keys.
- Makes one bounded JSON repair attempt and one bounded MCQ schema-correction attempt.
- Validates requested MCQ count, four distinct options, answer key, required fields, duplicates, and source page numbers against extracted pages.
- Keeps existing MCQs until a replacement set passes validation. A failure leaves the extracted lecture in session state for retry.

## Validation performed in this environment
- `python -m compileall -q app.py src tests`: passed.
- `python -m pytest -v`: 35 passed.
- Dependency installation was attempted but could not complete because DNS/network access was unavailable.
- `google-genai` and Streamlit are not installed in this environment, so app startup and live Gemini calls could not be performed.
- No API key was available for a live integration test. Mocked tests do not prove live API access.

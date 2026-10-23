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

## Follow-up fix: failed first analysis chunk

- Fixed `src/source_analyzer.py` so it no longer hides the underlying Gemini exception behind a generic failed-chunk message. The on-screen error now includes the safe diagnostic category/status/details returned by the Gemini service, helping distinguish invalid API keys, model access, quota, network errors, and invalid requests.
- Reduced the default lecture-analysis chunk size from 18,000 to 9,000 characters and overlap from 800 to 300 characters to lower request-size pressure.
- Added a bounded split-and-retry path for errors that indicate an oversized request/context. It splits a chunk at a nearby paragraph boundary and retries smaller pieces up to two levels; unrelated failures are not retried as if they were size issues.
- Added regression tests for diagnostic visibility and split/retry behavior.
- Validation: `python -m compileall -q app.py src tests` passed; `python -m pytest -q` passed (37 tests).
- Live Gemini API behavior remains unverified in this environment because no live API credentials/network are available. If the next run shows `authentication`, `permission`, `quota`, or `model_unavailable`, fix that specific API/account configuration; code cannot bypass those provider-side restrictions.

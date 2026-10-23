# LectureMate AI

LectureMate AI turns text-based university lecture PDFs into teacher-style study notes, practice questions, MCQs, interactive quizzes, flashcards, revision sheets, and downloadable Markdown/TXT resources.

> AI output can be wrong. Check important explanations, formulas, and source-page references against the original PDF. Lecture text is sent to Google's Gemini API when you ask the app to generate content.

## Features
- PDF upload, page-by-page text extraction, file/page status, low-text detection, and coverage report.
- Three modes: Simple Explanation, Detailed University Notes, and Exam-Focused Revision.
- Exam questions, validated four-option MCQs, quiz scoring and incorrect-answer review.
- Flashcards, last-minute revision sheet, and lecture-scoped AI chat.
- Markdown/TXT downloads; source-page references are shown when provided and validated.
- Gemini API key read from Streamlit Secrets or a local environment variable.
- Automated tests that do not require a live Gemini API key.

## Technology stack
Python, Streamlit, Google's official `google-genai` SDK, pypdf, pytest.

## Screenshots
Screenshots are not included yet. After running the app, capture the dashboard and add images under `screenshots/`, then update this section.

## Project structure
```text
lecturemate-ai/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/config.toml
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── pdf_processor.py
│   ├── lecture_chunker.py
│   ├── source_analyzer.py
│   ├── gemini_service.py
│   ├── notes_generator.py
│   ├── question_generator.py
│   ├── flashcard_generator.py
│   ├── quiz_engine.py
│   └── export_service.py
├── tests/
└── sample_data/README.md
```

## Prerequisites
- Python 3.10 or newer (Python 3.11 or 3.12 recommended for broad package compatibility).
- A Google Gemini API key with access to the configured model. Availability, quotas, and pricing depend on Google's current terms and your account.

## Local installation (Windows)
1. Download and extract this project ZIP.
2. Open the project folder in Command Prompt or PowerShell.
3. Create a virtual environment:
   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   ```
4. Install packages:
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
5. Set the key for the current terminal session (PowerShell):
   ```powershell
   $env:GEMINI_API_KEY="paste-your-key-here"
   ```
   Never paste a real key into source code or GitHub. Alternatively, create `.streamlit/secrets.toml` locally with `GEMINI_API_KEY = "your-key"`; this file is excluded by `.gitignore`.
6. Start the app:
   ```powershell
   streamlit run app.py
   ```
7. Open the local URL printed by Streamlit, normally `http://localhost:8501`.

## Gemini configuration
The default model is `gemini-3.8-flash`. The app reads `GEMINI_MODEL` from Streamlit Secrets first, then the environment. Model access can depend on Google AI Studio project and account settings. For local development, set `GEMINI_API_KEY`. For deployment, use Streamlit Community Cloud Secrets.

Example `.streamlit/secrets.toml` (local only; do not commit it):
```toml
GEMINI_API_KEY = "your-real-key-goes-here"
GEMINI_MODEL = "gemini-3.8-flash"
```

## Run tests
From the project root:
```bash
python -m pytest -v
```
Tests use synthetic data and mocked Gemini responses; they do not verify live API access or model output quality.

## Create a GitHub repository using the website
1. Sign in to GitHub and choose **New repository**.
2. Name it `lecturemate-ai` and select Public or Private.
3. Create the repository. If using the web uploader, upload the project files and folders; for folders, create each folder and upload its files, or use GitHub's supported upload flow for the extracted project.
4. Ensure `app.py`, `requirements.txt`, `README.md`, `.gitignore`, `.streamlit/config.toml`, `src/`, and `tests/` appear at the repository root/expected paths.
5. Check that no API key, `.streamlit/secrets.toml`, `.env`, or private lecture PDF was committed.

## Deploy on Streamlit Community Cloud
1. Sign in to Streamlit Community Cloud and connect GitHub if prompted.
2. Choose **Create app** and select repository `lecturemate-ai`, your branch (usually `main`), and main file path `app.py`.
3. In app settings, open **Secrets** and add:
   ```toml
   GEMINI_API_KEY = "your-real-key-goes-here"
   ```
4. Deploy and monitor build logs. Open the generated app URL.
5. Test with a non-private text-based PDF, generate notes and MCQs, submit a quiz, and test downloads. If deployment fails, inspect the build logs and verify dependency versions and Secrets syntax.

## Troubleshooting
- **API key missing:** add `GEMINI_API_KEY` to local environment or Streamlit Secrets.
- **Authentication/model error:** check the key, account permissions, and model ID.
- **Quota/rate limit:** wait, check account usage and current Google terms, or adjust usage.
- **Invalid PDF:** try exporting/saving the PDF again from the original source.
- **No selectable text:** likely a scanned/image PDF. OCR is not implemented; use a text-based PDF or OCR it separately before upload.
- **Low-text pages:** generated materials may omit image-only content; check the coverage report.
- **Deployment package error:** check build logs and confirm the selected Python/runtime supports the package versions.

## Privacy
Uploaded PDFs are processed in memory by the app and are not intentionally saved to disk. When you request AI generation, extracted lecture text is sent to Google's Gemini API. Review Google's current terms and your institution's rules before uploading private or copyrighted material. The app does not promise third-party non-retention.

## Limitations
- OCR for scanned pages is not implemented.
- PDF export is not implemented; Markdown and TXT downloads are available.
- Long documents are analyzed chunk by chunk with original page references before synthesis. If any chunk analysis fails, core study-pack generation stops and reports the incomplete sections instead of silently claiming full coverage. Later generated outputs can still be limited by model context or output limits. Coverage tracks PDF extraction and chunk analysis, not a guarantee that every generated answer uses every page.
- Source-page references returned by the model are validated for integer format but should still be checked against the original PDF.
- No user accounts, database, or persistent study history.
- Live Gemini API behavior, GitHub upload, and cloud deployment must be tested in the target account.

## Testing results
See the delivery message for the exact commands executed and actual outcomes in the build environment. Automated tests mock external Gemini calls and do not require a live API key.

## Gemini MCQ troubleshooting
- **Authentication error:** check that the `GEMINI_API_KEY` secret is correct and active. Never paste the key into chat, screenshots, logs, or source code.
- **Model unavailable / permission denied:** verify `GEMINI_MODEL` and that the API key's Google project has access to that model. The default is `gemini-2.5-flash`; it is not silently replaced if unavailable.
- **Quota exhausted:** check the API project's quota and billing/usage status. Waiting will not resolve a hard exhausted quota until quota is available again.
- **Rate limit or temporary service error:** wait briefly and retry. Only transient errors are retried automatically.
- **Invalid request:** check the server logs for the diagnostic category, HTTP status, and sanitized error detail. The app does not log lecture prompts or API keys intentionally.
- **Malformed MCQ output:** the app makes one bounded JSON repair attempt and one bounded schema-correction attempt. It displays an error rather than showing invalid questions.
- The extracted lecture stays in the current Streamlit session when generation fails, so a retry should not require another upload unless the page/session has been reset.

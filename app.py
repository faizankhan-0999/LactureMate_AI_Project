from __future__ import annotations
import os
import streamlit as st
from src.config import MAX_UPLOAD_MB, DEFAULT_MODEL, get_api_key
from src.pdf_processor import extract_pdf
from src.lecture_chunker import chunk_pages
from src.source_analyzer import analyze_chunks
from src.gemini_service import GeminiService, GeminiServiceError
from src.notes_generator import generate_notes, STUDY_MODES
from src.question_generator import generate_mcqs, generate_exam_questions, ValidationError
from src.flashcard_generator import generate_flashcards, generate_revision_sheet
from src.quiz_engine import score_quiz, restart_quiz_state
from src.export_service import notes_to_markdown, questions_to_markdown, mcqs_to_markdown, flashcards_to_markdown

st.set_page_config(page_title="LectureMate AI", page_icon="📚", layout="wide")
st.markdown("""
<style>
.stApp {background: radial-gradient(ellipse at top left,#17264a 0,#0b1224 42%,#080d19 100%); color:#edf2ff}
[data-testid="stSidebar"] {background:#0c1427;border-right:1px solid #263452}
.block-container {padding-top:2rem;max-width:1450px}
.lm-hero {padding:1.4rem 1.6rem;border:1px solid #2a3b60;border-radius:18px;background:linear-gradient(120deg,rgba(63,81,181,.22),rgba(22,163,174,.09));margin-bottom:1rem}
.lm-card {padding:1rem 1.1rem;border:1px solid #2b3854;border-radius:14px;background:rgba(20,31,54,.72)}
small,.muted {color:#aab7d0}
.stButton>button {border-radius:10px;border:1px solid #435a8d}
</style>
""", unsafe_allow_html=True)
st.markdown('<div class="lm-hero"><h1>📚 LectureMate AI</h1><p>Turn university lecture PDFs into clear notes, exam practice, MCQs, flashcards, and revision resources.</p><span class="muted">Source-aware learning • Three study modes • Student-controlled downloads</span></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## Your study workspace")
    st.caption("Upload a lecture, check its coverage, then create study materials.")
    mode = st.selectbox("Study mode", list(STUDY_MODES), index=1)
    mcq_count = st.selectbox("Number of MCQs", [5, 10, 15, 20, 30], index=1)
    question_count = st.slider("Practice questions", 5, 30, 10, 5)
    show_answers = st.toggle("Show practice answers immediately", value=False)
    want_flashcards = st.toggle("Generate flashcards", value=True)
    want_revision = st.toggle("Generate revision sheet", value=True)
    st.divider()
    st.caption(f"Model setting: `{DEFAULT_MODEL}`")

if "lecture_result" not in st.session_state: st.session_state.lecture_result = None
if "materials" not in st.session_state: st.session_state.materials = {}
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "quiz_state" not in st.session_state: st.session_state.quiz_state = restart_quiz_state()

uploaded = st.file_uploader("Upload your university lecture (PDF)", type=["pdf"], help=f"Maximum file size: {MAX_UPLOAD_MB} MB. Scanned PDFs need OCR, which is not built in.")
col1, col2 = st.columns([1, 1])
with col1:
    if uploaded:
        size_mb = uploaded.size / (1024 * 1024)
        st.info(f"**{uploaded.name}** · {size_mb:.2f} MB")
        if size_mb > MAX_UPLOAD_MB:
            st.error(f"File exceeds the {MAX_UPLOAD_MB} MB upload limit.")
        elif st.button("Extract lecture text", type="primary", use_container_width=True):
            try:
                result = extract_pdf(uploaded.getvalue(), uploaded.name)
                st.session_state.lecture_result = result
                st.session_state.materials = {}
                st.session_state.chat_history = []
                st.session_state.quiz_state = restart_quiz_state()
                st.success("PDF text extracted. Review the coverage report before generating materials.")
            except ValueError as exc:
                st.error(str(exc))
with col2:
    st.markdown('<div class="lm-card"><b>How it works</b><ol><li>Upload a text-based PDF.</li><li>Review page coverage and limitations.</li><li>Choose a study mode and generate resources.</li><li>Practice, review, and download your materials.</li></ol><small>Lecture text is sent to Google Gemini when you request AI generation. Do not upload material you are not permitted to share.</small></div>', unsafe_allow_html=True)

result = st.session_state.lecture_result
if result:
    st.divider()
    st.subheader("Lecture coverage")
    a,b,c,d = st.columns(4)
    a.metric("PDF pages", result.total_pages)
    b.metric("Pages with text", result.extracted_pages)
    c.metric("Low/empty text", len(result.low_text_pages))
    d.metric("Failed pages", len(result.failed_pages))
    coverage = result.coverage
    if coverage["all_pages_extractable"]: st.success("All pages yielded extractable text above the low-text threshold.")
    else: st.warning("Coverage is partial or uncertain. Review the page list below. Scanned pages are not read unless OCR is added.")
    if result.low_text_pages: st.write("Low/empty text pages:", ", ".join(map(str, result.low_text_pages)))
    if result.failed_pages: st.write("Pages that failed extraction:", ", ".join(map(str, result.failed_pages)))
    with st.expander("Preview extracted lecture text"):
        st.text(result.full_text[:12000] + ("\n… preview truncated" if len(result.full_text) > 12000 else ""))
    chunks = chunk_pages(result.pages)
    st.caption(f"{len(chunks)} content chunk(s) prepared. Original page references are retained in the source text.")
    api_key = get_api_key(st.secrets)
    if not api_key: st.warning("Gemini API key is not configured yet. Add `GEMINI_API_KEY` in Streamlit Secrets or your local environment to generate materials.")
    service = GeminiService(api_key=api_key) if api_key else None
    source_text = result.full_text
    source_pages = [p.page_number for p in result.pages if p.text.strip()]
    tabs = st.tabs(["Overview", "Study Notes", "Exam Questions", "MCQs", "Quiz Practice", "Flashcards", "AI Study Chat", "Downloads"])
    with tabs[0]:
        st.markdown("### Ready to study")
        st.write("The application has extracted selectable text and retained original PDF page numbers. Check the coverage report before relying on generated material.")
        st.write("**Selected mode:**", mode)
        if st.button("Generate core study pack", type="primary", disabled=service is None):
            try:
                with st.spinner(f"Analyzing {len(chunks)} lecture section(s) with original page references…"):
                    study_context = analyze_chunks(service, chunks, mode)
                st.session_state.materials["analysis_context"] = study_context
                with st.spinner("Generating teacher-quality notes from analyzed sections…"):
                    st.session_state.materials["notes"] = generate_notes(service, study_context, mode, source_pages)
                with st.spinner("Generating exam practice questions…"):
                    st.session_state.materials["questions"] = generate_exam_questions(service, study_context, question_count, source_pages)
                with st.spinner("Generating MCQs…"):
                    st.session_state.materials["mcqs"] = generate_mcqs(service, study_context, mcq_count, source_pages)
                if want_flashcards:
                    with st.spinner("Generating flashcards…"):
                        st.session_state.materials["flashcards"] = generate_flashcards(service, study_context, 12, source_pages)
                if want_revision:
                    with st.spinner("Generating revision sheet…"):
                        st.session_state.materials["revision"] = generate_revision_sheet(service, study_context, source_pages)
                st.session_state.quiz_state = restart_quiz_state()
                st.success("Study pack generated. Review each section and verify page references against the PDF.")
            except (GeminiServiceError, ValidationError, ValueError) as exc: st.error(str(exc))
            except Exception as exc: st.error(f"Generation did not complete: {exc}")
    with tabs[1]:
        st.markdown("### Teacher-quality study notes")
        if st.button("Generate / regenerate notes", disabled=service is None, key="gen_notes"):
            try:
                with st.spinner("Writing notes in the selected study mode…"):
                    st.session_state.materials["notes"] = generate_notes(service, st.session_state.materials.get("analysis_context", source_text), mode, source_pages)
            except Exception as exc: st.error(str(exc))
        if st.session_state.materials.get("notes"):
            st.markdown(st.session_state.materials["notes"])
            if st.button("Explain notes more simply", disabled=service is None):
                try: st.session_state.materials["simpler"] = service.generate("Explain the following notes in simpler English without changing meaning. Mark supplementary explanations clearly:\n" + st.session_state.materials["notes"])
                except Exception as exc: st.error(str(exc))
            if st.session_state.materials.get("simpler"): st.markdown(st.session_state.materials["simpler"])
        else: st.info("Generate notes to see them here. Changing the study mode changes the AI instructions.")
    with tabs[2]:
        st.markdown("### Exam practice questions")
        if st.button("Generate questions", disabled=service is None, key="gen_questions"):
            try: st.session_state.materials["questions"] = generate_exam_questions(service, st.session_state.materials.get("analysis_context", source_text), question_count, source_pages)
            except Exception as exc: st.error(str(exc))
        qs = st.session_state.materials.get("questions", [])
        if qs:
            for i,q in enumerate(qs,1):
                with st.expander(f"{i}. {q['question']} · {q['difficulty']}"):
                    st.write(f"Type: {q['type']} | Topic: {q['topic']}")
                    pages = q.get("source_pages", [])
                    st.caption("Source pages: " + (", ".join(map(str,pages)) if pages else "Not reliably identified"))
                    if show_answers: st.write("Suggested answer:", q["suggested_answer"])
                    else:
                        if st.button("Reveal suggested answer", key=f"answer_{i}"): st.write(q["suggested_answer"])
        else: st.info("Generate short, long, conceptual, and application-based practice questions.")
    with tabs[3]:
        st.markdown("### Multiple-choice questions")
        if st.button("Generate / regenerate MCQs", disabled=service is None, key="gen_mcqs"):
            try: st.session_state.materials["mcqs"] = generate_mcqs(service, st.session_state.materials.get("analysis_context", source_text), mcq_count, source_pages); st.session_state.quiz_state = restart_quiz_state()
            except Exception as exc: st.error(str(exc))
        mcqs = st.session_state.materials.get("mcqs", [])
        if mcqs:
            for i,q in enumerate(mcqs,1):
                with st.expander(f"{i}. {q['question']} · {q['difficulty']}"):
                    for letter in "ABCD": st.write(f"**{letter}.** {q['options'][letter]}")
                    st.caption(f"Topic: {q['topic']} · Source pages: {', '.join(map(str,q['source_pages'])) or 'Not reliably identified'}")
                    st.write(f"**Answer:** {q['correct_answer']} — {q['options'][q['correct_answer']]}")
                    st.write(q["explanation"])
        else: st.info("MCQs will have four options, one best answer, explanations, and validated source-page references.")
    with tabs[4]:
        st.markdown("### Interactive quiz")
        mcqs = st.session_state.materials.get("mcqs", [])
        if not mcqs: st.info("Generate MCQs first to start a quiz.")
        else:
            state = st.session_state.quiz_state
            if not state.get("answers"): state["answers"] = {}
            mode_quiz = st.radio("Quiz layout", ["One question at a time", "Review all questions"], horizontal=True)
            if mode_quiz == "One question at a time":
                idx = min(state.get("current_index",0),len(mcqs)-1); q=mcqs[idx]
                st.write(f"Question {idx+1} of {len(mcqs)} · {q['difficulty']} · {q['topic']}")
                selected = st.radio(q["question"], ["A","B","C","D"], format_func=lambda x:f"{x}. {q['options'][x]}", key=f"quiz_answer_{idx}")
                if st.button("Save answer", key=f"save_{idx}"):
                    state["answers"][idx] = selected
                    state["current_index"] = min(idx+1,len(mcqs)-1)
                    st.rerun()
            else:
                for idx,q in enumerate(mcqs):
                    st.write(f"**{idx+1}. {q['question']}**")
                    selected = st.radio("Choose an answer", ["A","B","C","D"], format_func=lambda x,opts=q["options"]:f"{x}. {opts[x]}", key=f"all_quiz_{idx}", index=None)
                    if selected: state["answers"][idx] = selected
            if st.button("Submit quiz", type="primary"):
                state["submitted"] = True; state["result"] = score_quiz(mcqs,state["answers"])
            if state.get("submitted"):
                score = state["result"] or score_quiz(mcqs,state["answers"])
                st.metric("Score", f"{score['correct']} / {score['total']}", f"{score['percentage']}%")
                st.write(f"Answered: {score['answered']} · Correct: {score['correct']} · Incorrect: {score['incorrect']}")
                for idx,q in enumerate(mcqs):
                    your = state["answers"].get(idx,"Not answered")
                    st.write(f"{'✅' if your == q['correct_answer'] else '❌'} {idx+1}. Your answer: {your} · Correct: {q['correct_answer']} — {q['explanation']}")
            if st.button("Restart quiz"):
                st.session_state.quiz_state = restart_quiz_state(); st.rerun()
    with tabs[5]:
        st.markdown("### Flashcards and revision")
        if st.button("Generate flashcards", disabled=service is None, key="gen_cards"):
            try: st.session_state.materials["flashcards"] = generate_flashcards(service,st.session_state.materials.get("analysis_context", source_text),12,source_pages)
            except Exception as exc: st.error(str(exc))
        cards = st.session_state.materials.get("flashcards", [])
        if cards:
            if "card_index" not in st.session_state: st.session_state.card_index = 0
            idx = st.session_state.card_index % len(cards); card=cards[idx]
            st.markdown(f"### Card {idx+1} / {len(cards)}")
            st.markdown(f"<div class='lm-card'><h3>{card['term']}</h3></div>", unsafe_allow_html=True)
            if st.button("Reveal answer", key="reveal_card"): st.session_state.reveal_card = idx
            if st.session_state.get("reveal_card") == idx:
                st.write(card["answer"])
                if card.get("example"): st.write("Example:",card["example"])
                st.caption("Source pages: " + (", ".join(map(str,card.get("source_pages",[]))) or "Not reliably identified"))
            left,right=st.columns(2)
            if left.button("← Previous", key="prev_card"): st.session_state.card_index=(idx-1)%len(cards); st.session_state.pop("reveal_card",None); st.rerun()
            if right.button("Next →", key="next_card"): st.session_state.card_index=(idx+1)%len(cards); st.session_state.pop("reveal_card",None); st.rerun()
        if st.button("Generate revision sheet", disabled=service is None, key="gen_revision"):
            try: st.session_state.materials["revision"] = generate_revision_sheet(service,st.session_state.materials.get("analysis_context", source_text),source_pages)
            except Exception as exc: st.error(str(exc))
        if st.session_state.materials.get("revision"): st.markdown(st.session_state.materials["revision"])
    with tabs[6]:
        st.markdown("### Ask about this lecture")
        st.caption("Answers are grounded in the active lecture where possible. Supplementary knowledge will be labeled.")
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
        prompt = st.chat_input("Ask a question about this lecture…", disabled=service is None)
        if prompt:
            st.session_state.chat_history.append({"role":"user","content":prompt})
            try:
                answer = service.generate("Answer the student's question using the lecture text first. Cite only original PDF pages evidenced by the source. If the lecture is insufficient, say so and label outside knowledge as supplementary.\nQuestion: " + prompt + "\nLecture:\n" + source_text[:50000])
                st.session_state.chat_history.append({"role":"assistant","content":answer})
            except Exception as exc: st.session_state.chat_history.append({"role":"assistant","content":f"I couldn't complete that request: {exc}"})
            st.rerun()
    with tabs[7]:
        st.markdown("### Download study materials")
        mats = st.session_state.materials
        if mats.get("notes"): st.download_button("Download notes (.md)", notes_to_markdown(result.filename,mats["notes"]), file_name="lecturemate-notes.md", mime="text/markdown")
        if mats.get("revision"): st.download_button("Download revision sheet (.txt)", mats["revision"], file_name="revision-sheet.txt", mime="text/plain")
        if mats.get("questions"): st.download_button("Download practice questions (.md)", questions_to_markdown(mats["questions"],True), file_name="practice-questions.md", mime="text/markdown")
        if mats.get("mcqs"): st.download_button("Download MCQs with answers (.md)", mcqs_to_markdown(mats["mcqs"],True), file_name="lecture-mcqs.md", mime="text/markdown")
        if mats.get("flashcards"): st.download_button("Download flashcards (.md)", flashcards_to_markdown(mats["flashcards"]), file_name="flashcards.md", mime="text/markdown")
        if not mats: st.info("Generate materials first. Downloads will appear here.")
        st.caption("PDF export is not included in this version; Markdown and TXT exports preserve headings and special characters.")
else:
    st.markdown("### Your study dashboard")
    st.info("Upload a text-based lecture PDF and select **Extract lecture text** to begin. Your study materials will appear after processing.")
    x,y,z = st.columns(3)
    x.markdown('<div class="lm-card"><h4>✍️ Understand</h4><p>Teacher-quality notes in simple, detailed, or exam-focused modes.</p></div>', unsafe_allow_html=True)
    y.markdown('<div class="lm-card"><h4>🧠 Practice</h4><p>MCQs, short and long questions, and an interactive quiz.</p></div>', unsafe_allow_html=True)
    z.markdown('<div class="lm-card"><h4>📥 Revise</h4><p>Flashcards, revision sheets, and downloadable study materials.</p></div>', unsafe_allow_html=True)

st.divider()
st.caption("LectureMate AI · Check AI-generated explanations and citations against your original lecture. Gemini model access and quotas depend on your Google API account.")

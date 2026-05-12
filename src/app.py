import random
import re
import tempfile
from datetime import datetime
from pathlib import Path
from difflib import SequenceMatcher

import streamlit as st
from src.config import CEFR_LEVELS, GROQ_API_KEY, PRACTICE_SENTENCES, USE_AI_FEEDBACK
from src.services.transcriber import WhisperTranscriber
from src.utils.database import Database


@st.cache_resource
def get_transcriber():
    return WhisperTranscriber()


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9àâçéèêëîïôûùüÿñæœ\s]", "", text)
    return re.sub(r"\s+", " ", text)


def compute_scores(reference: str, transcription_result: dict) -> dict:
    recognized_text = transcription_result.get("text", "")
    segments = transcription_result.get("segments", [])

    reference_norm = normalize_text(reference)
    recognized_norm = normalize_text(recognized_text)

    matcher = SequenceMatcher(None, reference_norm, recognized_norm)
    similarity = matcher.ratio()

    reference_words = reference_norm.split()
    recognized_words = recognized_norm.split()
    matched_words = sum(1 for word in reference_words if word in recognized_words)
    word_match_ratio = matched_words / max(1, len(reference_words))

    # Enhanced pronunciation scoring using timing information
    if segments:
        # Calculate speaking rate (words per minute)
        total_duration = segments[-1]["end"] - segments[0]["start"] if segments else 0
        word_count = len(recognized_words)
        speaking_rate = word_count / (total_duration / 60) if total_duration > 0 else 0

        # Ideal speaking rate for French is around 120-150 words per minute
        rate_score = max(0.0, min(1.0, 1.0 - abs(speaking_rate - 135) / 135))

        # Fluency based on segment continuity and natural pauses
        segment_durations = [seg["end"] - seg["start"] for seg in segments]
        avg_segment_duration = (
            sum(segment_durations) / len(segment_durations) if segment_durations else 0
        )
        fluency_timing = max(
            0.0, min(1.0, 1.0 - abs(avg_segment_duration - 2.0) / 2.0)
        )  # Ideal ~2 seconds per segment

        pronunciation = max(0.0, min(1.0, similarity * 0.7 + rate_score * 0.3))
        fluency = max(0.0, min(1.0, fluency_timing * 0.6 + word_match_ratio * 0.4))
    else:
        pronunciation = max(0.0, min(1.0, similarity))
        fluency = max(0.0, min(1.0, 0.1 + 0.9 * word_match_ratio))

    grammar = max(0.0, min(1.0, 0.25 + 0.75 * word_match_ratio))
    vocabulary = max(0.0, min(1.0, word_match_ratio))

    overall = round((pronunciation + fluency + grammar + vocabulary) / 4 * 100, 1)
    return {
        "pronunciation": round(pronunciation * 100, 1),
        "fluency": round(fluency * 100, 1),
        "grammar": round(grammar * 100, 1),
        "vocabulary": round(vocabulary * 100, 1),
        "overall": overall,
        "similarity": round(similarity * 100, 1),
    }


def build_feedback(scores: dict, recognized_text: str, target_text: str) -> str:
    if not recognized_text:
        return "No text was recognized. Make sure the audio is clear and try again."

    comments = [
        f"Pronunciation: {scores['pronunciation']}%.",
        f"Fluency: {scores['fluency']}%.",
        f"Grammar: {scores['grammar']}%.",
        f"Vocabulary: {scores['vocabulary']}%.",
    ]

    if scores["overall"] >= 85:
        comments.append(
            "Great job! You matched the target sentence well and your pronunciation is strong."
        )
    elif scores["overall"] >= 65:
        comments.append("Good effort. Focus on the missing words and fluency.")
    else:
        comments.append(
            "Work on pronunciation one word at a time and listen to the sentence before repeating it."
        )

    if normalize_text(recognized_text) != normalize_text(target_text):
        comments.append(
            "The recognized sentence differs from the target sentence. Try to get closer to the suggested text."
        )

    if USE_AI_FEEDBACK and GROQ_API_KEY:
        comments.append(
            "Additional AI feedback can be enabled by setting GROQ_API_KEY."
        )

    return " ".join(comments)


def save_uploaded_audio(username: str, audio_bytes: bytes, original_name: str) -> str:
    audio_dir = Path("data/audio")
    audio_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = Path(original_name).suffix or ".wav"
    filename = audio_dir / f"{username}_{timestamp}{suffix}"
    filename.write_bytes(audio_bytes)
    return str(filename)


def main():
    st.set_page_config(page_title="French Evaluator", page_icon="🇫🇷", layout="wide")

    st.title("French Pronunciation Evaluator")
    st.markdown(
        "This app helps learners practice French pronunciation, transcribe spoken audio, and track progress over time."
    )

    sidebar = st.sidebar
    sidebar.header("Session Settings")
    username = sidebar.text_input("Username", value="guest")
    cefr_level = sidebar.selectbox("CEFR Level", CEFR_LEVELS, index=0)
    sentence_options = PRACTICE_SENTENCES.get(cefr_level, [])

    if (
        "cefr_level" not in st.session_state
        or st.session_state.cefr_level != cefr_level
    ):
        st.session_state.cefr_level = cefr_level
        st.session_state.selected_sentence = (
            random.choice(sentence_options) if sentence_options else ""
        )

    if (
        "selected_sentence" not in st.session_state
        or st.session_state.selected_sentence not in sentence_options
    ):
        st.session_state.selected_sentence = (
            random.choice(sentence_options) if sentence_options else ""
        )

    selected_sentence = st.session_state.selected_sentence

    sidebar.markdown("---")
    sidebar.write("Optional: enable GROQ for deeper AI feedback.")
    sidebar.write(
        f"GROQ enabled: {'Yes' if USE_AI_FEEDBACK and GROQ_API_KEY else 'No'}"
    )

    transcriber = get_transcriber()
    database = Database()

    c1, c2 = st.columns([2, 3])

    with c1:
        st.subheader("Target sentence")
        st.write(f"**{selected_sentence}**")

        def refresh_sentence():
            if sentence_options:
                st.session_state.selected_sentence = random.choice(sentence_options)

        st.button("🔄 Refresh sentence", on_click=refresh_sentence)

        st.subheader("Upload a recording")
        upload = st.file_uploader(
            "Upload an audio file (MP3, WAV, M4A)",
            type=["mp3", "wav", "m4a", "ogg", "flac"],
        )

        if upload is not None:
            audio_bytes = upload.read()
            audio_path = save_uploaded_audio(username, audio_bytes, upload.name)
            st.audio(audio_bytes, format=upload.type)
            st.info(f"File saved: {audio_path}")

            with st.spinner("Transcribing..."):
                result = transcriber.transcribe(audio_bytes, language="fr")

            recognized_text = result.get("text", "")
            if result.get("error"):
                st.error(f"Transcription error: {result['error']}")
                recognized_text = ""

            st.subheader("Recognized text")
            st.write(recognized_text or "No transcription available.")

            scores = compute_scores(selected_sentence, result)
            feedback_text = build_feedback(scores, recognized_text, selected_sentence)

            st.subheader("Evaluation score")
            st.metric("Overall score", f"{scores['overall']} %")
            st.write(
                f"Pronunciation: {scores['pronunciation']} %, Fluency: {scores['fluency']} %, Grammar: {scores['grammar']} %, Vocabulary: {scores['vocabulary']} %."
            )
            st.markdown(f"**Feedback:** {feedback_text}")

            database.add_attempt(
                username=username,
                practice_sentence=selected_sentence,
                recognized_text=recognized_text,
                cefr_level=cefr_level,
                pronunciation_score=scores["pronunciation"],
                fluency_score=scores["fluency"],
                grammar_score=scores["grammar"],
                vocabulary_score=scores["vocabulary"],
                overall_score=scores["overall"],
                feedback=feedback_text,
                audio_path=audio_path,
            )
            database.update_progress(username, cefr_level, scores["overall"])
            if sentence_options:
                st.session_state.selected_sentence = random.choice(sentence_options)

    with c2:
        st.subheader("Dashboard")
        progress = database.get_user_progress(username)
        recent = database.get_recent_attempts(username, limit=10)

        if progress:
            st.write("### Progress by level")
            st.table(progress)
        else:
            st.info("No progress recorded for this user.")

        if recent:
            st.write("### Recent attempts")
            st.dataframe(recent)
        else:
            st.info("No recent attempts.")

    st.markdown("---")
    st.write(
        "Upload a voice recording to get a transcription, pronunciation score, and progress tracking."
    )


if __name__ == "__main__":
    main()

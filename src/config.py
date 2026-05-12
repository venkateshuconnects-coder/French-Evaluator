"""Configuration settings for French Evaluator."""

import os
from dotenv import load_dotenv

load_dotenv()

# Whisper Configuration
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "tiny")
WHISPER_DEVICE = "cpu"  # Change to "cuda" if GPU available

# TTS Configuration
TTS_VOICE = os.getenv("TTS_VOICE", "fr-FR-ColetteNeural")
TTS_RATE = float(os.getenv("TTS_RATE", "1.0"))

# Database Configuration
DB_PATH = "data/db/french_evaluator.db"

# Audio Configuration
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHUNK_DURATION = 30  # seconds

# CEFR Levels
CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

# Scoring Thresholds
PRONUNCIATION_WEIGHTS = {
    "phoneme_similarity": 0.40,
    "fluency": 0.20,
    "grammar": 0.20,
    "vocabulary": 0.20,
}

# Optional Groq API for AI feedback (free tier)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
USE_AI_FEEDBACK = bool(GROQ_API_KEY)

# Practice Sentences by CEFR Level
PRACTICE_SENTENCES = {
    "A1": [
        "Bonjour, comment allez-vous ?",
        "Je m'appelle Marie.",
        "Enchanté de vous rencontrer.",
        "Quel est votre nom ?",
        "Où habitez-vous ?",
    ],
    "A2": [
        "Je suis étudiant en français.",
        "Vous venez d'où ?",
        "Qu'est-ce que vous aimez faire ?",
        "Je travaille dans une entreprise.",
        "Pouvez-vous m'aider ?",
    ],
    "B1": [
        "Pourriez-vous m'expliquer cette leçon ?",
        "J'aimerais améliorer mon français.",
        "Selon moi, c'est une bonne idée.",
        "Qu'en pensez-vous de cette situation ?",
        "Je crois que nous devrions continuer.",
    ],
    "B2": [
        "Bien que ce soit difficile, je persiste.",
        "À mon avis, les gouvernements devraient investir davantage.",
        "Il est important de noter que la situation évolue.",
        "En contraste avec les années précédentes, la tendance a changé.",
        "Cette approche présente des avantages considérables.",
    ],
    "C1": [
        "Nonobstant les obstacles rencontrés, nous avons réussi.",
        "Il convient de souligner l'importance de cette nuance.",
        "Hormis quelques détails mineurs, tout est en ordre.",
        "À l'instar de nombreux pays, la France doit s'adapter.",
        "Cette thèse suscite des interrogations profondes.",
    ],
    "C2": [
        "Bien entendu, la sophistication de ce raisonnement ne peut échapper à l'analyste.",
        "Loin de se limiter à cette dimension, la problématique s'inscrit dans un cadre plus vaste.",
        "Paradoxalement, cette apparente contradiction constitue le fondement même de la théorie.",
        "Il convient de déplorer que les tenants de cette approche n'aient pas suffisamment développé.",
        "Cette perspective, quoique pertinente, souffre d'une certaine prétention théorique.",
    ],
}

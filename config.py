import os


# ==========================================
# BASE DIRECTORY
# ==========================================

BASE_DIR = os.path.abspath(
    os.path.dirname(
        __file__
    )
)


# ==========================================
# APPLICATION
# ==========================================

APP_HOST = (
    os.getenv(
        "APP_HOST",
        "127.0.0.1"
    )
)


APP_PORT = int(
    os.getenv(
        "APP_PORT",
        "5000"
    )
)


DEBUG = (
    os.getenv(
        "DEBUG",
        "true"
    ).lower()
    ==
    "true"
)


# ==========================================
# UPLOAD SETTINGS
# ==========================================

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)


MAX_CONTENT_LENGTH = (
    50
    *
    1024
    *
    1024
)


# ==========================================
# ALLOWED FILE TYPES
# ==========================================

ALLOWED_EXTENSIONS = {

    "txt",
    "pdf",
    "docx",
    "csv",
    "md"

}


# ==========================================
# CHUNKING SETTINGS
# ==========================================

# Maximum number of characters
# in one document chunk.

CHUNK_SIZE = int(
    os.getenv(
        "CHUNK_SIZE",
        "1000"
    )
)


# Number of characters shared
# between consecutive chunks.

CHUNK_OVERLAP = int(
    os.getenv(
        "CHUNK_OVERLAP",
        "200"
    )
)


# ==========================================
# CHROMADB
# ==========================================

CHROMA_DB_PATH = os.path.join(
    BASE_DIR,
    "chroma_db"
)


CHROMA_COLLECTION_NAME = (
    "documents"
)


# ==========================================
# EMBEDDING MODEL
# ==========================================

EMBEDDING_MODEL = (
    "sentence-transformers/"
    "all-MiniLM-L6-v2"
)


# ==========================================
# RAG SEARCH SETTINGS
# ==========================================

MAX_TOP_K = 10


TOPIC_SEARCH_RESULTS = 4


MAX_CONTEXT_CHUNKS = 4


# ==========================================
# EXACT TOPIC MATCH
# ==========================================

REQUIRE_EXACT_TOPIC_MATCH = True


# ==========================================
# OLLAMA SETTINGS
# ==========================================

OLLAMA_HOST = (
    os.getenv(
        "OLLAMA_HOST",
        "http://localhost:11434"
    )
)


OLLAMA_MODEL = (
    os.getenv(
        "OLLAMA_MODEL",
        "llama3.2"
    )
)


# ==========================================
# LLM SETTINGS
# ==========================================

LLM_TEMPERATURE = float(
    os.getenv(
        "LLM_TEMPERATURE",
        "0.1"
    )
)


LLM_NUM_PREDICT = int(
    os.getenv(
        "LLM_NUM_PREDICT",
        "1024"
    )
)


LLM_NUM_CTX = int(
    os.getenv(
        "LLM_NUM_CTX",
        "4096"
    )
)


# ==========================================
# AVAILABLE MODEL SETTINGS
# ==========================================

MAX_AVAILABLE_MODELS = int(
    os.getenv(
        "MAX_AVAILABLE_MODELS",
        "50"
    )
)


MODEL_LIST_CACHE_SECONDS = int(
    os.getenv(
        "MODEL_LIST_CACHE_SECONDS",
        "30"
    )
)
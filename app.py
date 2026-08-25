import json
import logging
import os
import re
import time
import uuid

from flask import (
    Flask,
    Response,
    jsonify,
    render_template,
    request,
    stream_with_context
)

from werkzeug.utils import secure_filename

from config import (
    ALLOWED_EXTENSIONS,
    APP_HOST,
    APP_PORT,
    DEBUG,
    MAX_CONTENT_LENGTH,
    MAX_CONTEXT_CHUNKS,
    MAX_TOP_K,
    TOPIC_SEARCH_RESULTS,
    REQUIRE_EXACT_TOPIC_MATCH,
    UPLOAD_FOLDER
)

from services.document_service import (
    DocumentService
)

from services.embedding_service import (
    EmbeddingService
)

from services.llm_service import (
    LLMService
)

from services.vector_service import (
    VectorService
)


# ==========================================
# LOGGING
# ==========================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# ==========================================
# FLASK APPLICATION
# ==========================================

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


# ==========================================
# ENSURE UPLOAD DIRECTORY EXISTS
# ==========================================

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ==========================================
# INITIALIZE SERVICES
# ==========================================

embedding_service = EmbeddingService()

vector_service = VectorService()

document_service = DocumentService(
    vector_service,
    embedding_service
)

llm_service = LLMService()


logger.info(
    "RAG services initialized."
)


# ==========================================
# CHECK ALLOWED FILE
# ==========================================

def allowed_file(filename):

    if "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    return extension in ALLOWED_EXTENSIONS


# ==========================================
# NORMALIZE TOPIC
# ==========================================

def normalize_topic(topic):

    if not topic:
        return ""

    topic = topic.strip()

    topic = re.sub(
        r"\s+",
        " ",
        topic
    )

    return topic.strip()


# ==========================================
# REMOVE DUPLICATE TOPICS
# ==========================================

def remove_duplicate_topics(topics):

    unique_topics = []

    seen_topics = set()

    for topic in topics:

        normalized = normalize_topic(
            topic
        ).lower()

        if not normalized:
            continue

        if normalized in seen_topics:
            continue

        seen_topics.add(
            normalized
        )

        unique_topics.append(
            normalize_topic(topic)
        )

    return unique_topics


# ==========================================
# EXTRACT TOPICS FROM QUERY
# ==========================================

def extract_query_topics(query):

    if not query:
        return []

    original_query = query.strip()

    if not original_query:
        return []

    # --------------------------------------
    # REMOVE TRAILING PUNCTUATION
    # --------------------------------------

    cleaned_query = re.sub(
        r"[?.!]+$",
        "",
        original_query
    )

    # --------------------------------------
    # REMOVE COMMON QUESTION PREFIXES
    #
    # Example:
    #
    # How does Kubernetes work with AWS
    #
    # becomes:
    #
    # Kubernetes work with AWS
    # --------------------------------------

    cleaned_query = re.sub(
        (
            r"^(?:"
            r"what\s+is|"
            r"what\s+are|"
            r"explain|"
            r"tell\s+me\s+about|"
            r"define|"
            r"describe|"
            r"how\s+does|"
            r"how\s+do|"
            r"how\s+is|"
            r"how\s+are|"
            r"can\s+you\s+explain|"
            r"can\s+you\s+describe|"
            r"please\s+explain"
            r")\s+"
        ),
        "",
        cleaned_query,
        flags=re.IGNORECASE
    )

    # --------------------------------------
    # SPLIT USING MAIN SEPARATORS
    #
    # Example:
    #
    # Kubernetes and AWS and Terraform
    #
    # becomes:
    #
    # Kubernetes
    # AWS
    # Terraform
    # --------------------------------------

    parts = re.split(
        r"\s*(?:,|&|\band\b|\bor\b)\s*",
        cleaned_query,
        flags=re.IGNORECASE
    )

    topics = []

    # --------------------------------------
    # PROCESS EACH PART
    # --------------------------------------

    for part in parts:

        part = normalize_topic(part)

        if not part:
            continue

        # ----------------------------------
        # REMOVE RELATIONSHIP WORDS
        #
        # Kubernetes work with AWS
        #
        # becomes two possible segments:
        #
        # Kubernetes
        # AWS
        # ----------------------------------

        relationship_parts = re.split(
            (
                r"\s+(?:"
                r"work\s+with|"
                r"works\s+with|"
                r"working\s+with|"
                r"integrate\s+with|"
                r"integrates\s+with|"
                r"integration\s+with|"
                r"used\s+with|"
                r"use\s+with|"
                r"using|"
                r"with|"
                r"between"
                r")\s+"
            ),
            part,
            flags=re.IGNORECASE
        )

        for relationship_part in relationship_parts:

            topic = normalize_topic(
                relationship_part
            )

            if not topic:
                continue

            # ------------------------------
            # REMOVE COMMON ACTION WORDS
            # ------------------------------

            topic = re.sub(
                (
                    r"\b(?:"
                    r"work|"
                    r"works|"
                    r"working|"
                    r"function|"
                    r"functions|"
                    r"operate|"
                    r"operates|"
                    r"connect|"
                    r"connects|"
                    r"interact|"
                    r"interacts"
                    r")\b"
                ),
                " ",
                topic,
                flags=re.IGNORECASE
            )

            # ------------------------------
            # REMOVE ARTICLES
            # ------------------------------

            topic = re.sub(
                r"\b(?:the|a|an)\b",
                " ",
                topic,
                flags=re.IGNORECASE
            )

            # ------------------------------
            # NORMALIZE SPACES
            # ------------------------------

            topic = normalize_topic(
                topic
            )

            if topic:
                topics.append(
                    topic
                )

    # --------------------------------------
    # SECOND PASS:
    # HANDLE CASES SUCH AS
    #
    # Kubernetes AWS
    #
    # If a multi-word phrase remains, we do
    # NOT blindly split all words because
    # legitimate topics can contain spaces.
    #
    # --------------------------------------

    final_topics = []

    for topic in topics:

        topic = normalize_topic(
            topic
        )

        if not topic:
            continue

        final_topics.append(
            topic
        )

    return remove_duplicate_topics(
        final_topics
    )


# ==========================================
# CHECK EXACT TOPIC MATCH
# ==========================================

def topic_exists_in_results(
    topic,
    documents
):

    if not documents:
        return False

    normalized_topic = normalize_topic(
        topic
    ).lower()

    if not normalized_topic:
        return False

    pattern = (
        r"(?<!\w)"
        +
        re.escape(
            normalized_topic
        )
        +
        r"(?!\w)"
    )

    for document in documents:

        if not document:
            continue

        normalized_document = (
            document
            .lower()
        )

        if re.search(
            pattern,
            normalized_document
        ):
            return True

    return False


# ==========================================
# REMOVE DUPLICATE DOCUMENT CHUNKS
# ==========================================

def remove_duplicate_documents(documents):

    unique_documents = []

    seen = set()

    for document in documents:

        if not document:
            continue

        normalized = document.strip()

        if not normalized:
            continue

        normalized_key = re.sub(
            r"\s+",
            " ",
            normalized
        ).lower()

        if normalized_key in seen:
            continue

        seen.add(
            normalized_key
        )

        unique_documents.append(
            normalized
        )

    return unique_documents


# ==========================================
# REMOVE DUPLICATE SOURCES
# ==========================================

def remove_duplicate_sources(sources):

    unique_sources = []

    seen = set()

    for source in sources:

        filename = source.get(
            "filename",
            ""
        )

        chunk_id = source.get(
            "chunk_id",
            ""
        )

        key = (
            filename,
            chunk_id
        )

        if key in seen:
            continue

        seen.add(key)

        unique_sources.append(
            source
        )

    return unique_sources


# ==========================================
# SEARCH FOR A SINGLE TOPIC
# ==========================================

def search_topic(
    topic,
    top_k
):

    logger.info(
        "Searching for topic: %s",
        topic
    )

    # --------------------------------------
    # CREATE EMBEDDING
    # --------------------------------------

    topic_embedding = (
        embedding_service
        .create_query_embedding(
            topic
        )
    )

    # --------------------------------------
    # SEARCH CHROMADB
    # --------------------------------------

    results = (
        vector_service
        .search(
            query_embedding=topic_embedding,
            top_k=top_k
        )
    )

    documents = results.get(
        "documents",
        [[]]
    )

    metadatas = results.get(
        "metadatas",
        [[]]
    )

    distances = results.get(
        "distances",
        [[]]
    )

    # ======================================
    # NORMALIZE RESULTS
    # ======================================

    documents = (
        documents[0]
        if documents and documents[0]
        else []
    )

    metadatas = (
        metadatas[0]
        if metadatas and metadatas[0]
        else []
    )

    distances = (
        distances[0]
        if distances and distances[0]
        else []
    )

    # ======================================
    # REMOVE DUPLICATE DOCUMENTS
    # ======================================

    documents = remove_duplicate_documents(
        documents
    )

    # ======================================
    # BUILD SOURCES
    # ======================================

    sources = []

    for index, metadata in enumerate(
        metadatas
    ):

        if not metadata:
            continue

        source = {
            "filename":
                metadata.get(
                    "filename",
                    metadata.get(
                        "original_filename",
                        "Unknown Document"
                    )
                ),

            "document_id":
                metadata.get(
                    "document_id"
                ),

            "chunk_id":
                metadata.get(
                    "chunk_id",
                    index + 1
                )
        }

        if index < len(distances):

            source["distance"] = (
                distances[index]
            )

        sources.append(
            source
        )

    sources = remove_duplicate_sources(
        sources
    )

    logger.info(
        "Topic '%s' returned %s relevant results",
        topic,
        len(documents)
    )

    # ======================================
    # EXACT TOPIC VALIDATION
    # ======================================

    if REQUIRE_EXACT_TOPIC_MATCH:

        exact_match = topic_exists_in_results(
            topic,
            documents
        )

        logger.info(
            "Topic '%s' exact match: %s",
            topic,
            exact_match
        )

        if not exact_match:

            return {
                "topic": topic,
                "found": False,
                "documents": [],
                "sources": []
            }

    return {
        "topic": topic,
        "found": len(documents) > 0,
        "documents": documents,
        "sources": sources
    }


# ==========================================
# BUILD TOPIC CONTEXT
# ==========================================

def build_topic_context(topic_results):

    context_sections = []

    found_topics = []

    missing_topics = []

    all_sources = []

    for result in topic_results:

        topic = result["topic"]

        found = result["found"]

        documents = result["documents"]

        sources = result.get(
            "sources",
            []
        )

        if not found:

            missing_topics.append(
                topic
            )

            continue

        found_topics.append(
            topic
        )

        topic_context = "\n\n".join(
            documents[
                :MAX_CONTEXT_CHUNKS
            ]
        )

        context_sections.append(
            f"""
TOPIC: {topic}

INFORMATION ABOUT {topic}:

{topic_context}
""".strip()
        )

        all_sources.extend(
            sources[
                :MAX_CONTEXT_CHUNKS
            ]
        )

    final_context = "\n\n".join(
        context_sections
    )

    all_sources = remove_duplicate_sources(
        all_sources
    )

    return {
        "context": final_context,
        "found_topics": found_topics,
        "missing_topics": missing_topics,
        "sources": all_sources
    }


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# ==========================================
# HEALTH CHECK
# ==========================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health():

    try:

        ollama_status = (
            llm_service
            .check_connection()
        )

        return jsonify(
            {
                "status":
                    (
                        "healthy"
                        if ollama_status
                        else "unhealthy"
                    ),

                "ollama":
                    ollama_status
            }
        ), (
            200
            if ollama_status
            else 503
        )

    except Exception as error:

        logger.exception(
            "Health check failed."
        )

        return jsonify(
            {
                "status": "unhealthy",
                "error": str(error)
            }
        ), 500


# ==========================================
# GET AVAILABLE MODELS
# ==========================================

@app.route(
    "/api/models",
    methods=["GET"]
)
def get_models():

    try:

        models = (
            llm_service
            .get_available_models()
        )

        return jsonify(
            {
                "models": models
            }
        )

    except Exception as error:

        logger.exception(
            "Could not get models."
        )

        return jsonify(
            {
                "error": str(error)
            }
        ), 500


# ==========================================
# UPLOAD DOCUMENTS
# ==========================================

@app.route(
    "/api/documents/upload",
    methods=["POST"]
)
def upload_documents():

    try:

        uploaded_files = (
            request.files.getlist(
                "files"
            )
        )

        # Backward compatibility.

        if not uploaded_files:

            single_file = (
                request.files.get(
                    "file"
                )
            )

            if single_file:

                uploaded_files = [
                    single_file
                ]

        if not uploaded_files:

            return jsonify(
                {
                    "error":
                        "No files provided."
                }
            ), 400

        results = []

        for file in uploaded_files:

            if not file:
                continue

            if not file.filename:

                results.append(
                    {
                        "status": "error",
                        "filename": "Unknown",
                        "message":
                            "No file selected."
                    }
                )

                continue

            if not allowed_file(
                file.filename
            ):

                results.append(
                    {
                        "status": "error",
                        "filename": file.filename,
                        "message":
                            "Unsupported file type."
                    }
                )

                continue

            try:

                filename = secure_filename(
                    file.filename
                )

                document_id = str(
                    uuid.uuid4()
                )

                file_path = os.path.join(
                    UPLOAD_FOLDER,
                    f"{document_id}_{filename}"
                )

                file.save(
                    file_path
                )

                result = (
                    document_service
                    .process_document(
                        file_path=file_path,
                        original_filename=filename,
                        document_id=document_id
                    )
                )

                if isinstance(
                    result,
                    dict
                ):

                    result.setdefault(
                        "filename",
                        filename
                    )

                    result.setdefault(
                        "status",
                        "success"
                    )

                    result.setdefault(
                        "message",
                        "Document processed successfully."
                    )

                else:

                    result = {
                        "status": "success",
                        "filename": filename,
                        "message":
                            "Document processed successfully."
                    }

                results.append(
                    result
                )

            except Exception as error:

                logger.exception(
                    "Failed to process document: %s",
                    file.filename
                )

                results.append(
                    {
                        "status": "error",
                        "filename": file.filename,
                        "message": str(error)
                    }
                )

        successful_files = [
            result
            for result in results
            if result.get("status") != "error"
        ]

        failed_files = [
            result
            for result in results
            if result.get("status") == "error"
        ]

        if not successful_files:

            return jsonify(
                {
                    "message":
                        "Document upload failed.",

                    "results":
                        results
                }
            ), 400

        message = (
            f"{len(successful_files)} document(s) "
            f"uploaded successfully."
        )

        if failed_files:

            message += (
                f" {len(failed_files)} document(s) "
                f"failed."
            )

        return jsonify(
            {
                "message": message,
                "results": results
            }
        )

    except Exception as error:

        logger.exception(
            "Document upload failed."
        )

        return jsonify(
            {
                "error": str(error)
            }
        ), 500


# ==========================================
# GET DOCUMENTS
# ==========================================

@app.route(
    "/api/documents",
    methods=["GET"]
)
def get_documents():

    try:

        documents = (
            document_service
            .get_documents()
        )

        return jsonify(
            {
                "documents": documents
            }
        )

    except Exception as error:

        logger.exception(
            "Could not retrieve documents."
        )

        return jsonify(
            {
                "error": str(error)
            }
        ), 500


# ==========================================
# DELETE DOCUMENT
# ==========================================

@app.route(
    "/api/documents/<document_id>",
    methods=["DELETE"]
)
def delete_document(document_id):

    try:

        result = (
            document_service
            .delete_document(
                document_id
            )
        )

        if isinstance(
            result,
            dict
        ):
            return jsonify(result)

        return jsonify(
            {
                "message":
                    "Document deleted successfully."
            }
        )

    except Exception as error:

        logger.exception(
            "Document deletion failed."
        )

        return jsonify(
            {
                "error": str(error)
            }
        ), 500


# ==========================================
# RESET DATABASE
# ==========================================

@app.route(
    "/api/documents/reset",
    methods=["DELETE"]
)
def reset_documents():

    try:

        result = (
            document_service
            .reset_documents()
        )

        if isinstance(
            result,
            dict
        ):
            return jsonify(result)

        return jsonify(
            {
                "message":
                    "All documents have been removed."
            }
        )

    except Exception as error:

        logger.exception(
            "Database reset failed."
        )

        return jsonify(
            {
                "error": str(error)
            }
        ), 500


# ==========================================
# STREAM RAG QUERY
# ==========================================

@app.route(
    "/api/query/stream",
    methods=["POST"]
)
def query_stream():

    try:

        total_start_time = time.perf_counter()

        data = request.get_json() or {}

        query = (
            data.get(
                "query",
                ""
            ).strip()
        )

        model_name = (
            data.get(
                "model",
                ""
            ).strip()
        )

        if not query:

            return jsonify(
                {
                    "error":
                        "Query is required."
                }
            ), 400

        # ==================================
        # GET TOP K
        # ==================================

        requested_top_k = data.get(
            "top_k",
            TOPIC_SEARCH_RESULTS
        )

        try:

            requested_top_k = int(
                requested_top_k
            )

        except Exception:

            requested_top_k = (
                TOPIC_SEARCH_RESULTS
            )

        top_k = max(
            1,
            min(
                requested_top_k,
                MAX_TOP_K
            )
        )

        # ==================================
        # EXTRACT TOPICS
        # ==================================

        topics = extract_query_topics(
            query
        )

        logger.info(
            "Extracted query topics: %s",
            topics
        )

        if not topics:

            topics = [query]

        # ==================================
        # SEARCH EACH TOPIC
        # ==================================

        retrieval_start_time = (
            time.perf_counter()
        )

        topic_results = []

        for topic in topics:

            result = search_topic(
                topic=topic,
                top_k=top_k
            )

            topic_results.append(
                result
            )

        retrieval_time = round(
            time.perf_counter()
            -
            retrieval_start_time,
            4
        )

        # ==================================
        # BUILD CONTEXT
        # ==================================

        context_data = build_topic_context(
            topic_results
        )

        context = context_data["context"]

        found_topics = (
            context_data["found_topics"]
        )

        missing_topics = (
            context_data["missing_topics"]
        )

        sources = (
            context_data["sources"]
        )

        logger.info(
            "Found topics: %s",
            found_topics
        )

        logger.info(
            "Missing topics: %s",
            missing_topics
        )

        # ==================================
        # STREAM RESPONSE
        # ==================================

        def generate_response():

            try:

                # ----------------------------------
                # ALL TOPICS MISSING
                # ----------------------------------

                if not found_topics:

                    start_event = {
                        "type": "start",
                        "sources": [],
                        "retrieval_time":
                            retrieval_time
                    }

                    yield (
                        json.dumps(
                            start_event
                        )
                        +
                        "\n"
                    )

                    for topic in topics:

                        content = (
                            f"## {topic}\n\n"
                            f"I could not find information "
                            f"about {topic} in the uploaded "
                            f"documents.\n\n"
                        )

                        yield (
                            json.dumps(
                                {
                                    "type": "token",
                                    "content": content
                                }
                            )
                            +
                            "\n"
                        )

                    total_time = round(
                        time.perf_counter()
                        -
                        total_start_time,
                        4
                    )

                    done_event = {
                        "type": "done",

                        "model":
                            model_name
                            or
                            llm_service.model,

                        "generation_time": 0,

                        "retrieval_time":
                            retrieval_time,

                        "total_time":
                            total_time
                    }

                    yield (
                        json.dumps(
                            done_event
                        )
                        +
                        "\n"
                    )

                    return

                # ----------------------------------
                # START EVENT
                # ----------------------------------

                start_event = {
                    "type": "start",
                    "sources": sources,
                    "retrieval_time":
                        retrieval_time
                }

                yield (
                    json.dumps(
                        start_event
                    )
                    +
                    "\n"
                )

                # ----------------------------------
                # MISSING TOPICS
                # ----------------------------------

                for topic in missing_topics:

                    content = (
                        f"## {topic}\n\n"
                        f"I could not find information "
                        f"about {topic} in the uploaded "
                        f"documents.\n\n"
                    )

                    yield (
                        json.dumps(
                            {
                                "type": "token",
                                "content": content
                            }
                        )
                        +
                        "\n"
                    )

                # ----------------------------------
                # GENERATE AI ANSWER
                # ----------------------------------

                generation_start_time = (
                    time.perf_counter()
                )

                selected_model = (
                    llm_service
                    .validate_model(
                        model_name
                        or
                        None
                    )
                )

                for chunk in (
                    llm_service
                    .stream_answer(
                        question=query,
                        context=context,
                        model_name=selected_model
                    )
                ):

                    chunk_type = (
                        chunk.get(
                            "type"
                        )
                    )

                    if (
                        chunk_type
                        ==
                        "token"
                    ):

                        content = (
                            chunk.get(
                                "content",
                                ""
                            )
                        )

                        if content:

                            yield (
                                json.dumps(
                                    {
                                        "type": "token",
                                        "content": content
                                    }
                                )
                                +
                                "\n"
                            )

                generation_time = round(
                    time.perf_counter()
                    -
                    generation_start_time,
                    4
                )

                total_time = round(
                    time.perf_counter()
                    -
                    total_start_time,
                    4
                )

                # ----------------------------------
                # DONE EVENT
                # ----------------------------------

                done_event = {
                    "type": "done",

                    "model":
                        selected_model,

                    "generation_time":
                        generation_time,

                    "retrieval_time":
                        retrieval_time,

                    "total_time":
                        total_time
                }

                yield (
                    json.dumps(
                        done_event
                    )
                    +
                    "\n"
                )

            except Exception as error:

                logger.exception(
                    "Streaming generation failed."
                )

                error_event = {
                    "type": "error",
                    "message":
                        str(error)
                }

                yield (
                    json.dumps(
                        error_event
                    )
                    +
                    "\n"
                )

        return Response(
            stream_with_context(
                generate_response()
            ),
            content_type=
                "application/x-ndjson"
        )

    except Exception as error:

        logger.exception(
            "Query processing failed."
        )

        return jsonify(
            {
                "error":
                    str(error)
            }
        ), 500


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    logger.info(
        "Starting RAG Flask application..."
    )

    app.run(
        host=APP_HOST,
        port=APP_PORT,
        debug=DEBUG
    )
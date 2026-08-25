document.addEventListener("DOMContentLoaded", () => {

    /* ==========================================
       API BASE
    ========================================== */

    const API_BASE = "/api";


    /* ==========================================
       DOM ELEMENTS
    ========================================== */

    const fileInput =
        document.getElementById("fileInput");

    const uploadArea =
        document.getElementById("uploadArea");

    const selectedFilesContainer =
        document.getElementById("selectedFiles");

    const uploadButton =
        document.getElementById("uploadButton");

    const uploadResult =
        document.getElementById("uploadResult");

    const documentList =
        document.getElementById("documentList");

    const resetButton =
        document.getElementById("resetButton");

    const questionInput =
        document.getElementById("questionInput");

    const askButton =
        document.getElementById("askButton");

    const queryResult =
        document.getElementById("queryResult");

    const modelSelect =
        document.getElementById("modelSelect");

    const refreshModelsButton =
        document.getElementById("refreshModelsButton");

    const topKSelect =
        document.getElementById("topKSelect");

    const healthStatus =
        document.getElementById("healthStatus");

    const healthText =
        document.getElementById("healthText");


    /* ==========================================
       UPLOAD MODAL
    ========================================== */

    const uploadModal =
        document.getElementById("uploadModal");

    const processingFiles =
        document.getElementById("processingFiles");

    const progressBar =
        document.getElementById("progressBar");

    const progressPercentage =
        document.getElementById("progressPercentage");

    const progressText =
        document.getElementById("progressText");

    const processingMessage =
        document.getElementById("processingMessage");


    /* ==========================================
       DELETE MODAL
    ========================================== */

    const deleteModal =
        document.getElementById("deleteModal");

    const deleteFileName =
        document.getElementById("deleteFileName");

    const cancelDeleteButton =
        document.getElementById("cancelDeleteButton");

    const confirmDeleteButton =
        document.getElementById("confirmDeleteButton");


    /* ==========================================
       TOAST
    ========================================== */

    const toast =
        document.getElementById("toast");

    const toastIcon =
        document.getElementById("toastIcon");

    const toastMessage =
        document.getElementById("toastMessage");


    /* ==========================================
       VARIABLES
    ========================================== */

    let selectedFiles = [];

    let documentToDelete = null;


    /* ==========================================
       SAFE API RESPONSE PARSER
    ========================================== */

    async function parseApiResponse(
        response
    ) {

        const contentType =

            response.headers.get(
                "content-type"
            )

            || "";


        if (

            contentType.includes(
                "application/json"
            )

        ) {

            return await response.json();

        }


        const text =
            await response.text();


        throw new Error(

            `Unexpected server response: ${
                text.substring(
                    0,
                    200
                )
            }`

        );

    }


    /* ==========================================
       FILE INPUT
    ========================================== */

    fileInput.addEventListener(
        "change",
        () => {

            addSelectedFiles(

                Array.from(
                    fileInput.files
                )

            );

        }
    );


    /* ==========================================
       DRAG AND DROP
    ========================================== */

    [
        "dragenter",
        "dragover"
    ].forEach(
        eventName => {

            uploadArea.addEventListener(

                eventName,

                event => {

                    event.preventDefault();

                    uploadArea.classList.add(
                        "dragover"
                    );

                }

            );

        }
    );


    [
        "dragleave",
        "drop"
    ].forEach(
        eventName => {

            uploadArea.addEventListener(

                eventName,

                event => {

                    event.preventDefault();

                    uploadArea.classList.remove(
                        "dragover"
                    );

                }

            );

        }
    );


    uploadArea.addEventListener(
        "drop",
        event => {

            const files =

                Array.from(
                    event.dataTransfer.files
                );


            addSelectedFiles(
                files
            );

        }
    );


    /* ==========================================
       ADD SELECTED FILES
    ========================================== */

    function addSelectedFiles(
        files
    ) {

        files.forEach(
            file => {

                const exists =

                    selectedFiles.some(
                        item =>

                            item.name ===
                            file.name
                    );


                if (!exists) {

                    selectedFiles.push(
                        file
                    );

                }

            }
        );


        renderSelectedFiles();

    }


    /* ==========================================
       RENDER SELECTED FILES
    ========================================== */

    function renderSelectedFiles() {

        selectedFilesContainer.innerHTML =
            "";


        if (

            selectedFiles.length === 0

        ) {

            uploadButton.disabled =
                true;

            return;

        }


        uploadButton.disabled =
            false;


        selectedFiles.forEach(
            file => {

                const fileElement =

                    document.createElement(
                        "div"
                    );


                fileElement.className =
                    "selected-file";


                fileElement.innerHTML = `

                    <span>
                        📄
                    </span>

                    <span>
                        ${escapeHtml(
                            file.name
                        )}
                    </span>

                `;


                selectedFilesContainer.appendChild(
                    fileElement
                );

            }
        );

    }


    /* ==========================================
       UPLOAD DOCUMENTS
    ========================================== */

    uploadButton.addEventListener(
        "click",
        async () => {

            if (

                selectedFiles.length === 0

            ) {

                showToast(
                    "Please select at least one file.",
                    "error"
                );

                return;

            }


            const filesToUpload =
                [...selectedFiles];


            showUploadModal();


            uploadButton.disabled =
                true;


            try {

                setStepActive(
                    "step1"
                );


                updateProgress(
                    15,
                    "Uploading documents..."
                );


                const formData =
                    new FormData();


                filesToUpload.forEach(
                    file => {

                        formData.append(
                            "files",
                            file
                        );

                    }
                );


                const response =

                    await fetch(

                        `${API_BASE}/documents/upload`,

                        {

                            method:
                            "POST",

                            body:
                            formData

                        }

                    );


                const data =

                    await parseApiResponse(
                        response
                    );


                if (!response.ok) {

                    throw new Error(

                        data.message ||

                        data.error ||

                        "Upload failed"

                    );

                }


                const failedFiles =

                    data.results

                        ? data.results.filter(

                            item =>

                                item.status ===
                                "error"

                        )

                        : [];


                if (

                    failedFiles.length > 0

                ) {

                    throw new Error(

                        failedFiles

                            .map(
                                item =>
                                    `${item.filename}: ${item.message}`
                            )

                            .join(
                                ", "
                            )

                    );

                }


                setStepCompleted(
                    "step1"
                );


                setStepActive(
                    "step2"
                );


                updateProgress(
                    40,
                    "Reading document content..."
                );


                await delay(
                    400
                );


                setStepCompleted(
                    "step2"
                );


                setStepActive(
                    "step3"
                );


                updateProgress(
                    70,
                    "Creating searchable chunks..."
                );


                await delay(
                    400
                );


                setStepCompleted(
                    "step3"
                );


                setStepActive(
                    "step4"
                );


                updateProgress(
                    90,
                    "Creating AI embeddings..."
                );


                await delay(
                    400
                );


                setStepCompleted(
                    "step4"
                );


                updateProgress(
                    100,
                    "Processing completed!"
                );


                uploadModal.classList.add(
                    "success"
                );


                showToast(

                    data.message ||

                    "Documents uploaded successfully!",

                    "success"

                );


                await delay(
                    800
                );


                hideUploadModal();


                selectedFiles = [];


                fileInput.value = "";


                renderSelectedFiles();


                await loadDocuments();

            }

            catch (error) {

                console.error(
                    "Upload error:",
                    error
                );


                hideUploadModal();


                showToast(

                    error.message ||

                    "Upload failed.",

                    "error"

                );

            }

            finally {

                uploadButton.disabled =

                    selectedFiles.length === 0;

            }

        }
    );


    /* ==========================================
       SHOW UPLOAD MODAL
    ========================================== */

    function showUploadModal() {

        uploadModal.classList.add(
            "show"
        );


        uploadModal.classList.remove(
            "success"
        );


        processingFiles.innerHTML =
            "";


        selectedFiles.forEach(
            file => {

                const fileElement =

                    document.createElement(
                        "div"
                    );


                fileElement.className =
                    "processing-file";


                fileElement.innerHTML = `

                    <span class="processing-file-icon">
                        📄
                    </span>

                    <span class="processing-file-name">
                        ${escapeHtml(
                            file.name
                        )}
                    </span>

                `;


                processingFiles.appendChild(
                    fileElement
                );

            }
        );


        resetSteps();


        updateProgress(
            0,
            "Preparing upload..."
        );

    }


    /* ==========================================
       RESET STEPS
    ========================================== */

    function resetSteps() {

        for (

            let i = 1;

            i <= 4;

            i++

        ) {

            const step =

                document.getElementById(
                    `step${i}`
                );


            step.classList.remove(

                "active",

                "completed"

            );


            const status =

                step.querySelector(
                    ".step-status"
                );


            status.innerHTML = `

                <span class="step-number">
                    ${i}
                </span>

            `;

        }

    }


    /* ==========================================
       STEP ACTIVE
    ========================================== */

    function setStepActive(
        id
    ) {

        const step =

            document.getElementById(
                id
            );


        step.classList.add(
            "active"
        );


        const status =

            step.querySelector(
                ".step-status"
            );


        status.innerHTML = `

            <span class="step-loader">
            </span>

        `;

    }


    /* ==========================================
       STEP COMPLETED
    ========================================== */

    function setStepCompleted(
        id
    ) {

        const step =

            document.getElementById(
                id
            );


        step.classList.remove(
            "active"
        );


        step.classList.add(
            "completed"
        );


        const status =

            step.querySelector(
                ".step-status"
            );


        status.innerHTML = `

            <span>
                ✓
            </span>

        `;

    }


    /* ==========================================
       UPDATE PROGRESS
    ========================================== */

    function updateProgress(
        percentage,
        message
    ) {

        progressBar.style.width =
            `${percentage}%`;


        progressPercentage.textContent =
            `${percentage}%`;


        progressText.textContent =
            message;


        processingMessage.textContent =
            message;

    }


    /* ==========================================
       HIDE UPLOAD MODAL
    ========================================== */

    function hideUploadModal() {

        uploadModal.classList.remove(
            "show"
        );

    }


    /* ==========================================
       LOAD DOCUMENTS
    ========================================== */

    async function loadDocuments() {

        try {

            const response =

                await fetch(
                    `${API_BASE}/documents`
                );


            const data =

                await parseApiResponse(
                    response
                );


            if (!response.ok) {

                throw new Error(

                    data.message ||

                    "Unable to load documents"

                );

            }


            const documents =

                Array.isArray(data)

                    ? data

                    : data.documents || [];


            documentList.innerHTML =
                "";


            if (

                documents.length === 0

            ) {

                showEmptyDocumentState();

                return;

            }


            documents.forEach(
                document => {

                    const documentId =

                        typeof document ===
                        "object"

                            ? document.document_id

                            : null;


                    const fileName =

                        typeof document ===
                        "string"

                            ? document

                            : (

                                document.filename ||

                                document.name ||

                                document.id ||

                                "Unknown Document"

                            );


                    createDocumentItem(

                        documentId,

                        fileName

                    );

                }
            );

        }

        catch (error) {

            console.error(
                "Load documents error:",
                error
            );


            showEmptyDocumentState();

        }

    }


    /* ==========================================
       EMPTY DOCUMENT STATE
    ========================================== */

    function showEmptyDocumentState() {

        documentList.innerHTML = `

            <div class="empty-state">

                <div class="empty-icon">
                    📂
                </div>

                <h3>
                    No Documents
                </h3>

                <p>
                    Upload documents to start asking questions.
                </p>

            </div>

        `;

    }


    /* ==========================================
       CREATE DOCUMENT ITEM
    ========================================== */

    function createDocumentItem(
        documentId,
        fileName
    ) {

        const documentItem =

            document.createElement(
                "div"
            );


        documentItem.className =
            "document-item";


        documentItem.dataset.documentId =
            documentId || "";


        documentItem.dataset.fileName =
            fileName;


        documentItem.innerHTML = `

            <div class="document-icon">
                📄
            </div>

            <div class="document-info">

                <strong>
                    ${escapeHtml(
                        fileName
                    )}
                </strong>

                <span>
                    Ready for AI search
                </span>

            </div>

            <button
                class="delete-button"
                title="Delete document"
            >
                🗑️
            </button>

        `;


        const deleteButton =

            documentItem.querySelector(
                ".delete-button"
            );


        deleteButton.addEventListener(
            "click",
            () => {

                if (!documentId) {

                    showToast(

                        "Unable to identify this document.",

                        "error"

                    );

                    return;

                }


                openDeleteModal(

                    documentItem,

                    documentId,

                    fileName

                );

            }
        );


        documentList.appendChild(
            documentItem
        );

    }


    /* ==========================================
       DELETE MODAL
    ========================================== */

    function openDeleteModal(
        documentElement,
        documentId,
        fileName
    ) {

        documentToDelete = {

            element:
            documentElement,

            documentId:
            documentId,

            fileName:
            fileName

        };


        deleteFileName.textContent =
            fileName;


        deleteModal.classList.add(
            "active"
        );

    }


    cancelDeleteButton.addEventListener(
        "click",
        closeDeleteModal
    );


    function closeDeleteModal() {

        deleteModal.classList.remove(
            "active"
        );


        documentToDelete =
            null;

    }


    confirmDeleteButton.addEventListener(
        "click",
        async () => {

            if (!documentToDelete) {
                return;
            }


            try {

                confirmDeleteButton.disabled =
                    true;


                const response =

                    await fetch(

                        `${API_BASE}/documents/${

                            encodeURIComponent(

                                documentToDelete.documentId

                            )

                        }`,

                        {

                            method:
                            "DELETE"

                        }

                    );


                const data =

                    await parseApiResponse(
                        response
                    );


                if (!response.ok) {

                    throw new Error(

                        data.message ||

                        "Unable to delete document"

                    );

                }


                documentToDelete.element.classList.add(
                    "deleting"
                );


                await delay(
                    250
                );


                closeDeleteModal();


                await loadDocuments();


                showToast(

                    data.message ||

                    "Document deleted successfully.",

                    "success"

                );

            }

            catch (error) {

                console.error(
                    "Delete error:",
                    error
                );


                showToast(

                    error.message ||

                    "Unable to delete document.",

                    "error"

                );

            }

            finally {

                confirmDeleteButton.disabled =
                    false;

            }

        }
    );


    /* ==========================================
       RESET ALL DOCUMENTS
    ========================================== */

    resetButton.addEventListener(
        "click",
        async () => {

            try {

                const response =

                    await fetch(

                        `${API_BASE}/documents/reset`,

                        {

                            method:
                            "DELETE"

                        }

                    );


                const data =

                    await parseApiResponse(
                        response
                    );


                if (!response.ok) {

                    throw new Error(

                        data.message ||

                        "Unable to reset documents"

                    );

                }


                await loadDocuments();


                showToast(

                    data.message ||

                    "All documents have been removed.",

                    "success"

                );

            }

            catch (error) {

                console.error(
                    "Reset error:",
                    error
                );


                showToast(

                    error.message ||

                    "Unable to reset documents.",

                    "error"

                );

            }

        }
    );


    /* ==========================================
       ASK AI - STREAMING
    ========================================== */

    askButton.addEventListener(
        "click",
        async () => {

            const question =

                questionInput.value.trim();


            if (!question) {

                showToast(

                    "Please enter a question.",

                    "error"

                );

                return;

            }


            askButton.disabled =
                true;


            showLoadingAnswer();


            try {

                const response =

                    await fetch(

                        `${API_BASE}/query/stream`,

                        {

                            method:
                            "POST",

                            headers: {

                                "Content-Type":
                                "application/json"

                            },

                            body:

                            JSON.stringify({

                                query:
                                question,

                                model:
                                modelSelect.value,

                                top_k:

                                Number(
                                    topKSelect.value
                                )

                            })

                        }

                    );


                if (!response.ok) {

                    const data =

                        await parseApiResponse(
                            response
                        );


                    throw new Error(

                        data.message ||

                        "Unable to get AI answer"

                    );

                }


                const reader =

                    response.body.getReader();


                const decoder =
                    new TextDecoder();


                let buffer = "";

                let answer = "";

                let sources = [];

                let usedModel =
                    modelSelect.value;


                let generationTime =
                    null;

                let retrievalTime =
                    null;

                let totalTime =
                    null;


                // ----------------------------------
                // Prepare Streaming UI
                // ----------------------------------

                showStreamingAnswer(
                    question
                );


                while (true) {

                    const {

                        value,

                        done

                    } =

                    await reader.read();


                    if (done) {
                        break;
                    }


                    buffer +=

                        decoder.decode(

                            value,

                            {

                                stream:
                                true

                            }

                        );


                    const lines =

                        buffer.split(
                            "\n"
                        );


                    buffer =
                        lines.pop();


                    for (
                        const line
                        of lines
                    ) {

                        if (!line.trim()) {
                            continue;
                        }


                        let event;


                        try {

                            event =
                                JSON.parse(
                                    line
                                );

                        }

                        catch (error) {

                            console.error(

                                "Invalid streaming JSON:",

                                line

                            );

                            continue;

                        }


                        // --------------------------
                        // START EVENT
                        // --------------------------

                        if (

                            event.type ===
                            "start"

                        ) {

                            sources =
                                event.sources || [];


                            retrievalTime =
                                event.retrieval_time;


                            updateStreamingStatus(
                                "Generating answer..."
                            );

                        }


                        // --------------------------
                        // TOKEN EVENT
                        // --------------------------

                        if (

                            event.type ===
                            "token"

                        ) {

                            answer +=

                                event.content ||
                                "";


                            appendStreamingToken(

                                event.content ||
                                ""

                            );

                        }


                        // --------------------------
                        // DONE EVENT
                        // --------------------------

                        if (

                            event.type ===
                            "done"

                        ) {

                            usedModel =
                                event.model ||
                                usedModel;


                            generationTime =
                                event.generation_time;


                            retrievalTime =
                                event.retrieval_time;


                            totalTime =
                                event.total_time;

                        }


                        // --------------------------
                        // ERROR EVENT
                        // --------------------------

                        if (

                            event.type ===
                            "error"

                        ) {

                            throw new Error(

                                event.message ||

                                "Streaming failed."

                            );

                        }

                    }

                }


                finishStreamingAnswer(

                    question,

                    answer,

                    sources,

                    usedModel,

                    generationTime,

                    retrievalTime,

                    totalTime

                );

            }

            catch (error) {

                console.error(
                    "Streaming query error:",
                    error
                );


                queryResult.innerHTML = `

                    <div class="error-message">

                        <span>
                            ⚠️
                        </span>

                        <div>

                            <strong>
                                Error
                            </strong>

                            <p>

                                ${escapeHtml(
                                    error.message
                                )}

                            </p>

                        </div>

                    </div>

                `;

            }

            finally {

                askButton.disabled =
                    false;

            }

        }
    );


    /* ==========================================
       SHOW LOADING ANSWER
    ========================================== */

    function showLoadingAnswer() {

        queryResult.innerHTML = `

            <div class="ai-loading">

                <div class="ai-loading-icon">
                    🤖
                </div>

                <div>

                    <strong>
                        AI is thinking...
                    </strong>

                    <p>
                        Searching your documents...
                    </p>

                </div>

            </div>

        `;

    }


    /* ==========================================
       SHOW STREAMING ANSWER
    ========================================== */

    function showStreamingAnswer(
        question
    ) {

        const model =

            modelSelect.value ||

            "AI Model";


        const topK =
            topKSelect.value;


        queryResult.innerHTML = `

            <div class="question-message">

                <div class="message-label">
                    YOUR QUESTION
                </div>

                <div class="question-text">

                    ${escapeHtml(
                        question
                    )}

                </div>

            </div>


            <div class="ai-answer-card">

                <div class="answer-header">

                    <div class="answer-avatar">
                        🤖
                    </div>

                    <div class="answer-title-section">

                        <h3>
                            AI Answer
                        </h3>

                        <span
                            id="streamingStatus"
                        >

                            Generating answer...

                        </span>

                    </div>

                </div>


                <div class="model-metrics">

                    <div class="metric-item">

                        <span class="metric-label">
                            Model
                        </span>

                        <strong
                            id="streamingModel"
                        >

                            ${escapeHtml(
                                model
                            )}

                        </strong>

                    </div>


                    <div class="metric-item">

                        <span class="metric-label">
                            Search Results
                        </span>

                        <strong>

                            Top ${escapeHtml(
                                topK
                            )}

                        </strong>

                    </div>

                </div>


                <div
                    id="streamingAnswer"
                    class="answer-content"
                >
                </div>

            </div>

        `;

    }


    /* ==========================================
       UPDATE STREAMING STATUS
    ========================================== */

    function updateStreamingStatus(
        status
    ) {

        const statusElement =

            document.getElementById(
                "streamingStatus"
            );


        if (statusElement) {

            statusElement.textContent =
                status;

        }

    }


    /* ==========================================
       APPEND STREAMING TOKEN
    ========================================== */

    function appendStreamingToken(
        token
    ) {

        const answerElement =

            document.getElementById(
                "streamingAnswer"
            );


        if (!answerElement) {
            return;
        }


        answerElement.textContent +=
            token;


        answerElement.scrollIntoView({

            behavior:
            "smooth",

            block:
            "nearest"

        });

    }


    /* ==========================================
       FINISH STREAMING ANSWER
    ========================================== */

    function finishStreamingAnswer(

        question,

        answer,

        sources,

        model,

        generationTime,

        retrievalTime,

        totalTime

    ) {

        const statusElement =

            document.getElementById(
                "streamingStatus"
            );


        if (statusElement) {

            statusElement.textContent =
                "Answer completed";

        }


        const modelElement =

            document.getElementById(
                "streamingModel"
            );


        if (modelElement && model) {

            modelElement.textContent =
                model;

        }


        const answerElement =

            document.getElementById(
                "streamingAnswer"
            );


        if (

            answerElement
            &&
            !answerElement.textContent.trim()

        ) {

            answerElement.textContent =

                answer ||

                "No answer was generated.";

        }


        addSourcesSection(
            sources
        );


        if (

            generationTime !== null
            ||
            retrievalTime !== null
            ||
            totalTime !== null

        ) {

            addPerformanceMetrics(

                generationTime,

                retrievalTime,

                totalTime

            );

        }

    }


    /* ==========================================
       ADD SOURCES SECTION
    ========================================== */

    function addSourcesSection(
        sources
    ) {

        let sourcesHtml =
            "";


        if (

            !sources
            ||
            sources.length === 0

        ) {

            sourcesHtml = `

                <div class="source-card">

                    <div class="source-file-icon">
                        📄
                    </div>

                    <div class="source-info">

                        <strong>
                            Document Source
                        </strong>

                        <span>
                            Relevant document content
                        </span>

                    </div>

                </div>

            `;

        }

        else {

            sources.forEach(
                source => {

                    const sourceName =

                        source.filename ||

                        source.source ||

                        source.name ||

                        "Document Source";


                    const sourceText =

                        source.chunk_id !==
                        undefined

                            ? `Chunk ${source.chunk_id}`

                            : "Relevant document content";


                    sourcesHtml += `

                        <div class="source-card">

                            <div class="source-file-icon">
                                📄
                            </div>

                            <div class="source-info">

                                <strong>

                                    ${escapeHtml(
                                        sourceName
                                    )}

                                </strong>

                                <span>

                                    ${escapeHtml(
                                        sourceText
                                    )}

                                </span>

                            </div>

                        </div>

                    `;

                }
            );

        }


        queryResult.innerHTML += `

            <div class="sources-section">

                <h3>

                    Sources

                    <span class="source-count">

                        ${sources.length || 1}

                    </span>

                </h3>


                <div class="sources-grid">

                    ${sourcesHtml}

                </div>

            </div>

        `;

    }


    /* ==========================================
       ADD PERFORMANCE METRICS
    ========================================== */

    function addPerformanceMetrics(

        generationTime,

        retrievalTime,

        totalTime

    ) {

        queryResult.innerHTML += `

            <div class="performance-section">

                <h3>
                    Performance
                </h3>

                <div class="performance-grid">

                    <div class="metric-item">

                        <span class="metric-label">
                            Retrieval
                        </span>

                        <strong>

                            ${

                                retrievalTime !== null

                                    ? `${retrievalTime}s`

                                    : "N/A"

                            }

                        </strong>

                    </div>


                    <div class="metric-item">

                        <span class="metric-label">
                            Generation
                        </span>

                        <strong>

                            ${

                                generationTime !== null

                                    ? `${generationTime}s`

                                    : "N/A"

                            }

                        </strong>

                    </div>


                    <div class="metric-item">

                        <span class="metric-label">
                            Total
                        </span>

                        <strong>

                            ${

                                totalTime !== null

                                    ? `${totalTime}s`

                                    : "N/A"

                            }

                        </strong>

                    </div>

                </div>

            </div>

        `;

    }


    /* ==========================================
       LOAD MODELS
    ========================================== */

    async function loadModels() {

        try {

            modelSelect.innerHTML = `

                <option value="">
                    Loading models...
                </option>

            `;


            const response =

                await fetch(
                    `${API_BASE}/models`
                );


            const data =

                await parseApiResponse(
                    response
                );


            if (!response.ok) {

                throw new Error(

                    data.message ||

                    "Unable to load models"

                );

            }


            const models =

                Array.isArray(data)

                    ? data

                    : data.models || [];


            modelSelect.innerHTML =
                "";


            if (

                models.length === 0

            ) {

                modelSelect.innerHTML = `

                    <option value="">
                        No models available
                    </option>

                `;

                return;

            }


            models.forEach(
                model => {

                    const modelName =

                        typeof model ===
                        "string"

                            ? model

                            : (

                                model.name ||

                                model.id

                            );


                    if (!modelName) {
                        return;
                    }


                    const option =

                        document.createElement(
                            "option"
                        );


                    option.value =
                        modelName;


                    option.textContent =
                        modelName;


                    modelSelect.appendChild(
                        option
                    );

                }
            );

        }

        catch (error) {

            console.error(
                "Load models error:",
                error
            );


            modelSelect.innerHTML = `

                <option value="">
                    Unable to load models
                </option>

            `;

        }

    }


    refreshModelsButton.addEventListener(
        "click",
        async () => {

            await loadModels();


            showToast(

                "Models refreshed.",

                "success"

            );

        }
    );


    /* ==========================================
       HEALTH CHECK
    ========================================== */

    async function checkHealth() {

        try {

            const response =

                await fetch(
                    `${API_BASE}/health`
                );


            const data =

                await parseApiResponse(
                    response
                );


            if (!response.ok) {

                throw new Error(

                    data.message ||

                    "Health check failed"

                );

            }


            healthStatus.className =

                "health-status healthy";


            healthText.textContent =
                "System Online";

        }

        catch (error) {

            console.error(
                "Health check error:",
                error
            );


            healthStatus.className =

                "health-status unhealthy";


            healthText.textContent =
                "System Offline";

        }

    }


    /* ==========================================
       TOAST
    ========================================== */

    function showToast(
        message,
        type = "success"
    ) {

        toast.className =

            `toast ${type}`;


        toastMessage.textContent =
            message;


        toastIcon.textContent =

            type === "success"

                ? "✓"

                : "!";


        requestAnimationFrame(
            () => {

                toast.classList.add(
                    "show"
                );

            }
        );


        setTimeout(
            () => {

                toast.classList.remove(
                    "show"
                );

            },

            3500
        );

    }


    /* ==========================================
       HELPERS
    ========================================== */

    function delay(
        milliseconds
    ) {

        return new Promise(
            resolve => {

                setTimeout(

                    resolve,

                    milliseconds

                );

            }
        );

    }


    function escapeHtml(
        text
    ) {

        const div =

            document.createElement(
                "div"
            );


        div.textContent =

            text === null ||

            text === undefined

                ? ""

                : String(
                    text
                );


        return div.innerHTML;

    }


    /* ==========================================
       INITIALIZE
    ========================================== */

    loadModels();

    checkHealth();

    loadDocuments();

});
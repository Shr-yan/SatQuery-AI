const queryInput =
    document.getElementById(
        "queryInput"
    );

const analyzeButton =
    document.getElementById(
        "analyzeButton"
    );

const statusBox =
    document.getElementById(
        "status"
    );

const results =
    document.getElementById(
        "results"
    );


const vegetationMetrics =
    document.getElementById(
        "vegetationMetrics"
    );

const indexMetrics =
    document.getElementById(
        "indexMetrics"
    );

const imageryMetrics =
    document.getElementById(
        "imageryMetrics"
    );

const changeMetrics =
    document.getElementById(
        "changeMetrics"
    );


const vegetationDetails =
    document.getElementById(
        "vegetationDetails"
    );

const indexDetails =
    document.getElementById(
        "indexDetails"
    );

const imageryDetails =
    document.getElementById(
        "imageryDetails"
    );


const imagesGrid =
    document.getElementById(
        "imagesGrid"
    );

const rgbImageCard =
    document.getElementById(
        "rgbImageCard"
    );

const analysisImageCard =
    document.getElementById(
        "analysisImageCard"
    );

const changeImagesGrid =
    document.getElementById(
        "changeImagesGrid"
    );


const normalDetailsGrid =
    document.getElementById(
        "normalDetailsGrid"
    );

const changeDetailsGrid =
    document.getElementById(
        "changeDetailsGrid"
    );

const trendMetrics =
    document.getElementById(
        "trendMetrics"
    );

const trendImagesGrid =
    document.getElementById(
        "trendImagesGrid"
    );

const trendDetailsGrid =
    document.getElementById(
        "trendDetailsGrid"
    );

const aiChat =
    document.getElementById(
        "aiChat"
    );

const chatMessages =
    document.getElementById(
        "chatMessages"
    );

const chatInput =
    document.getElementById(
        "chatInput"
    );

const chatSendButton =
    document.getElementById(
        "chatSendButton"
    );

const chatStatus =
    document.getElementById(
        "chatStatus"
    );

const clearChatButton =
    document.getElementById(
        "clearChatButton"
    );


const themeToggle =
    document.getElementById(
        "themeToggle"
    );

const themeIcon =
    document.getElementById(
        "themeIcon"
    );

const themeLabel =
    document.getElementById(
        "themeLabel"
    );

const evaluationLink =
    document.getElementById(
        "evaluationLink"
    );


const searchEarthModeButton =
    document.getElementById(
        "searchEarthModeButton"
    );

const analyzeImageryModeButton =
    document.getElementById(
        "analyzeImageryModeButton"
    );

const searchEarthPanel =
    document.getElementById(
        "searchEarthPanel"
    );

const analyzeImageryPanel =
    document.getElementById(
        "analyzeImageryPanel"
    );

const uploadDropzone =
    document.getElementById(
        "uploadDropzone"
    );

const imageryFileInput =
    document.getElementById(
        "imageryFileInput"
    );

const chooseImageryButton =
    document.getElementById(
        "chooseImageryButton"
    );

const uploadImageryButton =
    document.getElementById(
        "uploadImageryButton"
    );

const selectedImageryName =
    document.getElementById(
        "selectedImageryName"
    );

const selectedImagerySize =
    document.getElementById(
        "selectedImagerySize"
    );

const uploadStatus =
    document.getElementById(
        "uploadStatus"
    );

const uploadedImageResult =
    document.getElementById(
        "uploadedImageResult"
    );

const uploadedPreviewImage =
    document.getElementById(
        "uploadedPreviewImage"
    );

const uploadWarning =
    document.getElementById(
        "uploadWarning"
    );

const uploadedChatMessages =
    document.getElementById(
        "uploadedChatMessages"
    );

const uploadedChatInput =
    document.getElementById(
        "uploadedChatInput"
    );

const uploadedChatSendButton =
    document.getElementById(
        "uploadedChatSendButton"
    );

const uploadedChatStatus =
    document.getElementById(
        "uploadedChatStatus"
    );

const clearUploadedChatButton =
    document.getElementById(
        "clearUploadedChatButton"
    );

const uploadedExecutionTrace =
    document.getElementById(
        "uploadedExecutionTrace"
    );

const specialistEvidenceCard =
    document.getElementById(
        "specialistEvidenceCard"
    );

const downloadSearchReportButton =
    document.getElementById("downloadSearchReportButton");
const downloadSearchJsonButton =
    document.getElementById("downloadSearchJsonButton");
const searchReportStatus =
    document.getElementById("searchReportStatus");

const downloadUploadedReportButton =
    document.getElementById("downloadUploadedReportButton");
const downloadUploadedJsonButton =
    document.getElementById("downloadUploadedJsonButton");
const uploadedReportStatus =
    document.getElementById("uploadedReportStatus");

const downloadPairReportButton =
    document.getElementById("downloadPairReportButton");
const downloadPairJsonButton =
    document.getElementById("downloadPairJsonButton");
const pairReportStatus =
    document.getElementById("pairReportStatus");

const downloadCrossModalReportButton =
    document.getElementById("downloadCrossModalReportButton");
const downloadCrossModalJsonButton =
    document.getElementById("downloadCrossModalJsonButton");
const crossModalReportStatus =
    document.getElementById("crossModalReportStatus");


let lightModeEnabled =
    false;


let selectedImageryFile =
    null;

let currentWorkspaceMode =
    "search";

let currentAnalysisResult =
    null;

let conversationHistory =
    [];

let currentUploadId =
    null;

let uploadedConversationHistory =
    [];

let currentUploadedEvidence =
    null;

let currentPairEvidence =
    null;

let currentCrossModalEvidence =
    null;


function applyTheme(
    useLightMode
) {

    lightModeEnabled =
        useLightMode;

    document.body.classList.toggle(
        "light-mode",
        useLightMode
    );

    themeToggle.setAttribute(
        "aria-pressed",
        useLightMode
            ? "true"
            : "false"
    );

    themeToggle.setAttribute(
        "aria-label",
        useLightMode
            ? "Switch to dark mode"
            : "Switch to light mode"
    );

    themeIcon.textContent =
        useLightMode
            ? "🌙"
            : "☀️";

    themeLabel.textContent =
        useLightMode
            ? "Dark mode"
            : "Light mode";

}


/*
Direct visits still start in dark mode. When SatQuery navigates between the
main workspace and Evaluation Center, a short-lived URL parameter carries the
currently selected theme so the two pages do not visually jump.
*/
const initialTheme = new URLSearchParams(
    window.location.search
).get(
    "theme"
);

applyTheme(
    initialTheme === "light"
);


function setWorkspaceMode(
    mode
) {

    const useSearch =
        mode === "search";

    currentWorkspaceMode =
        useSearch
            ? "search"
            : "imagery";

    searchEarthPanel.classList.toggle(
        "hidden",
        !useSearch
    );

    analyzeImageryPanel.classList.toggle(
        "hidden",
        useSearch
    );

    searchEarthModeButton.classList.toggle(
        "active",
        useSearch
    );

    analyzeImageryModeButton.classList.toggle(
        "active",
        !useSearch
    );

    searchEarthModeButton.setAttribute(
        "aria-pressed",
        useSearch ? "true" : "false"
    );

    analyzeImageryModeButton.setAttribute(
        "aria-pressed",
        useSearch ? "false" : "true"
    );

    if (useSearch) {

        if (currentAnalysisResult) {
            results.style.display =
                "block";
        }

    }

    else {

        results.style.display =
            "none";

    }

}


function readableFileSize(
    bytes
) {

    if (!Number.isFinite(bytes)) {
        return "-";
    }

    if (bytes < 1024) {
        return bytes + " B";
    }

    const megabytes =
        bytes / (1024 * 1024);

    if (megabytes >= 1) {
        return megabytes.toFixed(2) + " MB";
    }

    return (bytes / 1024).toFixed(1) + " KB";
}


function setUploadStatus(
    message,
    isError = false
) {

    uploadStatus.textContent =
        message || "";

    uploadStatus.classList.toggle(
        "upload-status-error",
        isError
    );

}


function chooseUploadedImageryFile(
    file
) {

    selectedImageryFile =
        null;

    currentUploadId =
        null;

    uploadedConversationHistory =
        [];

    currentUploadedEvidence =
        null;

    downloadUploadedReportButton.disabled =
        true;
    downloadUploadedJsonButton.disabled =
        true;
    uploadedReportStatus.textContent =
        "";

    uploadedImageResult.classList.add(
        "hidden"
    );

    uploadImageryButton.disabled =
        true;

    if (!file) {

        selectedImageryName.textContent =
            "No file selected";

        selectedImagerySize.textContent =
            "-";

        return;

    }

    const allowedExtensions = [
        ".tif",
        ".tiff",
        ".png",
        ".jpg",
        ".jpeg"
    ];

    const lowerName =
        file.name.toLowerCase();

    const validExtension =
        allowedExtensions.some(
            extension =>
                lowerName.endsWith(
                    extension
                )
        );

    if (!validExtension) {

        setUploadStatus(
            "Unsupported file type. Use GeoTIFF/TIFF, PNG, JPG or JPEG.",
            true
        );

        selectedImageryName.textContent =
            file.name;

        selectedImagerySize.textContent =
            readableFileSize(file.size);

        return;

    }

    const maxBytes =
        30 * 1024 * 1024;

    if (file.size > maxBytes) {

        setUploadStatus(
            "This file is larger than the 30 MB upload limit.",
            true
        );

        selectedImageryName.textContent =
            file.name;

        selectedImagerySize.textContent =
            readableFileSize(file.size);

        return;

    }

    selectedImageryFile =
        file;

    selectedImageryName.textContent =
        file.name;

    selectedImagerySize.textContent =
        readableFileSize(file.size);

    uploadImageryButton.disabled =
        false;

    setUploadStatus(
        "Ready to upload and validate."
    );

}


function fillUploadedMetadata(
    data
) {

    const metadata =
        data.input || {};

    setText(
        "uploadedFormat",
        metadata.format || "-"
    );

    setText(
        "uploadedDimensions",
        metadata.width && metadata.height
            ? metadata.width + " × " + metadata.height + " px"
            : "-"
    );

    setText(
        "uploadedBands",
        metadata.bands ?? "-"
    );

    setText(
        "uploadedDtype",
        metadata.dtype || "-"
    );

    setText(
        "uploadedCrs",
        metadata.crs || "Not available"
    );

    setText(
        "uploadedResolution",
        Array.isArray(metadata.resolution)
            ? metadata.resolution
                .map(value => Number(value).toFixed(3))
                .join(" × ")
            : "Not available"
    );

    setText(
        "uploadedGeoreferenced",
        metadata.georeferenced
            ? "Yes"
            : "No"
    );

    setText(
        "uploadedModalityHint",
        (metadata.modality_hint || "unknown")
            .replaceAll("_", " ")
    );

    setText(
        "uploadedPreviewNote",
        metadata.preview_note || ""
    );

    setText(
        "uploadValidationMessage",
        data.message || "Validation complete."
    );

    const warnings =
        metadata.warnings || [];

    if (warnings.length) {

        uploadWarning.textContent =
            warnings.join(" ");

        uploadWarning.classList.remove(
            "hidden"
        );

    }

    else {

        uploadWarning.textContent =
            "";

        uploadWarning.classList.add(
            "hidden"
        );

    }

    uploadedPreviewImage.src =
        data.preview_url;

    uploadedImageResult.classList.remove(
        "hidden"
    );

}


async function uploadImagery() {

    if (!selectedImageryFile) {

        setUploadStatus(
            "Choose an image first.",
            true
        );

        return;

    }

    uploadImageryButton.disabled =
        true;

    uploadImageryButton.textContent =
        "Validating...";

    setUploadStatus(
        "Uploading image and validating remote-sensing metadata..."
    );

    const formData =
        new FormData();

    formData.append(
        "file",
        selectedImageryFile
    );

    try {

        const response =
            await fetch(
                "/upload-image",
                {
                    method: "POST",
                    body: formData
                }
            );

        const data =
            await response.json();

        if (!response.ok) {

            const message =
                data.detail?.message
                || data.detail
                || "Image upload failed.";

            throw new Error(message);

        }

        fillUploadedMetadata(
            data
        );

        currentUploadId =
            data.upload_id;

        currentUploadedEvidence =
            data;

        downloadUploadedReportButton.disabled =
            false;
        downloadUploadedJsonButton.disabled =
            false;
        uploadedReportStatus.textContent =
            "";

        resetUploadedChat();

        setUploadStatus(
            "Upload complete. Input validation passed."
        );

    }

    catch (error) {

        uploadedImageResult.classList.add(
            "hidden"
        );

        setUploadStatus(
            error.message,
            true
        );

    }

    finally {

        uploadImageryButton.disabled =
            false;

        uploadImageryButton.textContent =
            "Upload & Validate";

    }

}


function resetUploadedChat() {

    uploadedConversationHistory =
        [];

    uploadedChatMessages.innerHTML =
        "";

    addUploadedChatMessage(
        "assistant",
        (
            "Image validated. Ask a question about the uploaded scene, "
            + "or choose Describe Scene to generate a caption."
        )
    );

    uploadedChatStatus.textContent =
        "";

    uploadedExecutionTrace.classList.add(
        "hidden"
    );

    specialistEvidenceCard.classList.add(
        "hidden"
    );

}


function addUploadedChatMessage(
    role,
    content
) {

    const message =
        document.createElement(
            "div"
        );

    message.classList.add(
        "chat-message"
    );

    message.classList.add(
        role === "user"
            ? "user-message"
            : "assistant-message"
    );

    const roleElement =
        document.createElement(
            "div"
        );

    roleElement.className =
        "chat-role";

    roleElement.textContent =
        role === "user"
            ? "You"
            : "SatQuery Vision";

    const textElement =
        document.createElement(
            "div"
        );

    textElement.className =
        "chat-text";

    textElement.textContent =
        content;

    message.appendChild(
        roleElement
    );

    message.appendChild(
        textElement
    );

    uploadedChatMessages.appendChild(
        message
    );

    uploadedChatMessages.scrollTop =
        uploadedChatMessages.scrollHeight;

}


function showUploadedSpecialistEvidence(
    specialist
) {

    if (!specialist) {
        specialistEvidenceCard.classList.add(
            "hidden"
        );
        return;
    }

    if (!specialist.available) {
        setText(
            "specialistModelName",
            "Model not installed"
        );

        setText(
            "specialistDataset",
            "EuroSAT RGB"
        );

        setText(
            "specialistTopCandidate",
            "-"
        );

        setText(
            "specialistTopScore",
            "-"
        );

        setText(
            "specialistOtherCandidates",
            "-"
        );

        setText(
            "specialistTestAccuracy",
            "-"
        );

        setText(
            "specialistNote",
            specialist.message || "Specialist model is unavailable."
        );

        specialistEvidenceCard.classList.remove(
            "hidden"
        );
        return;
    }

    const predictions =
        specialist.predictions || [];

    const top =
        predictions[0] || null;

    const others =
        predictions
            .slice(1)
            .map(
                item =>
                    item.label
                    + " ("
                    + Number(item.model_score_percent).toFixed(1)
                    + "%)"
            )
            .join(", ");

    setText(
        "specialistModelName",
        specialist.model_name || "-"
    );

    setText(
        "specialistDataset",
        specialist.dataset || "-"
    );

    setText(
        "specialistTopCandidate",
        top ? top.label : "-"
    );

    setText(
        "specialistTopScore",
        top
            ? Number(top.model_score_percent).toFixed(2) + "%"
            : "-"
    );

    setText(
        "specialistOtherCandidates",
        others || "-"
    );

    setText(
        "specialistTestAccuracy",
        specialist.test_accuracy_percent !== null
        && specialist.test_accuracy_percent !== undefined
            ? Number(specialist.test_accuracy_percent).toFixed(2) + "%"
            : "-"
    );

    setText(
        "specialistNote",
        (specialist.applicability_note || "")
        + " "
        + (specialist.score_note || "")
    );

    specialistEvidenceCard.classList.remove(
        "hidden"
    );
}


function showUploadedExecutionTrace(
    summary
) {

    if (!summary) {
        return;
    }

    setText(
        "uploadedExecutionTask",
        (summary.task || "-")
            .replaceAll("_", " ")
    );

    setText(
        "uploadedExecutionController",
        summary.controller || "SatQuery Agent Controller"
    );

    setText(
        "uploadedExecutionTools",
        Array.isArray(summary.tools)
            ? summary.tools.join(" → ")
            : "-"
    );

    const parameters =
        summary.key_parameters || {};

    const parameterText =
        Object.entries(parameters)
            .filter(([, value]) =>
                value !== null
                && value !== undefined
            )
            .map(([key, value]) =>
                key.replaceAll("_", " ")
                + ": "
                + value
            )
            .join(" | ");

    setText(
        "uploadedExecutionParameters",
        parameterText || "-"
    );

    setText(
        "uploadedExecutionStatus",
        summary.status || "-"
    );

    uploadedExecutionTrace.classList.remove(
        "hidden"
    );

}


async function sendUploadedVisionQuestion(
    suppliedQuestion = null
) {

    const question =
        (
            suppliedQuestion
            || uploadedChatInput.value
        ).trim();

    if (!currentUploadId) {

        uploadedChatStatus.textContent =
            "Upload and validate an image first.";

        return;

    }

    if (!question) {

        uploadedChatStatus.textContent =
            "Enter a question about the uploaded image.";

        return;

    }

    addUploadedChatMessage(
        "user",
        question
    );

    uploadedChatInput.value =
        "";

    uploadedChatSendButton.disabled =
        true;

    uploadedChatInput.disabled =
        true;

    uploadedChatStatus.textContent =
        "SatQuery Vision is examining the uploaded image...";

    try {

        const response =
            await fetch(
                "/uploaded-vision-chat",
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            {
                                upload_id:
                                    currentUploadId,

                                question:
                                    question,

                                conversation_history:
                                    uploadedConversationHistory
                            }
                        )
                }
            );

        const data =
            await response.json();

        if (!response.ok) {

            const message =
                data.detail?.message
                || data.detail
                || "Uploaded-image vision analysis failed.";

            throw new Error(
                message
            );

        }

        addUploadedChatMessage(
            "assistant",
            data.answer
        );

        uploadedConversationHistory.push(
            {
                role:
                    "user",

                content:
                    question
            }
        );

        uploadedConversationHistory.push(
            {
                role:
                    "assistant",

                content:
                    data.answer
            }
        );

        if (
            uploadedConversationHistory.length
            > 20
        ) {

            uploadedConversationHistory =
                uploadedConversationHistory.slice(
                    -20
                );

        }

        showUploadedSpecialistEvidence(
            data.specialist_evidence
        );

        showUploadedExecutionTrace(
            data.execution_summary
        );

        currentUploadedEvidence = {
            ...(currentUploadedEvidence || {}),
            latest_question: question,
            latest_answer: data.answer,
            specialist_evidence: data.specialist_evidence,
            execution_summary: data.execution_summary
        };

        uploadedChatStatus.textContent =
            "";

    }

    catch (error) {

        addUploadedChatMessage(
            "assistant",
            (
                "I could not analyze the uploaded image: "
                + error.message
            )
        );

        uploadedChatStatus.textContent =
            "";

    }

    finally {

        uploadedChatSendButton.disabled =
            false;

        uploadedChatInput.disabled =
            false;

        uploadedChatInput.focus();

    }

}


setWorkspaceMode(
    "search"
);


function imageUrl(
    path
) {

    return (
        "/result-image?path="
        + encodeURIComponent(
            path
        )
    );

}


function setText(
    id,
    value
) {

    const element =
        document.getElementById(
            id
        );

    if (element) {

        element.textContent =
            value;

    }

}


function formatNumber(
    value,
    digits = 4
) {

    if (
        value === null
        || value === undefined
    ) {

        return "-";

    }

    return Number(
        value
    ).toFixed(
        digits
    );

}


function formatSignedNumber(
    value,
    digits = 4
) {

    if (
        value === null
        || value === undefined
    ) {

        return "-";

    }

    const number =
        Number(
            value
        );

    return (
        (
            number > 0
                ? "+"
                : ""
        )
        + number.toFixed(
            digits
        )
    );

}


function formatPercent(
    value
) {

    if (
        value === null
        || value === undefined
    ) {

        return "-";

    }

    return (
        Number(
            value
        ).toFixed(
            2
        )
        + "%"
    );

}


function formatDateDifference(
    value
) {

    if (
        value === null
        || value === undefined
    ) {

        return "-";

    }

    return (
        value
        + (
            value === 1
                ? " day"
                : " days"
        )
    );

}


function hideModeSections() {

    vegetationMetrics
        .classList
        .add(
            "hidden"
        );

    indexMetrics
        .classList
        .add(
            "hidden"
        );

    imageryMetrics
        .classList
        .add(
            "hidden"
        );

    changeMetrics
        .classList
        .add(
            "hidden"
        );


    vegetationDetails
        .classList
        .add(
            "hidden"
        );

    indexDetails
        .classList
        .add(
            "hidden"
        );

    imageryDetails
        .classList
        .add(
            "hidden"
        );


    imagesGrid
        .classList
        .add(
            "hidden"
        );

    changeImagesGrid
        .classList
        .add(
            "hidden"
        );


    normalDetailsGrid
        .classList
        .add(
            "hidden"
        );

    changeDetailsGrid
        .classList
        .add(
            "hidden"
        );

    trendMetrics
        .classList
        .add(
            "hidden"
        );

    trendImagesGrid
        .classList
        .add(
            "hidden"
        );

    trendDetailsGrid
        .classList
        .add(
            "hidden"
        );

}


function fillCommonDetails(
    data
) {

    setText(
        "resolvedLocation",
        data.location.resolved
    );

    setText(
        "coordinates",
        Number(
            data.location.latitude
        ).toFixed(
            6
        )
        + ", "
        + Number(
            data.location.longitude
        ).toFixed(
            6
        )
    );

    setText(
        "requestedDate",
        data.date.requested
        || "-"
    );

    setText(
        "selectedDate",
        data.date.selected
        || "-"
    );

    setText(
        "dateDifference",
        formatDateDifference(
            data.date
                .difference_days
        )
    );

    setText(
        "tile",
        data.scene.tile
        || "-"
    );

    setText(
        "coverage",
        formatPercent(
            data.scene
                .aoi_coverage_percent
        )
    );

    setText(
        "candidateCount",
        data.scene
            .candidate_count
    );

    setText(
        "rejectedCount",
        data.scene
            .rejected_count
    );

}


function showVegetationResult(
    data
) {

    vegetationMetrics
        .classList
        .remove(
            "hidden"
        );

    vegetationDetails
        .classList
        .remove(
            "hidden"
        );

    imagesGrid
        .classList
        .remove(
            "hidden"
        );

    normalDetailsGrid
        .classList
        .remove(
            "hidden"
        );

    rgbImageCard
        .classList
        .remove(
            "hidden"
        );

    analysisImageCard
        .classList
        .remove(
            "hidden"
        );

    imagesGrid
        .classList
        .remove(
            "single-image"
        );


    fillCommonDetails(
        data
    );


    setText(
        "resultTitle",
        "Vegetation Analysis: "
        + data.location.requested
    );

    setText(
        "meanNdvi",
        formatNumber(
            data.vegetation
                .mean_ndvi
        )
    );

    setText(
        "vegetationCondition",
        data.vegetation
            .condition
    );

    setText(
        "vegetationCloud",
        formatPercent(
            data.quality
                .cloud_percent
        )
    );

    setText(
        "cnnAgreement",
        data.model
            .agreement
            .toUpperCase()
    );

    setText(
        "minNdvi",
        formatNumber(
            data.vegetation
                .min_ndvi
        )
    );

    setText(
        "maxNdvi",
        formatNumber(
            data.vegetation
                .max_ndvi
        )
    );

    setText(
        "stdNdvi",
        formatNumber(
            data.vegetation
                .std_ndvi
        )
    );

    setText(
        "cnnPrediction",
        formatNumber(
            data.model
                .predicted_mean_ndvi
        )
    );

    setText(
        "cnnDifference",
        formatNumber(
            data.model
                .absolute_difference
        )
    );

    setText(
        "vegetationValidPixels",
        formatPercent(
            data.quality
                .scl_valid_percent
        )
    );

    setText(
        "analysisImageTitle",
        "Quality-Masked NDVI"
    );

    document
        .getElementById(
            "rgbImage"
        )
        .src = imageUrl(
            data.outputs
                .rgb_preview
        );

    document
        .getElementById(
            "analysisImage"
        )
        .src = imageUrl(
            data.outputs
                .ndvi_preview
        );

}


function showEnvironmentalResult(
    data
) {

    indexMetrics
        .classList
        .remove(
            "hidden"
        );

    indexDetails
        .classList
        .remove(
            "hidden"
        );

    imagesGrid
        .classList
        .remove(
            "hidden"
        );

    normalDetailsGrid
        .classList
        .remove(
            "hidden"
        );

    rgbImageCard
        .classList
        .remove(
            "hidden"
        );

    analysisImageCard
        .classList
        .remove(
            "hidden"
        );

    imagesGrid
        .classList
        .remove(
            "single-image"
        );


    fillCommonDetails(
        data
    );


    const indexName =
        data.index.name;

    const isNdwi =
        indexName
        === "NDWI";

    const title =
        isNdwi
            ? "Water Analysis"
            : "Built-up / Urban Analysis";


    setText(
        "resultTitle",
        title
        + ": "
        + data.location.requested
    );

    setText(
        "indexMean",
        formatNumber(
            data.index.mean
        )
    );

    setText(
        "positivePixels",
        formatPercent(
            data.index
                .positive_pixel_percent
        )
    );

    setText(
        "indexCloud",
        formatPercent(
            data.quality
                .cloud_percent
        )
    );

    setText(
        "indexInterpretation",
        data.index
            .interpretation
    );

    setText(
        "indexName",
        indexName
    );

    setText(
        "indexMin",
        formatNumber(
            data.index.min
        )
    );

    setText(
        "indexMax",
        formatNumber(
            data.index.max
        )
    );

    setText(
        "indexStd",
        formatNumber(
            data.index.std
        )
    );

    setText(
        "indexPositive",
        formatPercent(
            data.index
                .positive_pixel_percent
        )
    );

    setText(
        "indexValidPixels",
        formatPercent(
            data.index
                .valid_pixel_percent
        )
    );

    setText(
        "indexDetailInterpretation",
        data.index
            .interpretation
    );

    setText(
        "indexDetailsTitle",
        indexName
        + " Scientific Details"
    );

    setText(
        "analysisImageTitle",
        indexName
        + " Map"
    );

    document
        .getElementById(
            "rgbImage"
        )
        .src = imageUrl(
            data.outputs
                .rgb_preview
        );

    document
        .getElementById(
            "analysisImage"
        )
        .src = imageUrl(
            data.outputs
                .index_preview
        );

}


function showImageryResult(
    data
) {

    imageryMetrics
        .classList
        .remove(
            "hidden"
        );

    imageryDetails
        .classList
        .remove(
            "hidden"
        );

    imagesGrid
        .classList
        .remove(
            "hidden"
        );

    normalDetailsGrid
        .classList
        .remove(
            "hidden"
        );

    rgbImageCard
        .classList
        .remove(
            "hidden"
        );

    analysisImageCard
        .classList
        .add(
            "hidden"
        );

    imagesGrid
        .classList
        .add(
            "single-image"
        );


    fillCommonDetails(
        data
    );


    setText(
        "resultTitle",
        "Sentinel-2 Imagery: "
        + data.location.requested
    );

    setText(
        "imageryDate",
        data.date.selected
        || "-"
    );

    setText(
        "imageryCloud",
        formatPercent(
            data.scene
                .cloud_cover_percent
        )
    );

    setText(
        "imageryCoverage",
        formatPercent(
            data.scene
                .aoi_coverage_percent
        )
    );

    setText(
        "imageryResolution",
        data.resolution.display
        + " × "
        + data.resolution.display
    );

    setText(
        "imagerySceneId",
        data.scene.id
    );

    setText(
        "imagerySceneCloud",
        formatPercent(
            data.scene
                .cloud_cover_percent
        )
    );

    setText(
        "displayResolution",
        data.resolution.display
        + " × "
        + data.resolution.display
        + " px"
    );

    document
        .getElementById(
            "rgbImage"
        )
        .src = imageUrl(
            data.outputs
                .rgb_preview
        );

}


function showChangeResult(
    data
) {

    changeMetrics
        .classList
        .remove(
            "hidden"
        );

    changeImagesGrid
        .classList
        .remove(
            "hidden"
        );

    changeDetailsGrid
        .classList
        .remove(
            "hidden"
        );


    const indexName =
        data.change
            .index_name;


    setText(
        "resultTitle",
        indexName
        + " Change Analysis: "
        + data.location.requested
    );


    setText(
        "changeBeforeMean",
        formatNumber(
            data.before.mean
        )
    );

    setText(
        "changeAfterMean",
        formatNumber(
            data.after.mean
        )
    );

    setText(
        "changeMean",
        formatSignedNumber(
            data.change.mean
        )
    );

    setText(
        "changeInterpretation",
        data.change
            .interpretation
    );


    setText(
        "beforeRequestedDate",
        data.dates
            .requested_start
    );

    setText(
        "beforeSelectedDate",
        data.dates
            .selected_start
    );

    setText(
        "beforeTile",
        data.before
            .scene
            .tile
        || "-"
    );

    setText(
        "beforeCloud",
        formatPercent(
            data.before
                .scene
                .cloud_cover
        )
    );

    setText(
        "beforeCoverage",
        formatPercent(
            data.before
                .coverage_percent
        )
    );

    setText(
        "beforeMean",
        formatNumber(
            data.before.mean
        )
    );


    setText(
        "afterRequestedDate",
        data.dates
            .requested_end
    );

    setText(
        "afterSelectedDate",
        data.dates
            .selected_end
    );

    setText(
        "afterTile",
        data.after
            .scene
            .tile
        || "-"
    );

    setText(
        "afterCloud",
        formatPercent(
            data.after
                .scene
                .cloud_cover
        )
    );

    setText(
        "afterCoverage",
        formatPercent(
            data.after
                .coverage_percent
        )
    );

    setText(
        "afterMean",
        formatNumber(
            data.after.mean
        )
    );


    setText(
        "changeIndex",
        indexName
    );

    setText(
        "changeDetailMean",
        formatSignedNumber(
            data.change.mean
        )
    );

    setText(
        "increasePercent",
        formatPercent(
            data.change
                .increase_percent
        )
    );

    setText(
        "decreasePercent",
        formatPercent(
            data.change
                .decrease_percent
        )
    );

    setText(
        "stablePercent",
        formatPercent(
            data.change
                .stable_percent
        )
    );

    setText(
        "changeValidPixels",
        formatPercent(
            data.change
                .valid_pixel_percent
        )
    );

    setText(
        "changeThreshold",
        "±"
        + formatNumber(
            data.change
                .threshold,
            2
        )
    );


    setText(
        "changeResolvedLocation",
        data.location
            .resolved
    );

    setText(
        "changeCoordinates",
        Number(
            data.location
                .latitude
        ).toFixed(
            6
        )
        + ", "
        + Number(
            data.location
                .longitude
        ).toFixed(
            6
        )
    );

    setText(
        "changeMin",
        formatSignedNumber(
            data.change.min
        )
    );

    setText(
        "changeMax",
        formatSignedNumber(
            data.change.max
        )
    );

    setText(
        "changeStd",
        formatNumber(
            data.change.std
        )
    );

    setText(
        "changeDetailInterpretation",
        data.change
            .interpretation
    );


    setText(
        "changeImageTitle",
        indexName
        + " Change Map"
    );


    document
        .getElementById(
            "changeImage"
        )
        .src = imageUrl(
            data.outputs
                .change_preview
        );

}

function showTrendResult(
    data
) {

    trendMetrics
        .classList
        .remove(
            "hidden"
        );

    trendImagesGrid
        .classList
        .remove(
            "hidden"
        );

    trendDetailsGrid
        .classList
        .remove(
            "hidden"
        );


    setText(
        "resultTitle",
        "Vegetation Trend: "
        + data.location.requested
    );


    setText(
        "trendFirstMean",
        formatNumber(
            data.trend
                .first_mean_ndvi
        )
    );

    setText(
        "trendLastMean",
        formatNumber(
            data.trend
                .last_mean_ndvi
        )
    );

    setText(
        "trendTotalChange",
        formatSignedNumber(
            data.trend
                .total_change
        )
    );

    setText(
        "trendInterpretation",
        data.trend
            .interpretation
    );


    setText(
        "trendRequestedStart",
        data.dates
            .requested_start
    );

    setText(
        "trendRequestedEnd",
        data.dates
            .requested_end
    );

    setText(
        "trendObservationCount",
        data.observation_count
    );

    setText(
        "trendDetailFirst",
        formatNumber(
            data.trend
                .first_mean_ndvi
        )
    );

    setText(
        "trendDetailLast",
        formatNumber(
            data.trend
                .last_mean_ndvi
        )
    );

    setText(
        "trendDetailChange",
        formatSignedNumber(
            data.trend
                .total_change
        )
    );

    setText(
        "trendSlope30",
        formatSignedNumber(
            data.trend
                .slope_per_30_days,
            6
        )
    );


    setText(
        "trendResolvedLocation",
        data.location.resolved
    );

    setText(
        "trendCoordinates",
        Number(
            data.location.latitude
        ).toFixed(
            6
        )
        + ", "
        + Number(
            data.location.longitude
        ).toFixed(
            6
        )
    );

    setText(
        "trendDetailInterpretation",
        data.trend
            .interpretation
    );


    document
        .getElementById(
            "trendImage"
        )
        .src = imageUrl(
            data.outputs
                .trend_preview
        );

}

function resetChat() {

    conversationHistory =
        [];


    chatMessages.innerHTML =
        "";


    addChatMessage(
        "assistant",
        (
            "I have the current "
            + "satellite-analysis result. "
            + "Ask me anything about it."
        )
    );


    chatStatus.textContent =
        "";

}


function addChatMessage(
    role,
    content
) {

    const message =
        document.createElement(
            "div"
        );


    message.classList.add(
        "chat-message"
    );


    if (
        role === "user"
    ) {

        message.classList.add(
            "user-message"
        );

    }

    else {

        message.classList.add(
            "assistant-message"
        );

    }


    const roleElement =
        document.createElement(
            "div"
        );


    roleElement.className =
        "chat-role";


    roleElement.textContent =
        (
            role === "user"
                ? "You"
                : "SatQuery AI"
        );


    const textElement =
        document.createElement(
            "div"
        );


    textElement.className =
        "chat-text";


    textElement.textContent =
        content;


    message.appendChild(
        roleElement
    );


    message.appendChild(
        textElement
    );


    chatMessages.appendChild(
        message
    );


    chatMessages.scrollTop =
        chatMessages.scrollHeight;

}


function updateResultFromTool(
    data
) {

    hideModeSections();


    setText(
        "resultMessage",
        data.message
    );


    if (
        data.trend_analysis
        === true
    ) {

        showTrendResult(
            data
        );

    }

    else if (
        data.change_analysis
        === true
    ) {

        showChangeResult(
            data
        );

    }

    else if (
        data.analysis_type
        === "imagery"
    ) {

        showImageryResult(
            data
        );

    }

    else if (
        data.analysis_type
            === "ndwi"
        || data.analysis_type
            === "water"
        || data.analysis_type
            === "ndbi"
        || data.analysis_type
            === "urban"
    ) {

        showEnvironmentalResult(
            data
        );

    }

    else {

        showVegetationResult(
            data
        );

    }


    /*
    Keep the AI chat visible.
    Do NOT reset the conversation.
    */
    aiChat
        .classList
        .remove(
            "hidden"
        );

}

function isVisionQuestion(
    question
) {

    const text =
        question
        .toLowerCase();


    const visionTerms = [
        "what do you see",
        "describe the image",
        "describe this image",
        "describe the map",
        "describe this map",
        "what is visible",
        "visually",
        "visible pattern",
        "spatial pattern",
        "where in the image",
        "where is vegetation",
        "where is water",
        "what does the map show",
        "what does this map show",
        "what does the image show",
        "look at the image",
        "look at the map",
        "interpret the image",
        "interpret the map"
    ];


    return visionTerms.some(
        term =>
            text.includes(
                term
            )
    );

}

async function sendChatMessage() {

    const question =
        chatInput.value.trim();


    if (
        !question
        || !currentAnalysisResult
    ) {

        return;

    }


    addChatMessage(
        "user",
        question
    );


    chatInput.value =
        "";


    chatSendButton.disabled =
        true;


    chatInput.disabled =
        true;


    const useVision =
        isVisionQuestion(
            question
        );


    chatStatus.textContent =
        useVision
            ? "SatQuery AI is examining the current image..."
            : "SatQuery AI is processing your request...";


    try {


        const endpoint =
            useVision
                ? "/vision-chat"
                : "/chat";


        const requestBody =
            useVision
                ? {
                    question:
                        question,

                    analysis_result:
                        currentAnalysisResult
                }

                : {
                    question:
                        question,

                    analysis_result:
                        currentAnalysisResult,

                    conversation_history:
                        conversationHistory
                };


        const response =
            await fetch(
                endpoint,
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            requestBody
                        )
                }
            );


        const data =
            await response.json();


        if (
            !response.ok
        ) {

            const message =
                data.detail?.message
                || "AI assistant failed.";

            throw new Error(
                message
            );

        }


        addChatMessage(
            "assistant",
            data.answer
        );


        conversationHistory.push(
            {
                role:
                    "user",

                content:
                    question
            }
        );


        conversationHistory.push(
            {
                role:
                    "assistant",

                content:
                    data.answer
            }
        );


        /*
        If SatQuery AI executed a new
        scientific analysis, update the
        main result area automatically.
        */
        if (
            data.tool_executed
            === true
            && data.analysis_result
        ) {

            currentAnalysisResult =
                data.analysis_result;


            updateResultFromTool(
                data.analysis_result
            );

        }


        chatStatus.textContent =
            "";

    }

    catch (
        error
    ) {

        addChatMessage(
            "assistant",
            (
                "I could not answer "
                + "that question: "
                + error.message
            )
        );


        chatStatus.textContent =
            "";

    }

    finally {

        chatSendButton.disabled =
            false;


        chatInput.disabled =
            false;


        chatInput.focus();

    }

}


function showResult(
    data
) {

    hideModeSections();
    currentAnalysisResult =
        data;

    downloadSearchReportButton.disabled =
        false;
    downloadSearchJsonButton.disabled =
        false;
    searchReportStatus.textContent =
        "";


    resetChat();


    aiChat
        .classList
        .remove(
            "hidden"
        );

    results.style.display =
        "block";


    setText(
        "resultMessage",
        data.message
    );


    if (
        data.trend_analysis
        === true
    ) {

        showTrendResult(
            data
        );

    }

    else if (
        data.change_analysis
        === true
    ) {

        showChangeResult(
            data
        );

    }

    else if (
        data.analysis_type
        === "imagery"
    ) {

        showImageryResult(
            data
        );

    }

    else if (
        data.analysis_type
            === "ndwi"
        || data.analysis_type
            === "water"
        || data.analysis_type
            === "ndbi"
        || data.analysis_type
            === "urban"
    ) {

        showEnvironmentalResult(
            data
        );

    }

    else {

        showVegetationResult(
            data
        );

    }


    results.scrollIntoView(
        {
            behavior:
                "smooth",

            block:
                "start"
        }
    );

}


async function analyze() {

    const query =
        queryInput.value.trim();


    if (!query) {

        statusBox.innerHTML =
            '<div class="error">'
            + 'Please enter a query.'
            + '</div>';

        return;

    }
    currentAnalysisResult =
        null;

    downloadSearchReportButton.disabled =
        true;
    downloadSearchJsonButton.disabled =
        true;
    searchReportStatus.textContent =
        "";


    conversationHistory =
        [];


    aiChat
        .classList
        .add(
            "hidden"
        );

    analyzeButton.disabled =
        true;


    analyzeButton.textContent =
        "Analyzing...";


    results.style.display =
        "none";


    statusBox.innerHTML =
        '<div class="loading">'
        + 'Searching Sentinel-2 scenes '
        + 'and processing your request...'
        + '</div>';


    try {

        const response =
            await fetch(
                "/analyze",
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            {
                                query:
                                    query
                            }
                        )
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            const message =
                data.detail?.message
                || "Analysis failed.";

            throw new Error(
                message
            );

        }


        statusBox.innerHTML =
            "";


        showResult(
            data
        );

    }

    catch (error) {

        results.style.display =
            "none";


        statusBox.innerHTML =
            '<div class="error">'
            + error.message
            + '</div>';

    }

    finally {

        analyzeButton.disabled =
            false;


        analyzeButton.textContent =
            "Analyze";

    }

}


searchEarthModeButton.addEventListener(
    "click",
    function () {
        setWorkspaceMode("search");
    }
);


analyzeImageryModeButton.addEventListener(
    "click",
    function () {
        setWorkspaceMode("imagery");
    }
);


chooseImageryButton.addEventListener(
    "click",
    function (event) {

        event.stopPropagation();
        imageryFileInput.click();

    }
);



imageryFileInput.addEventListener(
    "change",
    function () {
        chooseUploadedImageryFile(
            imageryFileInput.files[0]
        );
    }
);


["dragenter", "dragover"].forEach(
    eventName => {
        uploadDropzone.addEventListener(
            eventName,
            function (event) {
                event.preventDefault();
                uploadDropzone.classList.add(
                    "drag-active"
                );
            }
        );
    }
);


["dragleave", "drop"].forEach(
    eventName => {
        uploadDropzone.addEventListener(
            eventName,
            function (event) {
                event.preventDefault();
                uploadDropzone.classList.remove(
                    "drag-active"
                );
            }
        );
    }
);


uploadDropzone.addEventListener(
    "drop",
    function (event) {
        chooseUploadedImageryFile(
            event.dataTransfer.files[0]
        );
    }
);


uploadImageryButton.addEventListener(
    "click",
    uploadImagery
);


uploadedChatSendButton.addEventListener(
    "click",
    function () {
        sendUploadedVisionQuestion();
    }
);


uploadedChatInput.addEventListener(
    "keydown",
    function (event) {

        if (
            event.key === "Enter"
            && !event.shiftKey
        ) {

            event.preventDefault();
            sendUploadedVisionQuestion();

        }

    }
);


clearUploadedChatButton.addEventListener(
    "click",
    function () {
        resetUploadedChat();
    }
);


document
    .querySelectorAll(
        ".uploaded-vqa-example"
    )
    .forEach(
        function (button) {

            button.addEventListener(
                "click",
                function () {

                    const question =
                        button.dataset
                            .uploadQuestion;

                    sendUploadedVisionQuestion(
                        question
                    );

                }
            );

        }
    );


if (
    evaluationLink
) {

    evaluationLink.addEventListener(
        "click",
        function (
            event
        ) {

            event.preventDefault();

            const theme =
                lightModeEnabled
                    ? "light"
                    : "dark";

            window.location.href =
                `/evaluation?theme=${theme}`;

        }
    );

}


themeToggle.addEventListener(
    "click",
    function () {

        applyTheme(
            !lightModeEnabled
        );

    }
);


analyzeButton.addEventListener(
    "click",
    analyze
);


queryInput.addEventListener(
    "keydown",
    function (
        event
    ) {

        if (
            event.key
            === "Enter"
        ) {

            analyze();

        }

    }
);


document
    .querySelectorAll(
        ".example-button"
    )
    .forEach(
        button => {

            button.addEventListener(
                "click",
                function () {

                    queryInput.value =
                        button.dataset.query;

                }
            );

        }
    );

chatSendButton.addEventListener(
    "click",
    sendChatMessage
);


chatInput.addEventListener(
    "keydown",
    function (
        event
    ) {

        if (
            event.key
            === "Enter"
        ) {

            sendChatMessage();

        }

    }
);


clearChatButton.addEventListener(
    "click",
    function () {

        resetChat();

        chatInput.focus();

    }
);


// ========================================
// BI-TEMPORAL UPLOADED PAIR WORKFLOW
// ========================================

const singleImageModeButton =
    document.getElementById("singleImageModeButton");
const changePairModeButton =
    document.getElementById("changePairModeButton");
const crossModalModeButton =
    document.getElementById("crossModalModeButton");
const singleImageWorkflow =
    document.getElementById("singleImageWorkflow");
const changePairWorkflow =
    document.getElementById("changePairWorkflow");
const crossModalWorkflow =
    document.getElementById("crossModalWorkflow");

const chooseBeforeButton =
    document.getElementById("chooseBeforeButton");
const chooseAfterButton =
    document.getElementById("chooseAfterButton");
const beforeFileInput =
    document.getElementById("beforeFileInput");
const afterFileInput =
    document.getElementById("afterFileInput");
const analyzePairButton =
    document.getElementById("analyzePairButton");
const pairStatus =
    document.getElementById("pairStatus");
const pairResult =
    document.getElementById("pairResult");

const pairChatMessages =
    document.getElementById("pairChatMessages");
const pairChatInput =
    document.getElementById("pairChatInput");
const pairChatSendButton =
    document.getElementById("pairChatSendButton");
const pairChatStatus =
    document.getElementById("pairChatStatus");
const clearPairChatButton =
    document.getElementById("clearPairChatButton");
const pairExecutionTrace =
    document.getElementById("pairExecutionTrace");

let selectedBeforeFile = null;
let selectedAfterFile = null;
let currentPairId = null;
let pairConversationHistory = [];


function setUploadedImageryMode(mode) {
    const singleMode = mode === "single";
    const pairMode = mode === "pair";
    const crossMode = mode === "crossmodal";

    singleImageWorkflow.classList.toggle(
        "hidden",
        !singleMode
    );
    changePairWorkflow.classList.toggle(
        "hidden",
        !pairMode
    );
    crossModalWorkflow.classList.toggle(
        "hidden",
        !crossMode
    );

    singleImageModeButton.classList.toggle(
        "active",
        singleMode
    );
    changePairModeButton.classList.toggle(
        "active",
        pairMode
    );
    crossModalModeButton.classList.toggle(
        "active",
        crossMode
    );

    singleImageModeButton.setAttribute(
        "aria-pressed",
        singleMode ? "true" : "false"
    );
    changePairModeButton.setAttribute(
        "aria-pressed",
        pairMode ? "true" : "false"
    );
    crossModalModeButton.setAttribute(
        "aria-pressed",
        crossMode ? "true" : "false"
    );
}


function pairFileSizeLabel(bytes) {
    if (!bytes && bytes !== 0) {
        return "-";
    }

    const megabytes = bytes / (1024 * 1024);
    return megabytes.toFixed(2) + " MB";
}


function refreshPairSelection() {
    setText(
        "beforeFileName",
        selectedBeforeFile
            ? selectedBeforeFile.name
            : "No file selected"
    );
    setText(
        "beforeFileSize",
        selectedBeforeFile
            ? pairFileSizeLabel(selectedBeforeFile.size)
            : "-"
    );
    setText(
        "afterFileName",
        selectedAfterFile
            ? selectedAfterFile.name
            : "No file selected"
    );
    setText(
        "afterFileSize",
        selectedAfterFile
            ? pairFileSizeLabel(selectedAfterFile.size)
            : "-"
    );

    analyzePairButton.disabled = !(
        selectedBeforeFile
        && selectedAfterFile
    );

    pairResult.classList.add("hidden");
    pairStatus.textContent = "";
    currentPairId = null;
    pairConversationHistory = [];
    currentPairEvidence = null;
    downloadPairReportButton.disabled = true;
    downloadPairJsonButton.disabled = true;
    pairReportStatus.textContent = "";
}


function resetPairChat() {
    pairConversationHistory = [];
    pairChatMessages.innerHTML = "";
    appendPairMessage(
        "assistant",
        "Pair validated. Ask what changed between the two observations."
    );
    pairChatStatus.textContent = "";
    pairExecutionTrace.classList.add("hidden");
}


function appendPairMessage(role, text) {
    const message = document.createElement("div");
    message.className =
        "chat-message "
        + (role === "user"
            ? "user-message"
            : "assistant-message");

    const roleLabel = document.createElement("div");
    roleLabel.className = "chat-role";
    roleLabel.textContent =
        role === "user"
            ? "You"
            : "SatQuery Change Vision";

    const content = document.createElement("div");
    content.textContent = text;

    message.appendChild(roleLabel);
    message.appendChild(content);
    pairChatMessages.appendChild(message);
    pairChatMessages.scrollTop =
        pairChatMessages.scrollHeight;
}


function showPairExecution(summary) {
    setText(
        "pairExecutionTask",
        summary?.task || "bi_temporal_change_vqa"
    );
    setText(
        "pairExecutionTools",
        Array.isArray(summary?.tools)
            ? summary.tools.join(" → ")
            : "Pair Validator → Change Tool → Vision Assistant"
    );
    setText(
        "pairExecutionStatus",
        summary?.status || "completed"
    );
    pairExecutionTrace.classList.remove("hidden");
}


async function analyzeUploadedPair() {
    if (!selectedBeforeFile || !selectedAfterFile) {
        pairStatus.className = "upload-status error";
        pairStatus.textContent =
            "Choose both a before image and an after image.";
        return;
    }

    analyzePairButton.disabled = true;
    pairStatus.className = "upload-status loading";
    pairStatus.textContent =
        "Validating pair and creating change evidence...";

    const formData = new FormData();
    formData.append("before_file", selectedBeforeFile);
    formData.append("after_file", selectedAfterFile);

    try {
        const response = await fetch(
            "/upload-change-pair",
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        if (!response.ok) {
            const detail = data.detail || {};
            throw new Error(
                detail.message
                || "The pair could not be validated."
            );
        }

        currentPairId = data.pair_id;
        pairConversationHistory = [];
        currentPairEvidence = data;
        downloadPairReportButton.disabled = false;
        downloadPairJsonButton.disabled = false;
        pairReportStatus.textContent = "";

        document.getElementById("beforePreviewImage").src =
            data.outputs.before_preview;
        document.getElementById("afterPreviewImage").src =
            data.outputs.after_preview;
        document.getElementById("pairChangeMap").src =
            data.outputs.change_map;

        setText(
            "pairValidationMessage",
            data.pair_validation.message
        );
        setText(
            "pairSameDimensions",
            data.pair_validation.same_dimensions
                ? "Yes"
                : "No"
        );
        setText(
            "pairBothGeoreferenced",
            data.pair_validation.both_georeferenced
                ? "Yes"
                : "No"
        );
        setText(
            "pairGeospatialCompatible",
            data.pair_validation.geospatial_compatible
                ? "Yes"
                : "Not independently verified"
        );
        setText(
            "pairBeforeCrs",
            data.before.crs || "Not available"
        );
        setText(
            "pairAfterCrs",
            data.after.crs || "Not available"
        );
        setText(
            "pairMeanDifference",
            Number(
                data.visual_change.mean_visual_difference_percent
            ).toFixed(2) + "%"
        );
        setText(
            "pairChangedPixels",
            Number(
                data.visual_change.changed_pixel_percent
            ).toFixed(2) + "%"
        );
        setText(
            "pairThreshold",
            data.visual_change.visual_change_threshold
        );
        setText(
            "pairHeuristicMeaning",
            data.visual_change.interpretation
        );

        pairResult.classList.remove("hidden");
        pairStatus.className = "upload-status success";
        pairStatus.textContent =
            "Pair validated. Change VQA is ready.";

        resetPairChat();
        showPairExecution(
            data.execution_summary
        );

        currentPairEvidence = {
            ...(currentPairEvidence || {}),
            latest_question: question,
            latest_answer: data.answer,
            execution_summary: data.execution_summary
        };
    }
    catch (error) {
        pairStatus.className = "upload-status error";
        pairStatus.textContent = error.message;
    }
    finally {
        analyzePairButton.disabled = !(
            selectedBeforeFile
            && selectedAfterFile
        );
    }
}


async function sendPairQuestion(questionOverride = null) {
    if (!currentPairId) {
        pairChatStatus.textContent =
            "Upload and validate a before/after pair first.";
        return;
    }

    const question = (
        questionOverride
        || pairChatInput.value
        || ""
    ).trim();

    if (!question) {
        pairChatStatus.textContent =
            "Enter a question about the change.";
        return;
    }

    appendPairMessage("user", question);
    pairChatInput.value = "";
    pairChatSendButton.disabled = true;
    pairChatInput.disabled = true;
    pairChatStatus.textContent =
        "SatQuery Change Vision is comparing the two observations...";

    try {
        const response = await fetch(
            "/uploaded-change-chat",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    pair_id: currentPairId,
                    question: question,
                    conversation_history:
                        pairConversationHistory
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            const detail = data.detail || {};
            throw new Error(
                detail.message
                || "Change VQA failed."
            );
        }

        appendPairMessage(
            "assistant",
            data.answer
        );

        pairConversationHistory.push(
            {
                role: "user",
                content: question
            },
            {
                role: "assistant",
                content: data.answer
            }
        );

        if (pairConversationHistory.length > 10) {
            pairConversationHistory =
                pairConversationHistory.slice(-10);
        }

        pairChatStatus.textContent = "";
        showPairExecution(
            data.execution_summary
        );
    }
    catch (error) {
        appendPairMessage(
            "assistant",
            "I could not analyze the pair: "
            + error.message
        );
        pairChatStatus.textContent = "";
    }
    finally {
        pairChatSendButton.disabled = false;
        pairChatInput.disabled = false;
        pairChatInput.focus();
    }
}

// OPTICAL + SAR CROSS-MODAL WORKFLOW
// ========================================

const chooseOpticalButton =
    document.getElementById("chooseOpticalButton");
const chooseSarButton =
    document.getElementById("chooseSarButton");
const opticalFileInput =
    document.getElementById("opticalFileInput");
const sarFileInput =
    document.getElementById("sarFileInput");
const analyzeCrossModalButton =
    document.getElementById("analyzeCrossModalButton");
const crossModalStatus =
    document.getElementById("crossModalStatus");
const crossModalResult =
    document.getElementById("crossModalResult");
const crossModalChatMessages =
    document.getElementById("crossModalChatMessages");
const crossModalChatInput =
    document.getElementById("crossModalChatInput");
const crossModalChatSendButton =
    document.getElementById("crossModalChatSendButton");
const crossModalChatStatus =
    document.getElementById("crossModalChatStatus");
const clearCrossModalChatButton =
    document.getElementById("clearCrossModalChatButton");
const crossModalExecutionTrace =
    document.getElementById("crossModalExecutionTrace");

let selectedOpticalFile = null;
let selectedSarFile = null;
let currentCrossModalPairId = null;
let crossModalConversationHistory = [];


function refreshCrossModalSelection() {
    setText(
        "opticalFileName",
        selectedOpticalFile
            ? selectedOpticalFile.name
            : "No file selected"
    );
    setText(
        "opticalFileSize",
        selectedOpticalFile
            ? pairFileSizeLabel(selectedOpticalFile.size)
            : "-"
    );
    setText(
        "sarFileName",
        selectedSarFile
            ? selectedSarFile.name
            : "No file selected"
    );
    setText(
        "sarFileSize",
        selectedSarFile
            ? pairFileSizeLabel(selectedSarFile.size)
            : "-"
    );

    analyzeCrossModalButton.disabled = !(
        selectedOpticalFile
        && selectedSarFile
    );

    crossModalResult.classList.add("hidden");
    crossModalStatus.textContent = "";
    currentCrossModalPairId = null;
    crossModalConversationHistory = [];
    currentCrossModalEvidence = null;
    downloadCrossModalReportButton.disabled = true;
    downloadCrossModalJsonButton.disabled = true;
    crossModalReportStatus.textContent = "";
}


function appendCrossModalMessage(role, text) {
    const message = document.createElement("div");
    message.className =
        "chat-message "
        + (role === "user"
            ? "user-message"
            : "assistant-message");

    const roleLabel = document.createElement("div");
    roleLabel.className = "chat-role";
    roleLabel.textContent =
        role === "user"
            ? "You"
            : "SatQuery Cross-Modal Vision";

    const content = document.createElement("div");
    content.textContent = text;

    message.appendChild(roleLabel);
    message.appendChild(content);
    crossModalChatMessages.appendChild(message);
    crossModalChatMessages.scrollTop =
        crossModalChatMessages.scrollHeight;
}


function resetCrossModalChat() {
    crossModalConversationHistory = [];
    crossModalChatMessages.innerHTML = "";
    appendCrossModalMessage(
        "assistant",
        "Pair validated. Ask a question that uses the optical and SAR evidence together."
    );
    crossModalChatStatus.textContent = "";
    crossModalExecutionTrace.classList.add("hidden");
}


function showCrossModalExecution(summary) {
    setText(
        "crossModalExecutionTask",
        summary?.task || "optical_sar_joint_vqa"
    );
    setText(
        "crossModalExecutionTools",
        Array.isArray(summary?.tools)
            ? summary.tools.join(" → ")
            : "Pair Validator → Fusion Tool → Vision Assistant"
    );
    setText(
        "crossModalExecutionStatus",
        summary?.status || "completed"
    );
    crossModalExecutionTrace.classList.remove("hidden");
}


async function analyzeCrossModalPair() {
    if (!selectedOpticalFile || !selectedSarFile) {
        crossModalStatus.className = "upload-status error";
        crossModalStatus.textContent =
            "Choose both an optical image and a SAR image.";
        return;
    }

    analyzeCrossModalButton.disabled = true;
    crossModalStatus.className = "upload-status loading";
    crossModalStatus.textContent =
        "Validating optical-SAR compatibility and fusing complementary evidence...";

    const formData = new FormData();
    formData.append("optical_file", selectedOpticalFile);
    formData.append("sar_file", selectedSarFile);

    try {
        const response = await fetch(
            "/upload-crossmodal-pair",
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        if (!response.ok) {
            const detail = data.detail || {};
            throw new Error(
                detail.message
                || "The optical-SAR pair could not be validated."
            );
        }

        currentCrossModalPairId = data.pair_id;
        crossModalConversationHistory = [];
        currentCrossModalEvidence = data;
        downloadCrossModalReportButton.disabled = false;
        downloadCrossModalJsonButton.disabled = false;
        crossModalReportStatus.textContent = "";

        document.getElementById("opticalPreviewImage").src =
            data.outputs.optical_preview;
        document.getElementById("sarPreviewImage").src =
            data.outputs.sar_preview;
        document.getElementById("crossModalFusionMap").src =
            data.outputs.fusion_map;

        setText(
            "crossModalValidationMessage",
            data.pair_validation.message
        );
        setText(
            "crossSameDimensions",
            data.pair_validation.same_dimensions
                ? "Yes"
                : "No"
        );
        setText(
            "crossBothGeoreferenced",
            data.pair_validation.both_georeferenced
                ? "Yes"
                : "No"
        );
        setText(
            "crossGeospatialCompatible",
            data.pair_validation.geospatial_compatible
                ? "Yes"
                : "Not independently verified"
        );
        setText(
            "crossOpticalCrs",
            data.optical.crs || "Not available"
        );
        setText(
            "crossSarCrs",
            data.sar.crs || "Not available"
        );
        setText(
            "crossWaterCandidates",
            Number(
                data.crossmodal_evidence
                    .water_like_candidate_percent
            ).toFixed(2) + "%"
        );
        setText(
            "crossBuiltCandidates",
            Number(
                data.crossmodal_evidence
                    .built_up_like_candidate_percent
            ).toFixed(2) + "%"
        );
        setText(
            "crossSarIntensity",
            Number(
                data.crossmodal_evidence
                    .mean_sar_display_intensity_percent
            ).toFixed(2) + "%"
        );
        setText(
            "crossOpticalTexture",
            Number(
                data.crossmodal_evidence
                    .mean_optical_texture_percent
            ).toFixed(2) + "%"
        );
        setText(
            "crossSarTexture",
            Number(
                data.crossmodal_evidence
                    .mean_sar_texture_percent
            ).toFixed(2) + "%"
        );
        setText(
            "crossModalInterpretation",
            data.crossmodal_evidence.interpretation
        );

        crossModalResult.classList.remove("hidden");
        crossModalStatus.className = "upload-status success";
        crossModalStatus.textContent =
            "Optical-SAR pair validated. Cross-modal VQA is ready.";

        resetCrossModalChat();
        showCrossModalExecution(
            data.execution_summary
        );

        currentCrossModalEvidence = {
            ...(currentCrossModalEvidence || {}),
            latest_question: question,
            latest_answer: data.answer,
            execution_summary: data.execution_summary
        };
    }
    catch (error) {
        crossModalStatus.className = "upload-status error";
        crossModalStatus.textContent = error.message;
    }
    finally {
        analyzeCrossModalButton.disabled = !(
            selectedOpticalFile
            && selectedSarFile
        );
    }
}


async function sendCrossModalQuestion(questionOverride = null) {
    if (!currentCrossModalPairId) {
        crossModalChatStatus.textContent =
            "Upload and validate an optical-SAR pair first.";
        return;
    }

    const question = (
        questionOverride
        || crossModalChatInput.value
        || ""
    ).trim();

    if (!question) {
        crossModalChatStatus.textContent =
            "Enter a question about the optical-SAR pair.";
        return;
    }

    appendCrossModalMessage("user", question);
    crossModalChatInput.value = "";
    crossModalChatSendButton.disabled = true;
    crossModalChatInput.disabled = true;
    crossModalChatStatus.textContent =
        "SatQuery Cross-Modal Vision is reasoning over both modalities...";

    try {
        const response = await fetch(
            "/uploaded-crossmodal-chat",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    pair_id: currentCrossModalPairId,
                    question: question,
                    conversation_history:
                        crossModalConversationHistory
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            const detail = data.detail || {};
            throw new Error(
                detail.message
                || "Optical-SAR VQA failed."
            );
        }

        appendCrossModalMessage(
            "assistant",
            data.answer
        );

        crossModalConversationHistory.push(
            {
                role: "user",
                content: question
            },
            {
                role: "assistant",
                content: data.answer
            }
        );

        if (crossModalConversationHistory.length > 10) {
            crossModalConversationHistory =
                crossModalConversationHistory.slice(-10);
        }

        crossModalChatStatus.textContent = "";
        showCrossModalExecution(
            data.execution_summary
        );
    }
    catch (error) {
        appendCrossModalMessage(
            "assistant",
            "I could not analyze the optical-SAR pair: "
            + error.message
        );
        crossModalChatStatus.textContent = "";
    }
    finally {
        crossModalChatSendButton.disabled = false;
        crossModalChatInput.disabled = false;
        crossModalChatInput.focus();
    }
}


crossModalModeButton.addEventListener(
    "click",
    function () {
        setUploadedImageryMode("crossmodal");
    }
);

chooseOpticalButton.addEventListener(
    "click",
    function () {
        opticalFileInput.click();
    }
);

chooseSarButton.addEventListener(
    "click",
    function () {
        sarFileInput.click();
    }
);

opticalFileInput.addEventListener(
    "change",
    function () {
        selectedOpticalFile =
            opticalFileInput.files[0] || null;
        refreshCrossModalSelection();
    }
);

sarFileInput.addEventListener(
    "change",
    function () {
        selectedSarFile =
            sarFileInput.files[0] || null;
        refreshCrossModalSelection();
    }
);

analyzeCrossModalButton.addEventListener(
    "click",
    analyzeCrossModalPair
);

crossModalChatSendButton.addEventListener(
    "click",
    function () {
        sendCrossModalQuestion();
    }
);

crossModalChatInput.addEventListener(
    "keydown",
    function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
            sendCrossModalQuestion();
        }
    }
);

clearCrossModalChatButton.addEventListener(
    "click",
    resetCrossModalChat
);

document
    .querySelectorAll(".crossmodal-vqa-example")
    .forEach(
        function (button) {
            button.addEventListener(
                "click",
                function () {
                    sendCrossModalQuestion(
                        button.dataset.crossmodalQuestion
                    );
                }
            );
        }
    );

singleImageModeButton.addEventListener(
    "click",
    function () {
        setUploadedImageryMode("single");
    }
);

changePairModeButton.addEventListener(
    "click",
    function () {
        setUploadedImageryMode("pair");
    }
);

chooseBeforeButton.addEventListener(
    "click",
    function () {
        beforeFileInput.click();
    }
);

chooseAfterButton.addEventListener(
    "click",
    function () {
        afterFileInput.click();
    }
);

beforeFileInput.addEventListener(
    "change",
    function () {
        selectedBeforeFile =
            beforeFileInput.files[0] || null;
        refreshPairSelection();
    }
);

afterFileInput.addEventListener(
    "change",
    function () {
        selectedAfterFile =
            afterFileInput.files[0] || null;
        refreshPairSelection();
    }
);

analyzePairButton.addEventListener(
    "click",
    analyzeUploadedPair
);

pairChatSendButton.addEventListener(
    "click",
    function () {
        sendPairQuestion();
    }
);

pairChatInput.addEventListener(
    "keydown",
    function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
            sendPairQuestion();
        }
    }
);

clearPairChatButton.addEventListener(
    "click",
    resetPairChat
);

document
    .querySelectorAll(".pair-vqa-example")
    .forEach(
        function (button) {
            button.addEventListener(
                "click",
                function () {
                    sendPairQuestion(
                        button.dataset.pairQuestion
                    );
                }
            );
        }
    );

setUploadedImageryMode("single");


// ========================================
// CHUNK 7 - DOWNLOADABLE EVIDENCE REPORTS
// ========================================

function triggerFileDownload(
    url
) {
    const link =
        document.createElement(
            "a"
        );

    link.href = url;
    link.style.display = "none";

    document.body.appendChild(
        link
    );

    link.click();
    link.remove();
}


async function requestEvidenceReport(
    workflow,
    title,
    record,
    format,
    statusElement
) {
    if (!record) {
        statusElement.textContent =
            "Run or validate an analysis first.";
        return;
    }

    statusElement.textContent =
        "Preparing auditable evidence report...";

    try {
        const response = await fetch(
            "/evidence-report",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    workflow: workflow,
                    title: title,
                    record: record
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            const detail = data.detail || {};
            throw new Error(
                detail.message
                || detail
                || "Evidence report generation failed."
            );
        }

        const downloadUrl =
            format === "json"
                ? data.json_url
                : data.html_url;

        triggerFileDownload(
            downloadUrl
        );

        statusElement.textContent =
            format === "json"
                ? "JSON evidence downloaded."
                : (
                    "Evidence report downloaded"
                    + (
                        data.embedded_image_count
                            ? " with "
                                + data.embedded_image_count
                                + " embedded visual(s)."
                            : "."
                    )
                );
    }
    catch (error) {
        statusElement.textContent =
            "Report failed: "
            + error.message;
    }
}


function searchEvidenceRecord() {
    if (!currentAnalysisResult) {
        return null;
    }

    return {
        ...currentAnalysisResult,
        conversation_history:
            conversationHistory
    };
}


function uploadedEvidenceRecord() {
    if (!currentUploadedEvidence) {
        return null;
    }

    return {
        ...currentUploadedEvidence,
        conversation_history:
            uploadedConversationHistory
    };
}


function pairEvidenceRecord() {
    if (!currentPairEvidence) {
        return null;
    }

    return {
        ...currentPairEvidence,
        conversation_history:
            pairConversationHistory
    };
}


function crossModalEvidenceRecord() {
    if (!currentCrossModalEvidence) {
        return null;
    }

    return {
        ...currentCrossModalEvidence,
        conversation_history:
            crossModalConversationHistory
    };
}


downloadSearchReportButton.addEventListener(
    "click",
    function () {
        requestEvidenceReport(
            "search_earth",
            "SatQuery Search Earth Evidence Report",
            searchEvidenceRecord(),
            "html",
            searchReportStatus
        );
    }
);


downloadSearchJsonButton.addEventListener(
    "click",
    function () {
        requestEvidenceReport(
            "search_earth",
            "SatQuery Search Earth Evidence Report",
            searchEvidenceRecord(),
            "json",
            searchReportStatus
        );
    }
);


downloadUploadedReportButton.addEventListener(
    "click",
    function () {
        requestEvidenceReport(
            "single_image",
            "SatQuery Single-Image Vision-Language Evidence Report",
            uploadedEvidenceRecord(),
            "html",
            uploadedReportStatus
        );
    }
);


downloadUploadedJsonButton.addEventListener(
    "click",
    function () {
        requestEvidenceReport(
            "single_image",
            "SatQuery Single-Image Vision-Language Evidence Report",
            uploadedEvidenceRecord(),
            "json",
            uploadedReportStatus
        );
    }
);


downloadPairReportButton.addEventListener(
    "click",
    function () {
        requestEvidenceReport(
            "bitemporal_pair",
            "SatQuery Bi-Temporal Change Evidence Report",
            pairEvidenceRecord(),
            "html",
            pairReportStatus
        );
    }
);


downloadPairJsonButton.addEventListener(
    "click",
    function () {
        requestEvidenceReport(
            "bitemporal_pair",
            "SatQuery Bi-Temporal Change Evidence Report",
            pairEvidenceRecord(),
            "json",
            pairReportStatus
        );
    }
);


downloadCrossModalReportButton.addEventListener(
    "click",
    function () {
        requestEvidenceReport(
            "optical_sar_pair",
            "SatQuery Optical-SAR Cross-Modal Evidence Report",
            crossModalEvidenceRecord(),
            "html",
            crossModalReportStatus
        );
    }
);


downloadCrossModalJsonButton.addEventListener(
    "click",
    function () {
        requestEvidenceReport(
            "optical_sar_pair",
            "SatQuery Optical-SAR Cross-Modal Evidence Report",
            crossModalEvidenceRecord(),
            "json",
            crossModalReportStatus
        );
    }
);

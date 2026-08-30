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


let currentAnalysisResult =
    null;


let conversationHistory =
    [];
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
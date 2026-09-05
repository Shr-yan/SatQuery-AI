const refreshEvaluationButton = document.getElementById("refreshEvaluationButton");
const evaluationStatus = document.getElementById("evaluationStatus");
const readinessCount = document.getElementById("readinessCount");
const runtimeEventCount = document.getElementById("runtimeEventCount");
const runtimeSuccessCount = document.getElementById("runtimeSuccessCount");
const specialistAccuracy = document.getElementById("specialistAccuracy");
const readinessList = document.getElementById("readinessList");
const runtimeSummary = document.getElementById("runtimeSummary");
const specialistSummary = document.getElementById("specialistSummary");
const demoCases = document.getElementById("demoCases");
const benchmarkInput = document.getElementById("benchmarkInput");
const runBenchmarkButton = document.getElementById("runBenchmarkButton");
const benchmarkStatus = document.getElementById("benchmarkStatus");
const benchmarkResult = document.getElementById("benchmarkResult");
const latestBenchmarkRun = document.getElementById("latestBenchmarkRun");

const backToSatQueryLink = document.getElementById("backToSatQueryLink");
const evaluationThemeToggle = document.getElementById("evaluationThemeToggle");
const evaluationThemeIcon = document.getElementById("evaluationThemeIcon");
const evaluationThemeLabel = document.getElementById("evaluationThemeLabel");

const publicBenchmarkFileInput = document.getElementById("publicBenchmarkFileInput");
const importPublicBenchmarkButton = document.getElementById("importPublicBenchmarkButton");
const publicBenchmarkImportStatus = document.getElementById("publicBenchmarkImportStatus");
const publicBenchmarkSummary = document.getElementById("publicBenchmarkSummary");

let lightModeEnabled = false;

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function detailRow(label, value) {
    return `
        <div class="detail">
            <span>${escapeHtml(label)}</span>
            <span>${escapeHtml(value)}</span>
        </div>
    `;
}

function applyEvaluationTheme(useLightMode) {
    lightModeEnabled = Boolean(useLightMode);

    document.body.classList.toggle(
        "light-mode",
        lightModeEnabled
    );

    evaluationThemeToggle.setAttribute(
        "aria-pressed",
        lightModeEnabled ? "true" : "false"
    );

    evaluationThemeToggle.setAttribute(
        "aria-label",
        lightModeEnabled
            ? "Switch to dark mode"
            : "Switch to light mode"
    );

    evaluationThemeIcon.textContent =
        lightModeEnabled ? "🌙" : "☀️";

    evaluationThemeLabel.textContent =
        lightModeEnabled ? "Dark mode" : "Light mode";

    const themeName = lightModeEnabled ? "light" : "dark";

    backToSatQueryLink.href = `/app?theme=${themeName}`;

    const currentUrl = new URL(window.location.href);
    currentUrl.searchParams.set("theme", themeName);
    window.history.replaceState({}, "", currentUrl);
}

const requestedTheme = new URLSearchParams(
    window.location.search
).get("theme");

applyEvaluationTheme(
    requestedTheme === "light"
);

function renderReadiness(items) {
    readinessList.innerHTML = items.map((item) => `
        <article class="readiness-item">
            <div class="readiness-item-top">
                <strong>${escapeHtml(item.requirement)}</strong>
                <span class="readiness-badge">${escapeHtml(item.status)}</span>
            </div>
            <p>${escapeHtml(item.evidence)}</p>
        </article>
    `).join("");
}

function renderRuntime(summary) {
    const counts = summary.workflow_counts || {};
    const workflowRows = Object.entries(counts)
        .map(([workflow, count]) => detailRow(workflow, count))
        .join("");

    runtimeSummary.innerHTML = `
        ${detailRow("Total events", summary.total_events ?? 0)}
        ${detailRow("Successful", summary.successful_events ?? 0)}
        ${detailRow("Failed", summary.failed_events ?? 0)}
        ${detailRow(
            "Average duration",
            summary.average_duration_ms == null
                ? "-"
                : `${summary.average_duration_ms} ms`
        )}
        <h3 class="evaluation-subheading">Workflow events</h3>
        ${workflowRows || "<p>No workflow events recorded yet.</p>"}
    `;
}

function renderSpecialist(status) {
    specialistSummary.innerHTML = `
        ${detailRow("Available", status.available ? "Yes" : "No")}
        ${detailRow("Model", status.model_name || "-")}
        ${detailRow("Dataset", status.dataset || "-")}
        ${detailRow(
            "Held-out test accuracy",
            status.test_accuracy_percent == null
                ? "-"
                : `${Number(status.test_accuracy_percent).toFixed(2)}%`
        )}
        ${detailRow(
            "Runtime role",
            "Supporting remote-sensing scene evidence; not calibrated confidence"
        )}
    `;
}

function renderDemoCases(items) {
    demoCases.innerHTML = items.map((item) => `
        <article class="demo-case-card">
            <span class="phase-badge">${escapeHtml(item.workflow)}</span>
            <h3>${escapeHtml(item.capability)}</h3>
            <p class="demo-prompt">“${escapeHtml(item.prompt)}”</p>
            <p><b>Evidence:</b> ${escapeHtml(item.expected_evidence)}</p>
        </article>
    `).join("");
}

function renderBenchmarkSummary(summary) {
    const latest = summary.latest_run;

    if (!latest) {
        latestBenchmarkRun.innerHTML = `
            <p>No saved local proxy benchmark run yet.</p>
            <p class="evaluation-note">Run the proxy evaluator above when you have reference/prediction pairs.</p>
        `;
        return;
    }

    latestBenchmarkRun.innerHTML = `
        ${detailRow("Saved runs", summary.run_count ?? 0)}
        ${detailRow("Cases", latest.overall?.count ?? 0)}
        ${detailRow("Exact match", `${latest.overall?.exact_match_percent ?? 0}%`)}
        ${detailRow("Token F1", `${latest.overall?.token_f1_percent ?? 0}%`)}
        <p class="evaluation-note">${escapeHtml(summary.metric_note || "")}</p>
    `;
}

function renderPublicBenchmarkSummary(summary) {
    const byBenchmark = summary.latest_by_benchmark || {};
    const runCounts = summary.run_counts_by_benchmark || {};
    const entries = Object.entries(byBenchmark);

    if (entries.length === 0) {
        publicBenchmarkSummary.innerHTML = `
            <p>No public benchmark subset run has been imported yet.</p>
            <p class="evaluation-note">
                Run a supplied Kaggle diagnostic script, download its JSON output,
                then import the result here.
            </p>
        `;
        return;
    }

    const preferredOrder = ["VRSBench", "CDVQA"];
    entries.sort(([nameA], [nameB]) => {
        const indexA = preferredOrder.indexOf(nameA);
        const indexB = preferredOrder.indexOf(nameB);
        const rankA = indexA === -1 ? 999 : indexA;
        const rankB = indexB === -1 ? 999 : indexB;
        return rankA - rankB || nameA.localeCompare(nameB);
    });

    const cards = entries.map(([benchmarkName, latest]) => {
        const metrics = latest.metrics || {};
        const categories = Array.isArray(latest.categories)
            ? latest.categories.join(", ")
            : "-";

        return `
            <article class="demo-case-card public-benchmark-run-card">
                <span class="phase-badge">${escapeHtml(benchmarkName)}</span>
                <h3>${escapeHtml(latest.subset_name || "Public subset diagnostic")}</h3>
                <div class="evaluation-metric-grid compact-grid public-benchmark-metrics">
                    <article class="metric evaluation-metric-card">
                        <div class="metric-label">Cases</div>
                        <div class="metric-value">${escapeHtml(latest.sample_count ?? 0)}</div>
                    </article>
                    <article class="metric evaluation-metric-card">
                        <div class="metric-label">Exact Match</div>
                        <div class="metric-value">${escapeHtml(metrics.exact_match_percent ?? 0)}%</div>
                    </article>
                    <article class="metric evaluation-metric-card">
                        <div class="metric-label">Token F1</div>
                        <div class="metric-value">${escapeHtml(metrics.token_f1_percent ?? 0)}%</div>
                    </article>
                </div>
                ${detailRow("Saved runs", runCounts[benchmarkName] ?? 1)}
                ${detailRow("Model", latest.model || "-")}
                ${detailRow(
                    "RS specialist used",
                    latest.satquery_rs_specialist_used ? "Yes" : "No"
                )}
                ${detailRow("Categories / types", categories)}
                <p class="evaluation-note">${escapeHtml(latest.evaluation_note || "")}</p>
            </article>
        `;
    }).join("");

    publicBenchmarkSummary.innerHTML = `
        <p class="evaluation-note">
            Total imported public benchmark runs: ${escapeHtml(summary.run_count ?? entries.length)}
        </p>
        <div class="demo-case-grid public-benchmark-history-grid">
            ${cards}
        </div>
    `;
}

async function loadEvaluationCenter() {
    evaluationStatus.textContent = "Loading evaluation data…";

    try {
        const response = await fetch("/evaluation-center-data");
        const data = await response.json();

        if (!response.ok || data.success !== true) {
            throw new Error(
                data?.detail?.message
                || data?.detail
                || "Could not load evaluation data."
            );
        }

        const readiness = data.implementation_readiness || [];
        const runtime = data.runtime_summary || {};
        const specialist = data.remote_sensing_specialist || {};

        readinessCount.textContent = readiness.length;
        runtimeEventCount.textContent = runtime.total_events ?? 0;
        runtimeSuccessCount.textContent = runtime.successful_events ?? 0;
        specialistAccuracy.textContent = specialist.test_accuracy_percent == null
            ? "-"
            : `${Number(specialist.test_accuracy_percent).toFixed(2)}%`;

        renderReadiness(readiness);
        renderRuntime(runtime);
        renderSpecialist(specialist);
        renderDemoCases(data.demo_cases || []);
        renderBenchmarkSummary(data.benchmark_summary || {});
        renderPublicBenchmarkSummary(data.public_benchmark_summary || {});

        evaluationStatus.textContent = "Evaluation data loaded.";
    } catch (error) {
        evaluationStatus.textContent = `Error: ${error.message}`;
    }
}

async function runProxyBenchmark() {
    benchmarkStatus.textContent = "Evaluating…";
    runBenchmarkButton.disabled = true;

    try {
        const records = JSON.parse(benchmarkInput.value);

        if (!Array.isArray(records) || records.length === 0) {
            throw new Error("Paste a non-empty JSON array of evaluation records.");
        }

        const response = await fetch("/benchmark-evaluate", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({records}),
        });

        const data = await response.json();

        if (!response.ok || data.success !== true) {
            throw new Error(
                data?.detail?.message
                || data?.detail
                || "Proxy evaluation failed."
            );
        }

        const result = data.result;

        benchmarkResult.classList.remove("hidden");
        benchmarkResult.innerHTML = `
            <div class="evaluation-metric-grid compact-grid">
                <article class="metric evaluation-metric-card">
                    <div class="metric-label">Cases</div>
                    <div class="metric-value">${result.overall.count}</div>
                </article>
                <article class="metric evaluation-metric-card">
                    <div class="metric-label">Exact Match</div>
                    <div class="metric-value">${result.overall.exact_match_percent}%</div>
                </article>
                <article class="metric evaluation-metric-card">
                    <div class="metric-label">Token F1</div>
                    <div class="metric-value">${result.overall.token_f1_percent}%</div>
                </article>
            </div>
            <p class="evaluation-note">${escapeHtml(result.metric_note)}</p>
        `;

        benchmarkStatus.textContent = "Saved local proxy run.";
        await loadEvaluationCenter();
    } catch (error) {
        benchmarkStatus.textContent = `Error: ${error.message}`;
    } finally {
        runBenchmarkButton.disabled = false;
    }
}

async function importPublicBenchmark() {
    const file = publicBenchmarkFileInput.files?.[0];

    if (!file) {
        publicBenchmarkImportStatus.textContent = "Choose the Kaggle result JSON first.";
        return;
    }

    publicBenchmarkImportStatus.textContent = "Importing…";
    importPublicBenchmarkButton.disabled = true;

    try {
        const text = await file.text();
        const result = JSON.parse(text);

        const response = await fetch("/public-benchmark-import", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({result}),
        });

        const data = await response.json();

        if (!response.ok || data.success !== true) {
            throw new Error(
                data?.detail?.message
                || data?.detail
                || "Public benchmark import failed."
            );
        }

        publicBenchmarkImportStatus.textContent = `Imported ${result.benchmark || "public benchmark"} diagnostic result.`;
        await loadEvaluationCenter();
    } catch (error) {
        publicBenchmarkImportStatus.textContent = `Error: ${error.message}`;
    } finally {
        importPublicBenchmarkButton.disabled = false;
    }
}

evaluationThemeToggle.addEventListener(
    "click",
    function () {
        applyEvaluationTheme(!lightModeEnabled);
    }
);

refreshEvaluationButton.addEventListener("click", loadEvaluationCenter);
runBenchmarkButton.addEventListener("click", runProxyBenchmark);
importPublicBenchmarkButton.addEventListener("click", importPublicBenchmark);

loadEvaluationCenter();

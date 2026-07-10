// Global State
let currentPrdTitle = "";
let currentPrdMarkdown = "";
let currentFeasibilityReport = null;
let currentSprintGoal = "";
let currentSprintTickets = [];
let currentUpgradePrdMarkdown = "";

// Initialize Lucide Icons
document.addEventListener("DOMContentLoaded", () => {
    lucide.createIcons();
    initTabs();
    initSubTabs();
    runConnectionDiagnostics();
    
    // Set default repo paths if available
    const defaultPath = "D:/PM agent/scratch_mock_repo";
    document.getElementById("feasibility-repo").value = defaultPath;
    document.getElementById("qa-repo-path").value = defaultPath;
    document.getElementById("qa-upgrade-path").value = defaultPath;
    document.getElementById("dashboard-mock-path").innerText = defaultPath;
});

// Tab Navigation Logic
function initTabs() {
    const navItems = document.querySelectorAll(".sidebar-nav .nav-item");
    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const target = item.getAttribute("data-target");
            if (target) {
                switchTab(target);
            }
        });
    });
}

function switchTab(tabId) {
    // Update sidebar items
    const navItems = document.querySelectorAll(".sidebar-nav .nav-item");
    navItems.forEach(item => {
        if (item.getAttribute("data-target") === tabId) {
            item.classList.add("active");
        } else {
            item.classList.remove("active");
        }
    });

    // Update tab panels
    const tabPanels = document.querySelectorAll(".main-content .tab-content");
    tabPanels.forEach(panel => {
        if (panel.id === tabId) {
            panel.classList.add("active");
        } else {
            panel.classList.remove("active");
        }
    });
}

// Sub-Tab Navigation inside components
function initSubTabs() {
    // PRD Generator Subnav
    const prdSubnavs = document.querySelectorAll(".tabs-subnav .subnav-item");
    prdSubnavs.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetPanel = btn.getAttribute("data-subtarget");
            
            // Toggle buttons
            prdSubnavs.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            
            // Toggle panels
            const panels = document.querySelectorAll(".prd-tab-panel");
            panels.forEach(p => {
                if (p.id === targetPanel) {
                    p.classList.add("active");
                } else {
                    p.classList.remove("active");
                }
            });
        });
    });

    // Git & QA tools subnav
    const gitSubnavs = document.querySelectorAll("#git-qa-tab .tabs-subnav .subnav-item");
    gitSubnavs.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetPanel = btn.getAttribute("data-subtarget");
            
            // Toggle buttons
            gitSubnavs.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            
            // Toggle panels
            const panels = document.querySelectorAll(".git-qa-panel");
            panels.forEach(p => {
                if (p.id === targetPanel) {
                    p.classList.add("active");
                } else {
                    p.classList.remove("active");
                }
            });
        });
    });

    // Version Upgrader subnav
    const upgradeSubnavs = document.querySelectorAll(".tabs-subnav .upgrade-subnav-item");
    upgradeSubnavs.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetPanel = btn.getAttribute("data-subtarget");
            
            // Toggle buttons
            upgradeSubnavs.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            
            // Toggle panels
            const panels = document.querySelectorAll(".upgrade-tab-panel");
            panels.forEach(p => {
                if (p.id === targetPanel) {
                    p.classList.add("active");
                } else {
                    p.classList.remove("active");
                }
            });
        });
    });
}

// Global Notification Banners
function showNotification(message, type = "info") {
    const banner = document.getElementById("notification-banner");
    const msgSpan = document.getElementById("notification-message");
    
    banner.className = `notification-banner ${type}`;
    msgSpan.innerText = message;
    
    // Change notification icon
    const icon = banner.querySelector(".notif-icon");
    if (type === "error") {
        icon.setAttribute("data-lucide", "alert-triangle");
    } else if (type === "success") {
        icon.setAttribute("data-lucide", "check-circle");
    } else {
        icon.setAttribute("data-lucide", "info");
    }
    lucide.createIcons();

    // Auto hide after 8 seconds
    setTimeout(hideNotification, 8000);
}

function hideNotification() {
    const banner = document.getElementById("notification-banner");
    banner.classList.add("hidden");
}

// Loading States Helpers
function toggleLoading(panelId, isLoading) {
    const panel = document.getElementById(panelId);
    let overlay = panel.querySelector(".loading-overlay");
    
    if (isLoading) {
        if (!overlay) {
            overlay = document.createElement("div");
            overlay.className = "loading-overlay";
            overlay.innerHTML = `
                <div class="spinner-box">
                    <div class="spinner"></div>
                    <span class="loading-text">Processing request with AI...</span>
                </div>
            `;
            panel.appendChild(overlay);
        }
        overlay.classList.add("active");
    } else if (overlay) {
        overlay.classList.remove("active");
    }
}

// General API Request wrapper
async function apiCall(endpoint, method = "GET", payload = null) {
    const headers = { "Content-Type": "application/json" };
    const config = {
        method,
        headers,
    };
    if (payload) {
        config.body = JSON.stringify(payload);
    }
    
    // Automatically direct API calls to local port 8000 if running from a file or another local dev port
    let url = endpoint;
    const isLocalHost = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
    const isDifferentPort = window.location.port !== "8000" && window.location.port !== "";
    if (window.location.protocol === "file:" || (isLocalHost && isDifferentPort)) {
        url = `http://127.0.0.1:8000${endpoint}`;
    }
    
    try {
        const response = await fetch(url, config);
        if (response.ok) {
            return await response.json();
        } else {
            const errData = await response.json().catch(() => ({}));
            const errMsg = errData.detail || `Server returned error status ${response.status}`;
            throw new Error(errMsg);
        }
    } catch (e) {
        console.error("API Call error:", e);
        throw e;
    }
}

// Connection Diagnostic checks
async function runConnectionDiagnostics() {
    const testBtn = document.getElementById("diag-test-btn");
    if (testBtn) testBtn.disabled = true;
    
    const statusItems = document.querySelectorAll("#diagnostics-list .config-status-item");
    statusItems.forEach(item => {
        item.className = "config-status-item loading";
        item.querySelector(".config-badge").innerText = "checking";
    });

    try {
        // Fetch health config check
        const data = await apiCall("/api/health");
        
        // Update dashboard status rows
        updateStatusBadge("diag-llm", data.sarvam_api_configured || data.claude_api_configured || data.gemini_api_configured || data.groq_api_configured ? "active" : "inactive", data.sarvam_api_configured ? "Sarvam" : (data.claude_api_configured ? "Claude" : (data.gemini_api_configured ? "Gemini" : (data.groq_api_configured ? "Groq" : "Not Configured"))));
        updateStatusBadge("diag-jira", data.jira_configured ? "active" : "inactive", data.jira_configured ? "Configured" : "Dry-Run Mode");
        updateStatusBadge("diag-notion", data.notion_configured ? "active" : "inactive", data.notion_configured ? "Configured" : "Dry-Run Mode");
        updateStatusBadge("diag-linear", data.linear_configured ? "active" : "inactive", data.linear_configured ? "Configured" : "Dry-Run Mode");
        updateStatusBadge("diag-slack", data.slack_configured || data.slack_configured === undefined ? "active" : "inactive", "Configured");
        
        // Update sidebar badges
        updateSidebarStatusBadge(0, data.sarvam_api_configured || data.claude_api_configured || data.gemini_api_configured || data.groq_api_configured, data.sarvam_api_configured ? "Sarvam" : (data.claude_api_configured ? "Claude" : (data.gemini_api_configured ? "Gemini" : "Groq")));
        updateSidebarStatusBadge(1, data.jira_configured, data.jira_configured ? "Active" : "Dry-Run");
        updateSidebarStatusBadge(2, data.notion_configured, data.notion_configured ? "Active" : "Dry-Run");
        updateSidebarStatusBadge(3, data.linear_configured, data.linear_configured ? "Active" : "Dry-Run");
        
        showNotification("Connections diagnostics completed successfully.", "success");
    } catch (err) {
        showNotification(`Failed to scan backend statuses: ${err.message}`, "error");
        statusItems.forEach(item => {
            item.className = "config-status-item inactive";
            item.querySelector(".config-badge").innerText = "failed";
        });
    } finally {
        if (testBtn) testBtn.disabled = false;
    }
}

document.getElementById("check-connection-btn").addEventListener("click", runConnectionDiagnostics);
document.getElementById("diag-test-btn").addEventListener("click", runConnectionDiagnostics);

function updateStatusBadge(id, state, text) {
    const el = document.getElementById(id);
    if (!el) return;
    el.className = `badge ${state === "active" ? "success" : "warning"}`;
    el.innerText = text;
}

function updateSidebarStatusBadge(index, isActive, text) {
    const list = document.getElementById("diagnostics-list");
    if (!list) return;
    const items = list.children;
    if (items[index]) {
        items[index].className = `config-status-item ${isActive ? "active" : "inactive"}`;
        items[index].querySelector(".config-badge").innerText = text;
    }
}

// Dynamic input lists builders
function addFeedbackInputRow() {
    const container = document.getElementById("feedback-items-container");
    const row = document.createElement("div");
    row.className = "dynamic-input-row mt-0-5";
    row.innerHTML = `
        <textarea class="feedback-item-input" placeholder="Paste user ticket comment or review here..." rows="3" required></textarea>
        <button type="button" class="icon-btn delete-row-btn" onclick="removeInputRow(this)">
            <i data-lucide="trash-2"></i>
        </button>
    `;
    container.appendChild(row);
    lucide.createIcons();
}

function addPrdRequirementRow() {
    const container = document.getElementById("prd-requirements-container");
    const row = document.createElement("div");
    row.className = "dynamic-input-row mt-0-5";
    row.innerHTML = `
        <input type="text" class="prd-req-input" placeholder="e.g. Exported file should download directly" required>
        <button type="button" class="icon-btn delete-row-btn" onclick="removeInputRow(this)">
            <i data-lucide="trash-2"></i>
        </button>
    `;
    container.appendChild(row);
    lucide.createIcons();
}

function addPrCriteriaRow() {
    const container = document.getElementById("pr-criteria-container");
    const row = document.createElement("div");
    row.className = "dynamic-input-row mt-0-5";
    row.innerHTML = `
        <input type="text" class="pr-crit-input" placeholder="Acceptance criteria check item" required>
        <button type="button" class="icon-btn delete-row-btn" onclick="removeInputRow(this)">
            <i data-lucide="trash-2"></i>
        </button>
    `;
    container.appendChild(row);
    lucide.createIcons();
}

function addQaSpecRow() {
    const container = document.getElementById("qa-specs-container");
    const row = document.createElement("div");
    row.className = "dynamic-input-row mt-0-5";
    row.innerHTML = `
        <input type="text" class="qa-spec-input" placeholder="Specification feature capability expected" required>
        <button type="button" class="icon-btn delete-row-btn" onclick="removeInputRow(this)">
            <i data-lucide="trash-2"></i>
        </button>
    `;
    container.appendChild(row);
    lucide.createIcons();
}

function removeInputRow(btn) {
    const row = btn.parentElement;
    const container = row.parentElement;
    if (container.children.length > 1) {
        container.removeChild(row);
    } else {
        showNotification("You must maintain at least one input field.", "error");
    }
}

// FEEDBACK ANALYZER FLOW
document.getElementById("feedback-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    toggleLoading("feedback-output", true);
    
    // Ingest inputs
    const context = document.getElementById("feedback-context").value;
    const instructions = document.getElementById("feedback-instructions").value;
    
    const textareas = document.querySelectorAll(".feedback-item-input");
    const feedback_items = Array.from(textareas).map(t => t.value).filter(val => val.trim() !== "");
    
    const payload = {
        feedback_items,
        company_context: context,
        instructions: instructions || null
    };

    try {
        const data = await apiCall("/api/analyze-feedback", "POST", payload);
        
        // Update views
        document.getElementById("feedback-total-processed").innerText = `${data.total_items_processed || feedback_items.length} Processed`;
        
        // Takeaways
        const takeawaysList = document.getElementById("feedback-takeaways");
        takeawaysList.innerHTML = "";
        data.key_takeaways.forEach(t => {
            const li = document.createElement("li");
            li.innerText = t;
            takeawaysList.appendChild(li);
        });
        
        // Clusters list
        const clustersList = document.getElementById("feedback-clusters-list");
        clustersList.innerHTML = "";
        data.clusters.forEach(c => {
            const card = document.createElement("div");
            card.className = "cluster-card";
            
            const badgeTypeClass = c.type.toLowerCase().includes("bug") ? "bug" : (c.type.toLowerCase().includes("request") ? "req" : "improve");
            const urgencyClass = c.urgency.toLowerCase() === "high" ? "danger" : (c.urgency.toLowerCase() === "medium" ? "warning" : "success");
            
            // Associated Quotes
            let quotesHtml = "";
            if (c.associated_quotes && c.associated_quotes.length > 0) {
                quotesHtml = `
                    <div class="quotes-container">
                        <p>"${c.associated_quotes[0]}"</p>
                    </div>
                `;
            }

            card.innerHTML = `
                <div class="cluster-card-header">
                    <h5>${c.theme}</h5>
                    <div class="badge-row">
                        <span class="theme-badge ${badgeTypeClass}">${c.type}</span>
                        <span class="badge ${urgencyClass}">${c.urgency}</span>
                        <span class="badge secondary">Impact ${c.impact_score}/10</span>
                    </div>
                </div>
                <p class="cluster-summary">${c.summary}</p>
                ${quotesHtml}
                <div class="action-bar">
                    <span class="recommendation-text"><strong>Recommendation:</strong> ${c.recommended_action}</span>
                    <button class="btn primary text-sm" onclick="sendFeedbackRecommendationToPRD('${c.theme}', '${c.recommended_action}')">
                        Draft PRD <i data-lucide="arrow-right" style="width:12px; height:12px"></i>
                    </button>
                </div>
            `;
            clustersList.appendChild(card);
        });
        
        // Reveal output
        document.querySelector("#feedback-output .output-placeholder").classList.add("hidden");
        document.querySelector("#feedback-output .output-content").classList.remove("hidden");
        showNotification("Feedback analysis clusters retrieved successfully.", "success");
    } catch (err) {
        showNotification(`Feedback analysis failed: ${err.message}`, "error");
    } finally {
        toggleLoading("feedback-output", false);
        lucide.createIcons();
    }
});

function sendFeedbackRecommendationToPRD(theme, action) {
    const conceptText = `Theme: ${theme}\nRecommended Action: ${action}\n\nPlease implement this feature solution fully.`;
    document.getElementById("prd-concept").value = conceptText;
    
    // Clear dynamic requirement checklists, add placeholder
    const container = document.getElementById("prd-requirements-container");
    container.innerHTML = `
        <div class="dynamic-input-row">
            <input type="text" class="prd-req-input" placeholder="Requirement description..." value="Solve issues reported regarding ${theme.toLowerCase()}" required>
            <button type="button" class="icon-btn delete-row-btn" onclick="removeInputRow(this)">
                <i data-lucide="trash-2"></i>
            </button>
        </div>
    `;
    
    switchTab("prd-tab");
    showNotification("Feedback cluster recommendation loaded into PRD Generator.", "info");
}

// PRD GENERATOR FLOW
document.getElementById("prd-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    toggleLoading("prd-output", true);
    
    const concept = document.getElementById("prd-concept").value;
    const audience = document.getElementById("prd-audience").value;
    const objectives = document.getElementById("prd-objectives").value;
    const instructions = document.getElementById("prd-instructions").value;
    
    const reqInputs = document.querySelectorAll(".prd-req-input");
    const key_requirements = Array.from(reqInputs).map(r => r.value).filter(val => val.trim() !== "");
    
    const payload = {
        feature_idea: concept,
        target_audience: audience || null,
        business_objectives: objectives || null,
        key_requirements: key_requirements.length > 0 ? key_requirements : null,
        instructions: instructions || null
    };

    try {
        const data = await apiCall("/api/generate-prd", "POST", payload);
        
        currentPrdTitle = data.title;
        currentPrdMarkdown = data.full_markdown;
        
        // Update output UI
        document.getElementById("prd-output-title").innerText = data.title;
        
        // Render markdown preview
        const renderContainer = document.getElementById("prd-preview");
        renderContainer.innerHTML = marked.parse(data.full_markdown);
        
        // Raw code panel
        const codeElement = document.getElementById("prd-raw-code");
        codeElement.innerText = data.full_markdown;
        Prism.highlightElement(codeElement);
        
        // Pre-fill requirements checklist in PR audit and feature QA tab
        prefillGitQATemplates(data.acceptance_criteria);

        // Reveal view
        document.querySelector("#prd-output .output-placeholder").classList.add("hidden");
        document.querySelector("#prd-output .output-content").classList.remove("hidden");
        
        showNotification(`PRD Draft for "${data.title}" generated successfully.`, "success");
    } catch (err) {
        showNotification(`PRD generation failed: ${err.message}`, "error");
    } finally {
        toggleLoading("prd-output", false);
        lucide.createIcons();
    }
});

function copyPrdMarkdown() {
    if (!currentPrdMarkdown) return;
    navigator.clipboard.writeText(currentPrdMarkdown).then(() => {
        showNotification("PRD Markdown copied to clipboard.", "success");
    }).catch(err => {
        showNotification("Clipboard copy failed.", "error");
    });
}

// Export PRD to Notion
document.getElementById("export-notion-btn").addEventListener("click", async () => {
    if (!currentPrdMarkdown) return;
    
    const origBtn = document.getElementById("export-notion-btn");
    origBtn.disabled = true;
    origBtn.innerHTML = `<i data-lucide="refresh-cw" class="animate-spin"></i> Exporting...`;
    lucide.createIcons();
    
    try {
        const payload = {
            title: currentPrdTitle,
            content_markdown: currentPrdMarkdown
        };
        const data = await apiCall("/api/export-notion", "POST", payload);
        if (data.success) {
            showNotification(`Notion Sync: ${data.message}. Page: ${data.page_url}`, "success");
            window.open(data.page_url, "_blank");
        } else {
            showNotification(`Notion Export warning: ${data.message}`, "warning");
        }
    } catch (err) {
        showNotification(`Notion export failed: ${err.message}`, "error");
    } finally {
        origBtn.disabled = false;
        origBtn.innerHTML = `<i data-lucide="external-link"></i> Export to Notion`;
        lucide.createIcons();
    }
});

function sendPrdToFeasibility() {
    if (!currentPrdMarkdown) return;
    document.getElementById("feasibility-prd").value = currentPrdMarkdown;
    switchTab("feasibility-tab");
    showNotification("Generated PRD loaded into Feasibility Analyzer.", "info");
}

function prefillGitQATemplates(criteriaList) {
    if (!criteriaList || criteriaList.length === 0) return;
    
    // Fill Git PR auditor checklist
    const prContainer = document.getElementById("pr-criteria-container");
    prContainer.innerHTML = "";
    criteriaList.forEach(crit => {
        const row = document.createElement("div");
        row.className = "dynamic-input-row mt-0-5";
        row.innerHTML = `
            <input type="text" class="pr-crit-input" placeholder="Criteria" value="${crit}" required>
            <button type="button" class="icon-btn delete-row-btn" onclick="removeInputRow(this)">
                <i data-lucide="trash-2"></i>
            </button>
        `;
        prContainer.appendChild(row);
    });

    // Fill Feature QA checklist
    const qaContainer = document.getElementById("qa-specs-container");
    qaContainer.innerHTML = "";
    criteriaList.forEach(crit => {
        const row = document.createElement("div");
        row.className = "dynamic-input-row mt-0-5";
        row.innerHTML = `
            <input type="text" class="qa-spec-input" placeholder="Spec" value="${crit}" required>
            <button type="button" class="icon-btn delete-row-btn" onclick="removeInputRow(this)">
                <i data-lucide="trash-2"></i>
            </button>
        `;
        qaContainer.appendChild(row);
    });
    
    // Fill version upgrader previous PRD
    document.getElementById("upgrade-prev-prd").value = currentPrdMarkdown;
}

// FEASIBILITY SCANNER FLOW
document.getElementById("feasibility-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    toggleLoading("feasibility-output", true);
    
    const prd = document.getElementById("feasibility-prd").value;
    const repo = document.getElementById("feasibility-repo").value;
    const instructions = document.getElementById("feasibility-instructions").value;
    
    const payload = {
        prd_content: prd,
        repo_path: repo || null,
        instructions: instructions || null
    };

    try {
        const data = await apiCall("/api/analyze-feasibility", "POST", payload);
        currentFeasibilityReport = data;
        
        // Populate KPIs
        const compBadge = document.getElementById("feas-complexity");
        compBadge.className = `complexity-badge ${data.complexity.toLowerCase()}`;
        compBadge.innerText = data.complexity;
        
        document.getElementById("feas-complexity-rationale").innerText = data.complexity_rationale;
        document.getElementById("feas-effort").innerText = `${data.effort_estimate_hours} hrs`;
        document.getElementById("feas-dependencies-count").innerText = data.new_dependencies.length;
        document.getElementById("feas-files-impacted").innerText = data.architectural_impact.length;
        
        document.getElementById("feas-summary-text").innerText = data.summary;
        
        // Render File Impacts
        const filesContainer = document.getElementById("feas-files-list");
        filesContainer.innerHTML = "";
        if (data.architectural_impact && data.architectural_impact.length > 0) {
            data.architectural_impact.forEach(file => {
                const row = document.createElement("div");
                row.className = "file-impact-item";
                const actClass = file.action.toLowerCase();
                
                row.innerHTML = `
                    <span class="action-tag ${actClass}">${file.action}</span>
                    <div class="file-impact-details">
                        <h6>${file.file_path}</h6>
                        <p>${file.description}</p>
                    </div>
                `;
                filesContainer.appendChild(row);
            });
        } else {
            filesContainer.innerHTML = `<p class="help-text">No direct file changes identified.</p>`;
        }
        
        // Render Risks
        const risksTable = document.getElementById("feas-risks-table");
        risksTable.innerHTML = "";
        if (data.technical_risks && data.technical_risks.length > 0) {
            data.technical_risks.forEach(risk => {
                const tr = document.createElement("tr");
                const impactClass = risk.impact.toLowerCase() === "high" ? "danger" : (risk.impact.toLowerCase() === "medium" ? "warning" : "success");
                tr.innerHTML = `
                    <td><strong>${risk.risk}</strong></td>
                    <td><span class="badge ${impactClass}">${risk.impact}</span></td>
                    <td>${risk.mitigation}</td>
                `;
                risksTable.appendChild(tr);
            });
        } else {
            risksTable.innerHTML = `<tr><td colspan="3" class="text-center help-text">No technical risks identified.</td></tr>`;
        }
        
        // Reveal outputs
        document.querySelector("#feasibility-output .output-placeholder").classList.add("hidden");
        document.querySelector("#feasibility-output .output-content").classList.remove("hidden");
        
        showNotification("Feasibility scan completed successfully.", "success");
    } catch (err) {
        showNotification(`Feasibility scanner failed: ${err.message}`, "error");
    } finally {
        toggleLoading("feasibility-output", false);
        lucide.createIcons();
    }
});

function sendToSprintPlanner() {
    if (!currentPrdMarkdown) {
        const prdText = document.getElementById("feasibility-prd").value;
        currentPrdMarkdown = prdText;
    }
    
    document.getElementById("sprint-prd").value = currentPrdMarkdown;
    
    if (currentFeasibilityReport) {
        document.getElementById("sprint-feasibility-json").value = JSON.stringify(currentFeasibilityReport, null, 2);
    }
    
    switchTab("sprint-tab");
    showNotification("PRD & Feasibility metadata pre-loaded into Sprint Planner.", "info");
}

// SPRINT PLANNING FLOW
document.getElementById("sprint-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    toggleLoading("sprint-output", true);
    
    const prd = document.getElementById("sprint-prd").value;
    const feasJsonText = document.getElementById("sprint-feasibility-json").value;
    const duration = document.getElementById("sprint-duration").value;
    
    let feasibility_report = null;
    if (feasJsonText.trim() !== "") {
        try {
            feasibility_report = JSON.parse(feasJsonText);
        } catch (jsonErr) {
            showNotification("Warning: Invalid Feasibility JSON payload. Proceeding without scanning report.", "warning");
        }
    }
    
    const payload = {
        prd_content: prd,
        feasibility_report,
        sprint_duration_weeks: parseInt(duration)
    };

    try {
        const data = await apiCall("/api/generate-sprint-plan", "POST", payload);
        
        currentSprintGoal = data.sprint_goal;
        currentSprintTickets = data.tickets;
        
        // Populate Goal
        document.getElementById("sprint-goal-statement").innerText = data.sprint_goal;
        document.getElementById("sprint-ticket-count").innerText = data.tickets.length;
        
        // Populate Tickets Cards list
        const ticketsContainer = document.getElementById("sprint-tickets-list");
        ticketsContainer.innerHTML = "";
        
        data.tickets.forEach(ticket => {
            const card = document.createElement("div");
            card.className = "ticket-card";
            
            const priClass = ticket.priority.toLowerCase() === "high" ? "pri-high" : (ticket.priority.toLowerCase() === "medium" ? "pri-med" : "pri-low");
            
            // Build checklist
            let checklistHtml = "";
            if (ticket.acceptance_criteria && ticket.acceptance_criteria.length > 0) {
                const checklistRows = ticket.acceptance_criteria.map(crit => `
                    <div class="criteria-checkbox-item">
                        <input type="checkbox">
                        <span>${crit}</span>
                    </div>
                `).join("");
                
                checklistHtml = `
                    <div class="criteria-list mt-0-5">
                        <h6>Acceptance Criteria Checklist</h6>
                        ${checklistRows}
                    </div>
                `;
            }
            
            // Generate click utility to populate git branch creator
            const branchNameSanitized = `feat-${ticket.id.toLowerCase()}-${ticket.title.toLowerCase().replace(/[^a-z0-9]/g, "-").slice(0, 20)}`;

            card.innerHTML = `
                <div class="ticket-card-header">
                    <div class="ticket-id-title">
                        <span class="ticket-id">${ticket.id}</span>
                        <h5>${ticket.title}</h5>
                    </div>
                    <div class="ticket-meta-badges">
                        <span class="meta-badge pts">${ticket.story_points} pts</span>
                        <span class="meta-badge ${priClass}">${ticket.priority}</span>
                        <span class="meta-badge role">${ticket.assignee_role}</span>
                    </div>
                </div>
                <p class="ticket-desc">${ticket.description}</p>
                ${checklistHtml}
                <div class="flex-row justify-end mt-0-5">
                    <button class="btn secondary text-sm" onclick="stageGitBranchCreator('${branchNameSanitized}')" title="Configure Git Branch">
                        <i data-lucide="git-branch" style="width:12px; height:12px"></i> Stage Branch Creation
                    </button>
                </div>
            `;
            ticketsContainer.appendChild(card);
        });
        
        // Reveal outputs
        document.querySelector("#sprint-output .output-placeholder").classList.add("hidden");
        document.querySelector("#sprint-output .output-content").classList.remove("hidden");
        
        showNotification("Decomposed Agile sprint backlog successfully.", "success");
    } catch (err) {
        showNotification(`Sprint planning failed: ${err.message}`, "error");
    } finally {
        toggleLoading("sprint-output", false);
        lucide.createIcons();
    }
});

function stageGitBranchCreator(branchName) {
    document.getElementById("git-branch-name").value = branchName;
    showNotification(`Branch name "${branchName}" loaded into developer creation utility. Scroll down to deploy.`, "info");
}

// Jira sprint exports
document.getElementById("export-jira-btn").addEventListener("click", async () => {
    if (currentSprintTickets.length === 0) return;
    const btn = document.getElementById("export-jira-btn");
    btn.disabled = true;
    btn.innerHTML = `<i class="animate-spin" data-lucide="refresh-cw"></i> Syncing...`;
    lucide.createIcons();

    try {
        const payload = {
            tickets: currentSprintTickets
        };
        const data = await apiCall("/api/export-jira", "POST", payload);
        if (data.success) {
            let msg = `Jira Cloud: Backlog exported.`;
            if (data.created_issues && data.created_issues.length > 0) {
                msg += ` Primary Ticket URL: ${data.created_issues[0].url}`;
                window.open(data.created_issues[0].url, "_blank");
            }
            showNotification(msg, "success");
        } else {
            showNotification(`Jira Export warning: ${data.message}`, "warning");
        }
    } catch (err) {
        showNotification(`Jira Sync failed: ${err.message}`, "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="trello"></i> Export Jira`;
        lucide.createIcons();
    }
});

// Linear sprint exports
document.getElementById("export-linear-btn").addEventListener("click", async () => {
    if (currentSprintTickets.length === 0) return;
    const btn = document.getElementById("export-linear-btn");
    btn.disabled = true;
    btn.innerHTML = `<i class="animate-spin" data-lucide="refresh-cw"></i> Syncing...`;
    lucide.createIcons();

    try {
        const payload = {
            tickets: currentSprintTickets
        };
        const data = await apiCall("/api/export-linear", "POST", payload);
        if (data.success) {
            let msg = `Linear Board: Backlog exported.`;
            if (data.created_issues && data.created_issues.length > 0) {
                msg += ` Primary Task URL: ${data.created_issues[0].url}`;
                window.open(data.created_issues[0].url, "_blank");
            }
            showNotification(msg, "success");
        } else {
            showNotification(`Linear Export warning: ${data.message}`, "warning");
        }
    } catch (err) {
        showNotification(`Linear Sync failed: ${err.message}`, "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="check-square"></i> Export Linear`;
        lucide.createIcons();
    }
});

// Slack notification exports
document.getElementById("export-slack-btn").addEventListener("click", async () => {
    if (currentSprintTickets.length === 0) return;
    const btn = document.getElementById("export-slack-btn");
    btn.disabled = true;
    btn.innerHTML = `<i class="animate-spin" data-lucide="refresh-cw"></i> Posting...`;
    lucide.createIcons();

    try {
        const payload = {
            sprint_goal: currentSprintGoal,
            tickets: currentSprintTickets,
            custom_message: "Agile backlog created via PM Copilot Dashboard."
        };
        const data = await apiCall("/api/export-slack", "POST", payload);
        if (data.success) {
            showNotification(`Slack Alert: ${data.message}`, "success");
        } else {
            showNotification(`Slack Alert warning: ${data.message}`, "warning");
        }
    } catch (err) {
        showNotification(`Slack Webhook post failed: ${err.message}`, "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="slack"></i> Share on Slack`;
        lucide.createIcons();
    }
});

// Create task Git branches
document.getElementById("create-branch-btn").addEventListener("click", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("create-branch-btn");
    
    const repo_owner = document.getElementById("git-repo-owner").value;
    const repo_name = document.getElementById("git-repo-name").value;
    const branch_name = document.getElementById("git-branch-name").value;
    
    if (!branch_name || branch_name.trim() === "") {
        showNotification("Please select a ticket or write a branch name first.", "error");
        return;
    }
    
    btn.disabled = true;
    btn.innerHTML = `<i class="animate-spin" data-lucide="refresh-cw"></i> Deploying...`;
    lucide.createIcons();
    
    const payload = {
        repo_owner,
        repo_name,
        branch_name,
        base_branch: "main",
        git_provider: "github"
    };

    try {
        const data = await apiCall("/api/create-branch", "POST", payload);
        if (data.success) {
            showNotification(`Git Branch: ${data.message}. URL: ${data.branch_url}`, "success");
            window.open(data.branch_url, "_blank");
        } else {
            showNotification(`Branch warnings: ${data.message}`, "warning");
        }
    } catch (err) {
        showNotification(`Git Branch creation failed: ${err.message}`, "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="git-branch"></i> Create Branch`;
        lucide.createIcons();
    }
});

// DEV COMPLIANCE TAB 1: PR AUDITOR FLOW
document.getElementById("pr-audit-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    toggleLoading("pr-audit-output", true);
    
    const owner = document.getElementById("pr-owner").value;
    const repo = document.getElementById("pr-repo").value;
    const prNum = parseInt(document.getElementById("pr-number").value);
    const provider = document.getElementById("pr-provider").value;
    
    const critInputs = document.querySelectorAll(".pr-crit-input");
    const criteria = Array.from(critInputs).map(c => c.value).filter(val => val.trim() !== "");
    
    const payload = {
        repo_owner: owner,
        repo_name: repo,
        pr_number: prNum,
        acceptance_criteria: criteria,
        git_provider: provider
    };

    try {
        const data = await apiCall("/api/audit-pr", "POST", payload);
        
        // Verdict Badge
        const statusBadge = document.getElementById("pr-status-badge");
        const statusClass = data.status.toLowerCase() === "pass" ? "pass" : (data.status.toLowerCase() === "fail" ? "fail" : "warn");
        statusBadge.className = `compliance-badge ${statusClass}`;
        statusBadge.innerText = data.status;
        
        document.getElementById("pr-summary-text").innerText = data.summary;
        
        // Criteria Checked list
        const itemsContainer = document.getElementById("pr-checked-items-container");
        itemsContainer.innerHTML = "";
        data.criteria_checked.forEach(item => {
            const row = document.createElement("div");
            row.className = "checklist-item-row";
            
            const iconName = item.satisfied ? "check-circle-2" : "x-circle";
            const iconClass = item.satisfied ? "success" : "failed";
            
            row.innerHTML = `
                <i data-lucide="${iconName}" class="${iconClass}"></i>
                <div class="checklist-item-info">
                    <h6>${item.criteria}</h6>
                    <p>${item.evidence}</p>
                </div>
            `;
            itemsContainer.appendChild(row);
        });
        
        // Reveal outputs
        document.querySelector("#pr-audit-output .output-placeholder").classList.add("hidden");
        document.querySelector("#pr-audit-output .output-content").classList.remove("hidden");
        
        showNotification("PR Compliance audit completed successfully.", "success");
    } catch (err) {
        showNotification(`PR Auditor failed: ${err.message}`, "error");
    } finally {
        toggleLoading("pr-audit-output", false);
        lucide.createIcons();
    }
});

// DEV COMPLIANCE TAB 2: FEATURE QA AUDIT FLOW
document.getElementById("feature-qa-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    toggleLoading("feature-qa-output", true);
    
    const repo_path = document.getElementById("qa-repo-path").value;
    const user_query = document.getElementById("qa-query").value;
    
    const specInputs = document.querySelectorAll(".qa-spec-input");
    const feature_specs = Array.from(specInputs).map(s => s.value).filter(val => val.trim() !== "");
    
    const payload = {
        repo_path,
        user_query,
        feature_specs
    };

    try {
        const data = await apiCall("/api/qa-feature", "POST", payload);
        
        // Verdict Badge
        const verdictBadge = document.getElementById("qa-verdict-badge");
        const vClass = data.compliance_status.toLowerCase() === "pass" ? "pass" : (data.compliance_status.toLowerCase() === "fail" ? "fail" : "warn");
        verdictBadge.className = `compliance-badge ${vClass}`;
        verdictBadge.innerText = data.compliance_status;
        
        document.getElementById("qa-answer-text").innerText = data.answer;
        
        // Checked items list
        const itemsContainer = document.getElementById("qa-checked-items-container");
        itemsContainer.innerHTML = "";
        data.checked_items.forEach(item => {
            const row = document.createElement("div");
            row.className = "checklist-item-row";
            
            const iconName = item.status.toLowerCase() === "implemented" ? "check-circle-2" : (item.status.toLowerCase() === "missing" ? "x-circle" : "alert-circle");
            const iconClass = item.status.toLowerCase() === "implemented" ? "success" : (item.status.toLowerCase() === "missing" ? "failed" : "warning");
            
            // Source File references
            let refHtml = "";
            if (item.file_references && item.file_references.length > 0) {
                refHtml = `<span class="references-tag">Ref: ${item.file_references.join(", ")}</span>`;
            }

            row.innerHTML = `
                <i data-lucide="${iconName}" class="${iconClass}"></i>
                <div class="checklist-item-info">
                    <h6>${item.requirement}</h6>
                    <p>${item.details}</p>
                    ${refHtml}
                </div>
            `;
            itemsContainer.appendChild(row);
        });
        
        // Reveal outputs
        document.querySelector("#feature-qa-output .output-placeholder").classList.add("hidden");
        document.querySelector("#feature-qa-output .output-content").classList.remove("hidden");
        
        showNotification("Codebase Feature QA evaluation finished.", "success");
    } catch (err) {
        showNotification(`QA Compliance check failed: ${err.message}`, "error");
    } finally {
        toggleLoading("feature-qa-output", false);
        lucide.createIcons();
    }
});

// DEV COMPLIANCE TAB 3: VERSION UPGRADE FLOW
document.getElementById("upgrade-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    toggleLoading("upgrade-output", true);
    
    const prevPrd = document.getElementById("upgrade-prev-prd").value;
    const upgrade_input = document.getElementById("upgrade-inputs").value;
    const repo_path = document.getElementById("qa-upgrade-path").value;
    
    const payload = {
        previous_prd: prevPrd,
        upgrade_input,
        repo_path: repo_path || null,
        additional_context: []
    };

    try {
        const data = await apiCall("/api/version-upgrade", "POST", payload);
        
        // Complexity badge
        const cBadge = document.getElementById("upgrade-complexity-badge");
        const cClass = data.migration_complexity.toLowerCase() === "high" ? "danger" : (data.migration_complexity.toLowerCase() === "medium" ? "warning" : "success");
        cBadge.className = `complexity-badge ${cClass}`;
        cBadge.innerText = data.migration_complexity;
        
        currentUpgradePrdMarkdown = data.updated_prd;
        
        // Renders upgraded specs markdown
        const prdDiv = document.getElementById("upgrade-prd-rendered");
        prdDiv.innerHTML = marked.parse(data.updated_prd);
        
        // Render Changelog
        const changelist = document.getElementById("upgrade-changelog-list");
        changelist.innerHTML = "";
        data.changelog.forEach(change => {
            const itemDiv = document.createElement("div");
            itemDiv.className = "changelog-item";
            const actClass = change.action.toLowerCase();
            
            itemDiv.innerHTML = `
                <span class="changelog-action ${actClass}">${change.action}</span>
                <div class="changelog-content">
                    <h6>${change.feature}</h6>
                    <p>${change.description}</p>
                </div>
            `;
            changelist.appendChild(itemDiv);
        });
        
        // Render Guide
        const guideDiv = document.getElementById("upgrade-guide");
        guideDiv.innerHTML = marked.parse(data.migration_guide);
        
        // Reveal outputs
        document.querySelector("#upgrade-output .output-placeholder").classList.add("hidden");
        document.querySelector("#upgrade-output .output-content").classList.remove("hidden");
        
        showNotification("Upgraded Version specs draft created.", "success");
    } catch (err) {
        showNotification(`Version upgrader failed: ${err.message}`, "error");
    } finally {
        toggleLoading("upgrade-output", false);
        lucide.createIcons();
    }
});

// Helper utilities to download and copy generated files
function downloadPrd() {
    if (!currentPrdMarkdown) return;
    const blob = new Blob([currentPrdMarkdown], { type: "text/markdown;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    
    // Sanitize title for filename
    const sanitizedTitle = currentPrdTitle.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
    const filename = `${sanitizedTitle || "feature"}-prd.md`;
    
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    showNotification("PRD downloaded successfully.", "success");
}

function copyUpgradePrdMarkdown() {
    if (!currentUpgradePrdMarkdown) return;
    navigator.clipboard.writeText(currentUpgradePrdMarkdown).then(() => {
        showNotification("Upgraded PRD copied to clipboard.", "success");
    }).catch(err => {
        showNotification("Clipboard copy failed.", "error");
    });
}

function downloadUpgradePrd() {
    if (!currentUpgradePrdMarkdown) return;
    const blob = new Blob([currentUpgradePrdMarkdown], { type: "text/markdown;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "upgraded-version-prd.md");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    showNotification("Upgraded Version PRD downloaded successfully.", "success");
}

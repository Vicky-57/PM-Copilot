from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
import os
from app.models.requests import FeasibilityRequest, SprintPlanRequest, PRDGenerationRequest, FeedbackAnalysisRequest, JiraExportRequest, NotionExportRequest, LinearExportRequest, SlackExportRequest, PRAuditRequest, GitBranchRequest, FeatureQARequest, VersionUpgradeRequest
from app.models.responses import FeasibilityResponse, SprintPlanResponse, PRDGenerationResponse, FeedbackAnalysisResponse, JiraExportResponse, NotionExportResponse, LinearExportResponse, SlackExportResponse, PRAuditResponse, GitBranchResponse, FeatureQAResponse, VersionUpgradeResponse
from app.services.feasibility import run_feasibility_analysis
from app.services.planner import run_sprint_planning
from app.services.prd_generator import run_prd_generation
from app.services.feedback_analyzer import run_feedback_analysis
from app.services.jira_service import export_sprint_to_jira
from app.services.notion_service import export_prd_to_notion
from app.services.linear_service import export_sprint_to_linear
from app.services.slack_service import export_to_slack
from app.services.git_service import audit_pull_request, create_git_branch
from app.services.lifecycle_service import run_feature_qa, run_version_upgrade
from app.services.gemini_service import GeminiService
from app.config import settings

app = FastAPI(
    title="AI Product Manager Copilot Backend",
    description="Backend-only service providing AI Technical Feasibility Analysis and Sprint Planning task breakdown.",
    version="1.0.0"
)

# Enable CORS for local development (allowing React/Next.js frontends to call the API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """Redirect root to the UI."""
    return RedirectResponse(url="/ui")

@app.get("/api/health")
def health_check():
    """Health check endpoint and general diagnostic details."""
    has_claude = bool(settings.CLAUDE_API_KEY)
    has_gemini = bool(settings.GEMINI_API_KEY)
    has_groq = bool(settings.GROQ_API_KEY)
    has_jira = bool(settings.JIRA_URL and settings.JIRA_EMAIL and settings.JIRA_API_TOKEN)
    has_notion = bool(settings.NOTION_API_KEY)
    has_linear = bool(settings.LINEAR_API_KEY and settings.LINEAR_TEAM_ID)
    return {
        "status": "online",
        "service": "AI Product Manager Copilot Backend",
        "claude_api_configured": has_claude,
        "groq_api_configured": has_groq,
        "gemini_api_configured": has_gemini,
        "jira_configured": has_jira,
        "notion_configured": has_notion,
        "linear_configured": has_linear,
        "docs_url": "/docs"
    }

@app.get("/api/test-connection")
def test_connection():
    """Diagnostic check to verify that the configured API keys are working."""
    if not settings.CLAUDE_API_KEY and not settings.GROQ_API_KEY and not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="No API keys are set. Please configure CLAUDE_API_KEY, GEMINI_API_KEY, or GROQ_API_KEY in your .env file."
        )
    
    is_connected = GeminiService.test_connection()
    if settings.CLAUDE_API_KEY:
        provider = "Claude (Anthropic)"
    elif settings.GROQ_API_KEY:
        provider = "Groq"
    else:
        provider = "Gemini"
    
    if is_connected:
        return {"status": "success", "message": f"Successfully connected to the {provider} API."}
    else:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to connect to the {provider} API. Check your network or credentials."
        )


@app.post("/api/analyze-feasibility", response_model=FeasibilityResponse)
def analyze_feasibility(request: FeasibilityRequest):
    """
    Parses a PRD and scans the provided codebase directory structure.
    Generates a technical feasibility report containing complexity, risks, file impacts, and estimates.
    """
    return run_feasibility_analysis(
        prd_content=request.prd_content,
        repo_path=request.repo_path,
        instructions=request.instructions
    )

@app.post("/api/generate-sprint-plan", response_model=SprintPlanResponse)
def generate_sprint_plan(request: SprintPlanRequest):
    """
    Parses a PRD and (optionally) the structured feasibility report to
    decompose the implementation work into structured sprint tickets.
    """
    return run_sprint_planning(
        prd_content=request.prd_content,
        feasibility_report=request.feasibility_report,
        sprint_duration_weeks=request.sprint_duration_weeks or 2
    )

@app.post("/api/generate-prd", response_model=PRDGenerationResponse)
def generate_prd(request: PRDGenerationRequest):
    """
    Ingests feature concepts, target user audience, business objectives and guidelines,
    and drafts a structured and copy-paste ready Product Requirement Document (PRD).
    """
    return run_prd_generation(
        feature_idea=request.feature_idea,
        target_audience=request.target_audience,
        business_objectives=request.business_objectives,
        key_requirements=request.key_requirements,
        instructions=request.instructions
    )

@app.post("/api/analyze-feedback", response_model=FeedbackAnalysisResponse)
def analyze_feedback(request: FeedbackAnalysisRequest):
    """
    Ingests customer feedback, support logs, review snippets, or survey answers.
    Aggregates them into categorized themes/clusters, assesses sentiment and urgency,
    and returns suggested product/PM next steps.
    """
    return run_feedback_analysis(
        feedback_items=request.feedback_items,
        company_context=request.company_context,
        instructions=request.instructions
    )

@app.post("/api/export-jira", response_model=JiraExportResponse)
def export_jira(request: JiraExportRequest):
    """
    Exports a list of sprint plan tickets directly to your Jira Cloud backlog.
    Runs in Dry-Run simulation mode if Jira configurations are not set in the .env file.
    """
    return export_sprint_to_jira(
        tickets=request.tickets,
        project_key=request.project_key
    )

@app.post("/api/export-notion", response_model=NotionExportResponse)
def export_notion(request: NotionExportRequest):
    """
    Exports a generated PRD document directly to your Notion workspace as a page.
    Runs in Dry-Run simulation mode if Notion credentials are not configured in the .env file.
    """
    return export_prd_to_notion(
        title=request.title,
        content_markdown=request.content_markdown,
        parent_page_id=request.parent_page_id
    )

@app.post("/api/export-linear", response_model=LinearExportResponse)
def export_linear(request: LinearExportRequest):
    """
    Exports a list of sprint plan tickets directly to your Linear team board.
    Runs in Dry-Run simulation mode if Linear configurations are not set in the .env file.
    """
    return export_sprint_to_linear(
        tickets=request.tickets,
        team_id=request.team_id
    )

@app.post("/api/export-slack", response_model=SlackExportResponse)
def export_slack(request: SlackExportRequest):
    """
    Posts a sprint summary and ticket status alerts directly to a Slack channel.
    Runs in Dry-Run simulation mode if Slack credentials are not configured in the .env file.
    """
    return export_to_slack(
        sprint_goal=request.sprint_goal,
        tickets=request.tickets,
        custom_message=request.custom_message,
        webhook_url=request.webhook_url
    )

@app.post("/api/audit-pr", response_model=PRAuditResponse)
def audit_pr(request: PRAuditRequest):
    """
    Fetches remote Pull Request file diffs and runs a semantic validation audit
    against the sprint ticket's Acceptance Criteria to confirm code compliance.
    Runs in Dry-Run simulation mode if access tokens are not configured in the .env file.
    """
    return audit_pull_request(
        repo_owner=request.repo_owner,
        repo_name=request.repo_name,
        pr_number=request.pr_number,
        acceptance_criteria=request.acceptance_criteria,
        git_provider=request.git_provider
    )

@app.post("/api/create-branch", response_model=GitBranchResponse)
def create_branch(request: GitBranchRequest):
    """
    Creates a development task branch directly on the remote GitHub or GitLab repository.
    Runs in Dry-Run simulation mode if access tokens are not configured in the .env file.
    """
    return create_git_branch(
        repo_owner=request.repo_owner,
        repo_name=request.repo_name,
        branch_name=request.branch_name,
        base_branch=request.base_branch,
        git_provider=request.git_provider
    )

@app.post("/api/qa-feature", response_model=FeatureQAResponse)
def qa_feature(request: FeatureQARequest):
    """
    Evaluates whether the codebase conforms to launch specs/benefits by asking AI QA compliance questions.
    Runs in Dry-Run simulation mode if the provided repo_path is missing or not a valid directory.
    """
    return run_feature_qa(
        feature_specs=request.feature_specs,
        repo_path=request.repo_path,
        user_query=request.user_query,
        instructions=request.instructions
    )

@app.post("/api/version-upgrade", response_model=VersionUpgradeResponse)
def version_upgrade(request: VersionUpgradeRequest):
    """
    Ingests previous version PRD and context (charts/logs/metrics) alongside upgrade goals to draft
    the next upgraded Version PRD, transition changelog, and developer migration guide without redundancies.
    """
    return run_version_upgrade(
        previous_prd=request.previous_prd,
        upgrade_input=request.upgrade_input,
        repo_path=request.repo_path,
        additional_context=request.additional_context
    )

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

@app.get("/ui", response_class=HTMLResponse)
@app.get("/ui/", response_class=HTMLResponse)
def get_ui():
    """Serves the main single-page UI."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="UI files not found. Ensure frontend/index.html is created.")
    return FileResponse(index_path, media_type="text/html")

@app.get("/ui/style.css")
def get_style():
    """Serves the UI stylesheet."""
    style_path = os.path.join(FRONTEND_DIR, "style.css")
    if not os.path.exists(style_path):
        raise HTTPException(status_code=404, detail="style.css not found.")
    return FileResponse(style_path, media_type="text/css")

@app.get("/ui/app.js")
def get_app():
    """Serves the UI application logic."""
    app_path = os.path.join(FRONTEND_DIR, "app.js")
    if not os.path.exists(app_path):
        raise HTTPException(status_code=404, detail="app.js not found.")
    return FileResponse(app_path, media_type="application/javascript")

if __name__ == "__main__":
    import uvicorn
    # Allow uvicorn options to be loaded from config
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )

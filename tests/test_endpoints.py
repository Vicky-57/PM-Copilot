import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.models.responses import FeasibilityResponse, SprintPlanResponse, PRDGenerationResponse, FeedbackAnalysisResponse, FeedbackCluster, JiraExportResponse, JiraIssueInfo, NotionExportResponse, FileImpact, TechnicalRisk, SprintTicket, LinearExportResponse, LinearIssueInfo, SlackExportResponse, PRAuditResponse, PRAuditCriterion, GitBranchResponse, FeatureQAResponse, QAEvidence, VersionUpgradeResponse, UpgradeChangelogItem
from app.services.linear_service import export_sprint_to_linear
from app.services.slack_service import export_to_slack
from app.services.git_service import audit_pull_request, create_git_branch
from app.services.lifecycle_service import run_feature_qa, run_version_upgrade
from app.config import settings

client = TestClient(app)

def test_health_check():
    """Verify that root endpoint redirects to UI."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/ui"

def test_api_health_check():
    """Verify that /api/health endpoint responds successfully."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "gemini_api_configured" in data
    assert "jira_configured" in data
    assert "notion_configured" in data
    assert "linear_configured" in data

def test_analyze_feasibility_invalid_request():
    """Verify endpoint rejects requests with missing or invalid fields."""
    response = client.post("/api/analyze-feasibility", json={})
    assert response.status_code == 422  # validation error

@patch("app.main.run_feasibility_analysis")
def test_analyze_feasibility_endpoint(mock_feasibility):
    """Verify `/api/analyze-feasibility` correctly delegates and returns expected response structure."""
    expected_data = FeasibilityResponse(
        complexity="Medium",
        complexity_rationale="Requires API integration",
        architectural_impact=[
            FileImpact(file_path="app/main.py", action="MODIFY", description="Add endpoint")
        ],
        technical_risks=[
            TechnicalRisk(risk="Timeout", impact="Medium", mitigation="Set timeouts")
        ],
        new_dependencies=["httpx"],
        effort_estimate_hours=16,
        summary="Feasibility is medium due to external dependencies."
    )
    mock_feasibility.return_value = expected_data
    
    payload = {
        "prd_content": "### Feature X\nImplement an external API client.",
        "repo_path": None
    }
    
    response = client.post("/api/analyze-feasibility", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["complexity"] == "Medium"
    assert res_json["effort_estimate_hours"] == 16
    assert len(res_json["architectural_impact"]) == 1

@patch("app.main.run_sprint_planning")
def test_generate_sprint_plan_endpoint(mock_planner):
    """Verify `/api/generate-sprint-plan` correctly delegates and returns expected response structure."""
    expected_plan = SprintPlanResponse(
        sprint_goal="Build external client integration",
        tickets=[
            SprintTicket(
                id="T-1",
                title="Create client module",
                description="Write http requester class",
                acceptance_criteria=["Status code is 200"],
                story_points=3,
                priority="High",
                assignee_role="Backend"
            )
        ]
    )
    mock_planner.return_value = expected_plan
    
    payload = {
        "prd_content": "### Feature X\nImplement an external API client.",
        "sprint_duration_weeks": 2
    }
    
    response = client.post("/api/generate-sprint-plan", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["sprint_goal"] == "Build external client integration"
    assert len(res_json["tickets"]) == 1
    assert res_json["tickets"][0]["id"] == "T-1"

@patch("app.main.run_prd_generation")
def test_generate_prd_endpoint(mock_prd_generator):
    """Verify `/api/generate-prd` correctly delegates and returns expected response structure."""
    expected_prd = PRDGenerationResponse(
        title="External API Client",
        executive_summary="Build external client to fetch resources.",
        objectives=["Ensure low latency fetching"],
        user_personas=["Integration Developer"],
        functional_requirements=["Retry logic on HTTP 5xx errors"],
        user_stories=["As a dev, I want a retry loop"],
        acceptance_criteria=["Status code is 200 after retry"],
        out_of_scope=["Webhooks", "Billing configuration"],
        edge_cases=["API token expiration"],
        full_markdown="# External API Client\nThis is a mock markdown PRD."
    )
    mock_prd_generator.return_value = expected_prd

    payload = {
        "feature_idea": "Build a robust external API client with retry handling.",
        "target_audience": "Integration Developers",
        "business_objectives": "Reduce API timeout issues by 20%"
    }

    response = client.post("/api/generate-prd", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["title"] == "External API Client"
    assert "mock markdown" in res_json["full_markdown"]

@patch("app.main.run_feedback_analysis")
def test_analyze_feedback_endpoint(mock_feedback):
    """Verify `/api/analyze-feedback` correctly delegates and returns expected response structure."""
    expected_feedback = FeedbackAnalysisResponse(
        total_items_processed=2,
        clusters=[
            FeedbackCluster(
                theme="CSV Timeout",
                type="Bug",
                sentiment="Frustrated",
                urgency="High",
                impact_score=8,
                summary="CSV download crashes on large datasets.",
                associated_quotes=["App crashes when export exceeds 5k rows"],
                recommended_action="Create a PRD to move CSV export to background execution."
            )
        ],
        key_takeaways=["CSV export is the primary stability concern."]
    )
    mock_feedback.return_value = expected_feedback

    payload = {
        "feedback_items": [
            "App crashes when export exceeds 5k rows",
            "Please fix the CSV export speed, it hangs forever"
        ],
        "company_context": "SaaS analytics tool"
    }

    response = client.post("/api/analyze-feedback", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["total_items_processed"] == 2
    assert len(res_json["clusters"]) == 1
    assert res_json["clusters"][0]["theme"] == "CSV Timeout"

@patch("app.main.export_sprint_to_jira")
def test_export_jira_endpoint(mock_jira_export):
    """Verify `/api/export-jira` correctly delegates and returns expected response structure."""
    expected_export = JiraExportResponse(
        success=True,
        message="Simulated mock success",
        created_issues=[
            JiraIssueInfo(
                id="MOCK-1",
                key="PROJ-101",
                url="https://mock-company.atlassian.net/browse/PROJ-101"
            )
        ]
    )
    mock_jira_export.return_value = expected_export

    payload = {
        "tickets": [
            {
                "id": "PROJ-1",
                "title": "Create exporter utility",
                "description": "Background compiler logic",
                "acceptance_criteria": ["CSV compiles"],
                "story_points": 5,
                "priority": "High",
                "assignee_role": "Backend"
            }
        ],
        "project_key": "PROJ"
    }

    response = client.post("/api/export-jira", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert len(res_json["created_issues"]) == 1
    assert res_json["created_issues"][0]["key"] == "PROJ-101"

@patch("app.main.export_prd_to_notion")
def test_export_notion_endpoint(mock_notion_export):
    """Verify `/api/export-notion` correctly delegates and returns expected response structure."""
    expected_export = NotionExportResponse(
        success=True,
        message="Simulated mock Notion success",
        page_url="https://notion.so/mock-page-id",
        page_id="mock-page-id"
    )
    mock_notion_export.return_value = expected_export

    payload = {
        "title": "Background CSV Export PRD",
        "content_markdown": "# Background CSV Export\nThis is a mock markdown PRD.",
        "parent_page_id": "mock-parent-id"
    }

    response = client.post("/api/export-notion", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["page_url"] == "https://notion.so/mock-page-id"
    assert res_json["page_id"] == "mock-page-id"

@patch("app.main.export_sprint_to_linear")
def test_export_linear_endpoint(mock_linear_export):
    """Verify `/api/export-linear` correctly delegates and returns expected response structure."""
    expected_export = LinearExportResponse(
        success=True,
        message="Simulated mock Linear success",
        created_issues=[
            LinearIssueInfo(
                id="simulated-linear-id-MOCK-101",
                key="MOCK-101",
                url="https://linear.app/issue/MOCK-101"
            )
        ]
    )
    mock_linear_export.return_value = expected_export

    payload = {
        "tickets": [
            {
                "id": "PROJ-1",
                "title": "Create exporter utility",
                "description": "Background compiler logic",
                "acceptance_criteria": ["CSV compiles"],
                "story_points": 5,
                "priority": "High",
                "assignee_role": "Backend"
            }
        ],
        "team_id": "mock-team-id"
    }

    response = client.post("/api/export-linear", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert len(res_json["created_issues"]) == 1
    assert res_json["created_issues"][0]["key"] == "MOCK-101"
    assert res_json["created_issues"][0]["url"] == "https://linear.app/issue/MOCK-101"

def test_linear_service_dry_run():
    """Verify that export_sprint_to_linear falls back to Dry-Run Mode when credentials are not configured."""
    old_key = settings.LINEAR_API_KEY
    old_team = settings.LINEAR_TEAM_ID
    try:
        settings.LINEAR_API_KEY = ""
        settings.LINEAR_TEAM_ID = ""
        
        tickets = [
            SprintTicket(
                id="PROJ-1",
                title="Create exporter utility",
                description="Background compiler logic",
                acceptance_criteria=["CSV compiles"],
                story_points=5,
                priority="High",
                assignee_role="Backend"
            )
        ]
        
        response = export_sprint_to_linear(tickets)
        assert response.success is True
        assert "Dry-Run Mode" in response.message
        assert len(response.created_issues) == 1
        assert response.created_issues[0].key == "MOCK-101"
        assert response.created_issues[0].url == "https://linear.app/issue/MOCK-101"
    finally:
        settings.LINEAR_API_KEY = old_key
        settings.LINEAR_TEAM_ID = old_team

@patch("requests.post")
def test_linear_service_live_mock(mock_post):
    """Verify that export_sprint_to_linear hits the Linear GraphQL endpoint correctly when configured."""
    old_key = settings.LINEAR_API_KEY
    old_team = settings.LINEAR_TEAM_ID
    try:
        settings.LINEAR_API_KEY = "lin_api_test_key"
        settings.LINEAR_TEAM_ID = "test-team-uuid"
        
        # Mock successful GraphQL response from Linear
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "issueCreate": {
                    "success": True,
                    "issue": {
                        "id": "real-uuid-1",
                        "identifier": "TST-1",
                        "url": "https://linear.app/issue/TST-1"
                    }
                }
            }
        }
        
        tickets = [
            SprintTicket(
                id="PROJ-1",
                title="Create exporter utility",
                description="Background compiler logic",
                acceptance_criteria=["CSV compiles"],
                story_points=5,
                priority="High",
                assignee_role="Backend"
            )
        ]
        
        response = export_sprint_to_linear(tickets)
        assert response.success is True
        assert "Successfully exported 1 tickets to Linear Team UUID" in response.message
        assert len(response.created_issues) == 1
        assert response.created_issues[0].key == "TST-1"
        assert response.created_issues[0].id == "real-uuid-1"
        
        # Verify mock requests was called with expected arguments
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.linear.app/graphql"
        assert kwargs["headers"]["Authorization"] == "lin_api_test_key"
        assert kwargs["json"]["variables"]["input"]["teamId"] == "test-team-uuid"
    finally:
        settings.LINEAR_API_KEY = old_key
        settings.LINEAR_TEAM_ID = old_team

# --- Slack Endpoint & Service Tests ---

@patch("app.main.export_to_slack")
def test_export_slack_endpoint(mock_slack_export):
    """Verify `/api/export-slack` correctly delegates and returns expected response structure."""
    expected_response = SlackExportResponse(
        success=True,
        message="Posted to Slack successfully",
        payload_sent={"blocks": []}
    )
    mock_slack_export.return_value = expected_response
    
    payload = {
        "sprint_goal": "Optimize CSV rendering pipeline",
        "tickets": [],
        "custom_message": "Urgent attention required"
    }
    response = client.post("/api/export-slack", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["message"] == "Posted to Slack successfully"

def test_slack_service_dry_run():
    """Verify export_to_slack defaults to Dry-Run Mode when webhook is missing."""
    old_webhook = settings.SLACK_WEBHOOK_URL
    try:
        settings.SLACK_WEBHOOK_URL = ""
        tickets = [
            SprintTicket(
                id="PROJ-1",
                title="Create exporter utility",
                description="Background compiler logic",
                acceptance_criteria=["CSV compiles"],
                story_points=5,
                priority="High",
                assignee_role="Backend"
            )
        ]
        res = export_to_slack(
            sprint_goal="CSV Performance",
            tickets=tickets,
            custom_message="Dry run test"
        )
        assert res.success is True
        assert "Dry-Run Mode" in res.message
        assert "blocks" in res.payload_sent
        assert len(res.payload_sent["blocks"]) > 0
    finally:
        settings.SLACK_WEBHOOK_URL = old_webhook

@patch("requests.post")
def test_slack_service_live(mock_post):
    """Verify export_to_slack triggers POST request to the webhook when configured."""
    old_webhook = settings.SLACK_WEBHOOK_URL
    try:
        settings.SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/test"
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        
        res = export_to_slack(
            sprint_goal="Webhook Test",
            tickets=[]
        )
        assert res.success is True
        assert "Successfully posted to Slack webhook" in res.message
        mock_post.assert_called_once()
    finally:
        settings.SLACK_WEBHOOK_URL = old_webhook


# --- Git Endpoint & Service Tests ---

@patch("app.main.audit_pull_request")
def test_audit_pr_endpoint(mock_audit):
    """Verify `/api/audit-pr` correctly delegates and returns expected response structure."""
    expected_response = PRAuditResponse(
        success=True,
        status="Pass",
        criteria_checked=[
            PRAuditCriterion(criteria="Item 1", satisfied=True, evidence="Found code")
        ],
        summary="Audit looks solid"
    )
    mock_audit.return_value = expected_response
    
    payload = {
        "repo_owner": "google",
        "repo_name": "antigravity",
        "pr_number": 42,
        "acceptance_criteria": ["Item 1"]
    }
    response = client.post("/api/audit-pr", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["status"] == "Pass"
    assert len(res_json["criteria_checked"]) == 1

@patch("app.main.create_git_branch")
def test_create_branch_endpoint(mock_branch):
    """Verify `/api/create-branch` correctly delegates and returns expected response structure."""
    expected_response = GitBranchResponse(
        success=True,
        message="Created branch",
        branch_url="https://github.com/google/antigravity/tree/feat-csv"
    )
    mock_branch.return_value = expected_response
    
    payload = {
        "repo_owner": "google",
        "repo_name": "antigravity",
        "branch_name": "feat-csv"
    }
    response = client.post("/api/create-branch", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert "feat-csv" in res_json["branch_url"]

def test_git_service_audit_dry_run():
    """Verify audit_pull_request runs in Dry-Run when tokens are missing."""
    old_token = settings.GITHUB_ACCESS_TOKEN
    try:
        settings.GITHUB_ACCESS_TOKEN = ""
        res = audit_pull_request(
            repo_owner="owner",
            repo_name="repo",
            pr_number=5,
            acceptance_criteria=["Verify test log"]
        )
        assert res.success is True
        assert "Dry-Run Mode" in res.summary
        assert len(res.criteria_checked) == 1
        assert res.criteria_checked[0].criteria == "Verify test log"
    finally:
        settings.GITHUB_ACCESS_TOKEN = old_token

@patch("requests.get")
@patch("app.services.git_service.GeminiService.generate_structured_data")
def test_git_service_audit_github(mock_generate, mock_get):
    """Verify audit_pull_request requests files from GitHub and calls LLM structured audit."""
    old_token = settings.GITHUB_ACCESS_TOKEN
    try:
        settings.GITHUB_ACCESS_TOKEN = "ghp_test_token"
        
        # Mock GitHub files API call
        mock_res = mock_get.return_value
        mock_res.status_code = 200
        mock_res.json.return_value = [
            {"filename": "app.py", "patch": "@@ -1 +1,2 @@\n+print('test')", "status": "modified"}
        ]
        
        # Mock LLM generation call
        expected_audit = PRAuditResponse(
            success=True,
            status="Pass",
            criteria_checked=[
                PRAuditCriterion(criteria="Verify test log", satisfied=True, evidence="print statement found")
            ],
            summary="PR looks complete"
        )
        mock_generate.return_value = expected_audit
        
        res = audit_pull_request(
            repo_owner="google",
            repo_name="antigravity",
            pr_number=1,
            acceptance_criteria=["Verify test log"]
        )
        assert res.success is True
        assert res.status == "Pass"
        assert len(res.criteria_checked) == 1
        assert res.criteria_checked[0].satisfied is True
        
        mock_get.assert_called_once_with(
            "https://api.github.com/repos/google/antigravity/pulls/1/files",
            headers={
                "Authorization": "token ghp_test_token",
                "Accept": "application/vnd.github.v3+json"
            },
            timeout=20
        )
    finally:
        settings.GITHUB_ACCESS_TOKEN = old_token

def test_git_service_branch_dry_run():
    """Verify create_git_branch runs in Dry-Run when token is missing."""
    old_token = settings.GITHUB_ACCESS_TOKEN
    try:
        settings.GITHUB_ACCESS_TOKEN = ""
        res = create_git_branch(
            repo_owner="owner",
            repo_name="repo",
            branch_name="feat-xyz"
        )
        assert res.success is True
        assert "Dry-Run Mode" in res.message
        assert "feat-xyz" in res.branch_url
    finally:
        settings.GITHUB_ACCESS_TOKEN = old_token

@patch("requests.post")
@patch("requests.get")
def test_git_service_branch_github(mock_get, mock_post):
    """Verify create_git_branch checks reference and creates GitHub branch."""
    old_token = settings.GITHUB_ACCESS_TOKEN
    try:
        settings.GITHUB_ACCESS_TOKEN = "ghp_test_token"
        
        # Mock branch ref retrieval
        mock_res_get = mock_get.return_value
        mock_res_get.status_code = 200
        mock_res_get.json.return_value = {"object": {"sha": "mock-sha-val"}}
        
        # Mock branch creation
        mock_res_post = mock_post.return_value
        mock_res_post.status_code = 201
        
        res = create_git_branch(
            repo_owner="google",
            repo_name="antigravity",
            branch_name="new-feature"
        )
        assert res.success is True
        assert "new-feature" in res.branch_url
        
        mock_get.assert_called_once()
        mock_post.assert_called_once()
    finally:
        settings.GITHUB_ACCESS_TOKEN = old_token

# --- Product Lifecycle Endpoint & Service Tests ---

@patch("app.main.run_feature_qa")
def test_qa_feature_endpoint(mock_qa):
    """Verify `/api/qa-feature` endpoint works correctly."""
    expected_response = FeatureQAResponse(
        success=True,
        answer="The code satisfies the specifications.",
        compliance_status="Pass",
        checked_items=[
            QAEvidence(requirement="Email link", status="Implemented", file_references=["main.py"], details="Found function")
        ]
    )
    mock_qa.return_value = expected_response
    
    payload = {
        "feature_specs": ["Send email when done"],
        "repo_path": "/mock/path",
        "user_query": "Is email working fine?"
    }
    response = client.post("/api/qa-feature", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["compliance_status"] == "Pass"

@patch("app.main.run_version_upgrade")
def test_version_upgrade_endpoint(mock_upgrade):
    """Verify `/api/version-upgrade` endpoint works correctly."""
    expected_response = VersionUpgradeResponse(
        success=True,
        updated_prd="# New version PRD",
        changelog=[UpgradeChangelogItem(feature="Email", action="Modified", description="Added track status")],
        migration_complexity="Low",
        migration_guide="Perform migration step 1"
    )
    mock_upgrade.return_value = expected_response
    
    payload = {
        "previous_prd": "# PRD 1.0",
        "upgrade_input": "Add tracking metrics to email delivery",
        "repo_path": None,
        "additional_context": []
    }
    response = client.post("/api/version-upgrade", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert "# New version PRD" in res_json["updated_prd"]

def test_qa_feature_service_dry_run():
    """Verify run_feature_qa defaults to Dry-Run Mode when repo_path is missing or invalid."""
    res = run_feature_qa(
        feature_specs=["Ensure background compilation works"],
        repo_path=None,
        user_query="Is compilation fine?"
    )
    assert res.success is True
    assert "Dry-Run Mode" in res.answer
    assert len(res.checked_items) > 0

def test_version_upgrade_service_dry_run():
    """Verify run_version_upgrade operates correctly with missing repo_path."""
    with patch("app.services.lifecycle_service.GeminiService.generate_structured_data") as mock_generate:
        mock_generate.return_value = VersionUpgradeResponse(
            success=True,
            updated_prd="# Version 2.0 PRD",
            changelog=[UpgradeChangelogItem(feature="X", action="Added", description="Y")],
            migration_complexity="Low",
            migration_guide="Z"
        )
        res = run_version_upgrade(
            previous_prd="# Old PRD",
            upgrade_input="Add features",
            repo_path=None
        )
        assert res.success is True
        assert "# Version 2.0 PRD" in res.updated_prd

def test_ui_endpoints():
    """Verify that UI endpoints respond successfully with correct media types."""
    # Test GET /ui
    response = client.get("/ui")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "PM Copilot" in response.text

    # Test GET /ui/style.css
    response = client.get("/ui/style.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
    assert "CSS Variables" in response.text

    # Test GET /ui/app.js
    response = client.get("/ui/app.js")
    assert response.status_code == 200
    assert "application/javascript" in response.headers["content-type"]
    assert "currentPrdTitle" in response.text

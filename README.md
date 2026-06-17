# AI Product Manager Copilot - Backend

An AI-powered backend service that assists Product Managers and Software Architects by:
1. **Drafting PRDs**: Converts feature ideas and user problems into structured, copy-paste-ready Product Requirement Documents (PRDs).
2. **Analyzing Technical Feasibility**: Scans codebases, maps PRDs to file adjustments, rates complexity, detects engineering risks, and estimates effort hours.
3. **Generating Sprint Plans**: Translates PRDs and feasibility metrics into detailed, estimation-ready Scrum/Kanban backlog tickets (Jira/Linear style).

---

## Technical Stack
- **Framework**: FastAPI (Python 3.13)
- **AI Integration**: Google Gemini SDK (using `gemini-2.5-flash` for high-speed, large-context parsing)
- **Data Validation**: Pydantic v2
- **Environment Management**: Python-dotenv

---

## Quick Start

### 1. Configure the Environment
Copy `.env.example` to `.env` and configure your credentials:
```bash
cp .env.example .env
```
Ensure you provide a valid **`GEMINI_API_KEY`** from [Google AI Studio](https://aistudio.google.com/).

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Server
Start the uvicorn development server:
```bash
python -m uvicorn app.main:app --reload
```
By default, the server runs on `http://127.0.0.1:8000`.

---

## API Documentation

Once the server is running, visit **`http://127.0.0.1:8000/docs`** to view the interactive Swagger API documentation.

### Core Endpoints

#### 1. Test Connection
- **Endpoint**: `GET /api/test-connection`
- **Description**: Verifies that the configured `GEMINI_API_KEY` is valid and active.

#### 2. Analyze Feedback
- **Endpoint**: `POST /api/analyze-feedback`
- **Request Body (`FeedbackAnalysisRequest`)**:
  ```json
  {
    "feedback_items": [
      "Our CSV downloads time out when we have more than 5,000 users. It's a huge blocker.",
      "The CSV export is extremely slow and crashes the page on operations tab."
    ],
    "company_context": "Analytics dashboard for ops teams"
  }
  ```
- **Response (`FeedbackAnalysisResponse`)**:
  - `total_items_processed`: Number of feedback records analyzed
  - `clusters`: Array of theme clusters:
    - `theme`: Group title (e.g. `CSV Timeout`)
    - `type`: Category (`Bug`, `Feature Request`, `Usability Improvement`)
    - `sentiment`: User emotion (`Positive`, `Neutral`, `Frustrated`, `Angry`)
    - `urgency`: Priority classification (`High`, `Medium`, `Low`)
    - `impact_score`: Priority rating (1 to 10)
    - `summary`: In-depth aggregation of findings
    - `associated_quotes`: Direct user quotes mapped to this cluster
    - `recommended_action`: Proposed PM next step
  - `key_takeaways`: Core strategic recommendations

#### 3. Generate PRD
- **Endpoint**: `POST /api/generate-prd`
- **Request Body (`PRDGenerationRequest`)**:
  ```json
  {
    "feature_idea": "Build a robust CSV export feature with email delivery when done.",
    "target_audience": "Enterprise Operations managers",
    "business_objectives": "Reduce user wait time and server timeout exceptions",
    "key_requirements": [
      "Process in the background",
      "Upload export to S3",
      "Email download link"
    ]
  }
  ```
- **Response (`PRDGenerationResponse`)**:
  - `title`: Formal name of the feature
  - `executive_summary`: Brief objective description
  - `objectives`: Array of business/user goals
  - `user_personas`: Target users description
  - `functional_requirements`: Array of exact system tasks
  - `user_stories`: Agile stories (`As a... I want to... So that...`)
  - `acceptance_criteria`: Checklist for QA
  - `out_of_scope`: Features excluded from this version
  - `edge_cases`: Boundary conditions and handling
  - `full_markdown`: Renders the entire compiled PRD document for one-click copy-pasting into Notion/Confluence

#### 4. Analyze Technical Feasibility
- **Endpoint**: `POST /api/analyze-feasibility`
- **Request Body (`FeasibilityRequest`)**:
  ```json
  {
    "prd_content": "### Feature Name\nDescription of requirements...",
    "repo_path": "D:/MyProjects/my-app",
    "instructions": "Focus on database changes and API endpoints"
  }
  ```
- **Response (`FeasibilityResponse`)**:
  - `complexity`: Overall complexity (`Easy`, `Medium`, `Hard`)
  - `complexity_rationale`: Reason for complexity rating
  - `architectural_impact`: Array of files to `NEW`, `MODIFY`, or `DELETE` with descriptions
  - `technical_risks`: High/Medium/Low risks with mitigation proposals
  - `new_dependencies`: Libraries to install
  - `effort_estimate_hours`: Expected development time in hours
  - `summary`: Detailed architectural overview

#### 5. Generate Sprint Plan
- **Endpoint**: `POST /api/generate-sprint-plan`
- **Request Body (`SprintPlanRequest`)**:
  ```json
  {
    "prd_content": "### Feature Name\nDescription of requirements...",
    "feasibility_report": { ... }, 
    "sprint_duration_weeks": 2
  }
  ```
- **Response (`SprintPlanResponse`)**:
  - `sprint_goal`: Standard sprint outcome statement
  - `tickets`: Array of structured tickets:
    - `id`: Unique ticket ID (e.g. `PROJ-1`)
    - `title`: Short task name
    - `description`: Detailed technical execution steps
    - `acceptance_criteria`: Checklist for validation
    - `story_points`: Fibonacci effort estimate (1, 2, 3, 5, 8, 13)
    - `priority`: High, Medium, Low priority
    - `assignee_role`: Frontend, Backend, DevOps, QA, etc.


#### 6. Export Sprint to Jira
- **Endpoint**: `POST /api/export-jira`
- **Request Body (`JiraExportRequest`)**:
  ```json
  {
    "tickets": [
      {
        "id": "PROJ-1",
        "title": "Create Exporter Utility",
        "description": "Create python background CSV task exporter",
        "acceptance_criteria": ["CSV logic works"],
        "story_points": 5,
        "priority": "High",
        "assignee_role": "Backend"
      }
    ],
    "project_key": "PROJ"
  }
  ```
- **Response (`JiraExportResponse`)**:
  - `success`: Boolean indicating if export completed successfully
  - `message`: Confirmation or status information
  - `created_issues`: Array of objects containing:
    - `id`: Jira unique database ID
    - `key`: Jira issue ticket key (e.g. `PROJ-101`)
    - `url`: Direct browse link to browse ticket on Jira board


#### 7. Export PRD to Notion
- **Endpoint**: `POST /api/export-notion`
- **Request Body (`NotionExportRequest`)**:
  ```json
  {
    "title": "CSV Background Exporter PRD",
    "content_markdown": "# CSV Background Exporter PRD\n\n## Executive Summary\nImplement background processing for export tasks.",
    "parent_page_id": "secret_parent_page_id_override"
  }
  ```
- **Response (`NotionExportResponse`)**:
  - `success`: Boolean indicating if Notion page sync completed successfully
  - `message`: Confirmation or status information
  - `page_url`: Direct browse link to browse page in Notion workspace
  - `page_id`: Notion unique database UUID created

#### 8. Export Sprint to Linear
- **Endpoint**: `POST /api/export-linear`
- **Request Body (`LinearExportRequest`)**:
  ```json
  {
    "tickets": [
      {
        "id": "PROJ-1",
        "title": "Create exporter utility",
        "description": "Background CSV exporter service and mutation",
        "acceptance_criteria": ["GraphQL works"],
        "story_points": 3,
        "priority": "High",
        "assignee_role": "Backend"
      }
    ],
    "team_id": "optional-linear-team-uuid-override"
  }
  ```
- **Response (`LinearExportResponse`)**:
  - `success`: Boolean indicating if export completed successfully
  - `message`: Confirmation or status information
  - `created_issues`: Array of objects containing:
    - `id`: Linear unique database ID
    - `key`: Linear issue identifier key (e.g., `MOCK-101`)
    - `url`: Direct browse link to browse issue on Linear board

#### 9. Export Sprint to Slack
- **Endpoint**: `POST /api/export-slack`
- **Request Body (`SlackExportRequest`)**:
  ```json
  {
    "sprint_goal": "Optimize CSV downloads processing",
    "tickets": [
      {
        "id": "PROJ-1",
        "title": "Create exporter utility",
        "story_points": 3,
        "priority": "High",
        "assignee_role": "Backend"
      }
    ],
    "custom_message": "Release planned for Friday"
  }
  ```
- **Response (`SlackExportResponse`)**:
  - `success`: Boolean indicating if post succeeded
  - `message`: Detailed status message
  - `payload_sent`: Constructed JSON Slack Block Kit structure

#### 10. Audit Pull Request Compliance
- **Endpoint**: `POST /api/audit-pr`
- **Request Body (`PRAuditRequest`)**:
  ```json
  {
    "repo_owner": "google",
    "repo_name": "antigravity",
    "pr_number": 12,
    "acceptance_criteria": [
      "Process CSV generation in the background",
      "Retry on failure"
    ],
    "git_provider": "github"
  }
  ```
- **Response (`PRAuditResponse`)**:
  - `success`: Boolean indicating if audit ran successfully
  - `status`: Overall audit compliance status (`Pass`, `Fail`, or `Needs Work`)
  - `criteria_checked`: Checklist details including satisfaction boolean and reasoning/evidence
  - `summary`: Deep-dive audit report summary from LLM analysis of PR diffs

#### 11. Create Task Branch
- **Endpoint**: `POST /api/create-branch`
- **Request Body (`GitBranchRequest`)**:
  ```json
  {
    "repo_owner": "google",
    "repo_name": "antigravity",
    "branch_name": "feat-csv-background",
    "base_branch": "main",
    "git_provider": "github"
  }
  ```
- **Response (`GitBranchResponse`)**:
  - `success`: Boolean indicating branch creation
  - `message`: Details about reference created
  - `branch_url`: Direct URL to browse new branch on GitHub/GitLab

#### 12. Evaluate Feature Code vs specs
- **Endpoint**: `POST /api/qa-feature`
- **Request Body (`FeatureQARequest`)**:
  ```json
  {
    "feature_specs": [
      "Process CSV generation in background",
      "Email download link once generated",
      "Deliver under 10 seconds"
    ],
    "repo_path": "D:/MyProjects/my-app",
    "user_query": "Does the code support sending emails to the user when CSV compile succeeds?"
  }
  ```
- **Response (`FeatureQAResponse`)**:
  - `success`: Boolean indicating if query evaluation completed
  - `answer`: Written explanation addressing query referencing codebase files
  - `compliance_status`: Overall compliance (`Pass`, `Needs Work`, or `Mismatched`)
  - `checked_items`: Array of checklist evaluations showing satisfaction flags and code references

#### 13. Context-Aware Version Upgrade
- **Endpoint**: `POST /api/version-upgrade`
- **Request Body (`VersionUpgradeRequest`)**:
  ```json
  {
    "previous_prd": "# PRD Version 1.0\nRequirements detail...",
    "upgrade_input": "Upgrade CSV generation to run on worker threads with progress updates",
    "repo_path": "D:/MyProjects/my-app",
    "additional_context": [
      "Previous latency charts: timeouts happen after 30s",
      "S3 storage configuration parameters"
    ]
  }
  ```
- **Response (`VersionUpgradeResponse`)**:
  - `success`: Boolean indicating if v2.0 PRD generated successfully
  - `updated_prd`: Complete v2.0 PRD markdown incorporating previous structure without redundancies
  - `changelog`: Exact details of requirements added, modified, or removed
  - `migration_complexity`: Codebase refactoring complexity (`Low`, `Medium`, `High`)
  - `migration_guide`: Developer instructions on how to transition codebase to v2.0

---

## Running Tests
Run unit tests and verification suites:
```bash
pytest
```



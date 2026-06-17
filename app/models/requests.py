from pydantic import BaseModel, Field
from typing import Optional, List

class FeasibilityRequest(BaseModel):
    prd_content: str = Field(..., description="The markdown text or description of the Product Requirement Document (PRD)")
    repo_path: Optional[str] = Field(None, description="Absolute local path to the codebase repository to analyze")
    instructions: Optional[str] = Field(None, description="Optional custom guidelines or areas of engineering focus to pay attention to")

class SprintPlanRequest(BaseModel):
    prd_content: str = Field(..., description="The Product Requirement Document (PRD) markdown or text")
    feasibility_report: Optional[dict] = Field(None, description="Optional structured result from the feasibility analysis API to inform task breakdown")
    sprint_duration_weeks: Optional[int] = Field(2, description="Target duration of the sprint in weeks")

class PRDGenerationRequest(BaseModel):
    feature_idea: str = Field(..., description="The raw concept, prompt, or user problem statement for the feature")
    target_audience: Optional[str] = Field(None, description="Brief description of the intended users/audience")
    business_objectives: Optional[str] = Field(None, description="The key business goals, e.g., increase engagement, reduce support requests")
    key_requirements: Optional[List[str]] = Field(None, description="List of essential requirements that must be included in the PRD")
    instructions: Optional[str] = Field(None, description="Custom guidelines, styling, or architecture expectations")

class FeedbackAnalysisRequest(BaseModel):
    feedback_items: List[str] = Field(..., description="A list of raw customer feedback comments, support logs, reviews, or Slack text snippets")
    company_context: Optional[str] = Field(None, description="Brief description of the company and context to help AI categorize feedback properly")
    instructions: Optional[str] = Field(None, description="Optional custom guidelines for feedback classification and theme prioritization")

from app.models.responses import SprintTicket

class JiraExportRequest(BaseModel):
    tickets: List[SprintTicket] = Field(..., description="List of sprint backlog tickets to export to Jira")
    project_key: Optional[str] = Field(None, description="Optional override Jira Project Key (defaults to JIRA_PROJECT_KEY env)")

class NotionExportRequest(BaseModel):
    title: str = Field(..., description="The title of the PRD page to create in Notion")
    content_markdown: str = Field(..., description="The full Markdown text of the PRD to import")
    parent_page_id: Optional[str] = Field(None, description="Optional parent Notion page/database UUID to override config setting")

class LinearExportRequest(BaseModel):
    tickets: List[SprintTicket] = Field(..., description="List of sprint backlog tickets to export to Linear")
    team_id: Optional[str] = Field(None, description="Optional override Linear Team UUID (defaults to LINEAR_TEAM_ID env)")

class SlackExportRequest(BaseModel):
    sprint_goal: str = Field(..., description="The high level sprint goal or main notification message")
    tickets: Optional[List[SprintTicket]] = Field(default=[], description="Optional list of sprint tickets to summarize")
    custom_message: Optional[str] = Field(None, description="Optional custom markdown/text to output alongside tickets")
    webhook_url: Optional[str] = Field(None, description="Optional override Slack Incoming Webhook URL")

class PRAuditRequest(BaseModel):
    repo_owner: str = Field(..., description="The owner of the GitHub/GitLab repository")
    repo_name: str = Field(..., description="The name of the repository")
    pr_number: int = Field(..., description="The pull request or merge request number")
    acceptance_criteria: List[str] = Field(..., description="List of acceptance criteria checklist items to verify")
    git_provider: Optional[str] = Field("github", description="Git provider: 'github' or 'gitlab'")

class GitBranchRequest(BaseModel):
    repo_owner: str = Field(..., description="The owner of the repository")
    repo_name: str = Field(..., description="The name of the repository")
    branch_name: str = Field(..., description="The name of the new branch to create")
    base_branch: Optional[str] = Field("main", description="The base branch to branch off from")
    git_provider: Optional[str] = Field("github", description="Git provider: 'github' or 'gitlab'")

class FeatureQARequest(BaseModel):
    feature_specs: List[str] = Field(..., description="Launch event notes, specifications, benefits, or expected capabilities documents")
    repo_path: Optional[str] = Field(None, description="Absolute local path to the created codebase directory to analyze")
    user_query: str = Field(..., description="The PM's specific question about the feature, e.g., 'Is this working fine?'")
    instructions: Optional[str] = Field(None, description="Optional custom guidelines for QA verification")

class VersionUpgradeRequest(BaseModel):
    previous_prd: str = Field(..., description="The Product Requirement Document (PRD) markdown of the previous version")
    upgrade_input: str = Field(..., description="The new features, changes, or version improvements expected")
    repo_path: Optional[str] = Field(None, description="Absolute local path to the current codebase directory for reference")
    additional_context: Optional[List[str]] = Field(default=[], description="Optional charts descriptions, metric reports, or other past context files")






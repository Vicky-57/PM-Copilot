from pydantic import BaseModel, Field
from typing import List, Optional

class FileImpact(BaseModel):
    file_path: str = Field(..., description="Path to the file relative to repo root, or proposed path if it's new")
    action: str = Field(..., description="Action required: 'NEW', 'MODIFY', or 'DELETE'")
    description: str = Field(..., description="Details of the specific modifications or logic to implement")

class TechnicalRisk(BaseModel):
    risk: str = Field(..., description="Description of the risk (e.g., performance bottleneck, security concern)")
    impact: str = Field(..., description="Severity of the impact if it occurs ('High', 'Medium', 'Low')")
    mitigation: str = Field(..., description="Suggested mitigation plan or architectural pattern to bypass risk")

class FeasibilityResponse(BaseModel):
    complexity: str = Field(..., description="Overall implementation complexity level ('Easy', 'Medium', 'Hard')")
    complexity_rationale: str = Field(..., description="Justification for the chosen complexity rating")
    architectural_impact: List[FileImpact] = Field(..., description="A list of files that will be added, edited, or deleted, and why")
    technical_risks: List[TechnicalRisk] = Field(..., description="List of engineering risks, impacts, and mitigations")
    new_dependencies: List[str] = Field(..., description="List of third-party libraries, packages, or services that must be integrated")
    effort_estimate_hours: int = Field(..., description="Estimated total engineering hours required for implementation")
    summary: str = Field(..., description="Executive summary of the feasibility analyzer's findings")

class SprintTicket(BaseModel):
    id: str = Field(..., description="Unique ticket identifier (e.g. PROJ-1, PROJ-2)")
    title: str = Field(..., description="Clear, action-oriented task title")
    description: str = Field(..., description="Detailed description of implementation instructions, context, and requirements")
    acceptance_criteria: List[str] = Field(..., description="List of clear, verifiable checklist items for QA/Review")
    story_points: int = Field(..., description="Fibonacci estimate (1, 2, 3, 5, 8, 13)")
    priority: str = Field(..., description="Task priority level ('High', 'Medium', 'Low')")
    assignee_role: str = Field(..., description="Recommended role ('Frontend', 'Backend', 'Fullstack', 'DevOps', 'QA')")

class SprintPlanResponse(BaseModel):
    sprint_goal: str = Field(..., description="High level goal of the sprint based on the requirements")
    tickets: List[SprintTicket] = Field(..., description="List of sprint backlog tickets required to fulfill the PRD")

class PRDGenerationResponse(BaseModel):
    title: str = Field(..., description="The official, formal name of the feature")
    executive_summary: str = Field(..., description="A concise, high-level summary of what the feature is and why it's being built")
    objectives: List[str] = Field(..., description="Business and user objectives or goals this feature seeks to achieve")
    user_personas: List[str] = Field(..., description="Description of the target user roles/personas who benefit from this")
    functional_requirements: List[str] = Field(..., description="Direct functional items and behaviors required by the software")
    user_stories: List[str] = Field(..., description="User stories formatted as: As a... I want to... So that...")
    acceptance_criteria: List[str] = Field(..., description="Key validation conditions and rules (Given/When/Then or checklist style)")
    out_of_scope: List[str] = Field(..., description="Explicitly details what is NOT being built in this release/version")
    edge_cases: List[str] = Field(..., description="Potential outlier scenarios, exceptions, or error states and how the system behaves")
    full_markdown: str = Field(..., description="A fully formatted, professional markdown document combining all the PRD fields, ready to copy-paste or upload to Notion/Confluence")

class FeedbackCluster(BaseModel):
    theme: str = Field(..., description="The main feature theme or bug category representing this cluster (e.g., 'Slow CSV Exports')")
    type: str = Field(..., description="The classification of this cluster: 'Bug', 'Feature Request', or 'Usability Improvement'")
    sentiment: str = Field(..., description="Dominant user sentiment in this feedback cluster: 'Positive', 'Neutral', 'Frustrated', 'Angry'")
    urgency: str = Field(..., description="Estimated priority based on sentiment and description: 'High', 'Medium', 'Low'")
    impact_score: int = Field(..., description="Numerical score from 1-10 of how critical/impactful solving this is")
    summary: str = Field(..., description="Detailed description summing up the user problems/requests in this theme")
    associated_quotes: List[str] = Field(..., description="Select quotes from the input items that illustrate this cluster's theme")
    recommended_action: str = Field(..., description="Recommended PM next step (e.g., 'Create a PRD for optimizing CSV export processing')")

class FeedbackAnalysisResponse(BaseModel):
    total_items_processed: int = Field(..., description="Number of feedback records analyzed")
    clusters: List[FeedbackCluster] = Field(..., description="Grouped feature request or bug clusters extracted from the input data")
    key_takeaways: List[str] = Field(..., description="Top strategic insights and overall product findings from the feedback list")

class JiraIssueInfo(BaseModel):
    id: str = Field(..., description="The unique database ID of the created Jira issue")
    key: str = Field(..., description="The ticket key of the created issue (e.g., PROJ-101)")
    url: str = Field(..., description="Direct URL link to browse the ticket on the Jira board")

class JiraExportResponse(BaseModel):
    success: bool = Field(..., description="Whether the issues were successfully exported or simulated")
    message: str = Field(..., description="Completion details and confirmation statement")
    created_issues: List[JiraIssueInfo] = Field(..., description="List of exported or mock-created Jira issue keys and direct links")

class NotionExportResponse(BaseModel):
    success: bool = Field(..., description="Whether the Notion page was created successfully or simulated")
    message: str = Field(..., description="Details and confirmation statement of the Notion sync status")
    page_url: str = Field(..., description="Direct link to browse the created page in the Notion workspace")
    page_id: str = Field(..., description="The unique page ID created in Notion")

class LinearIssueInfo(BaseModel):
    id: str = Field(..., description="The unique database ID of the created Linear issue")
    key: str = Field(..., description="The ticket identifier of the created issue (e.g. ABC-101)")
    url: str = Field(..., description="Direct URL link to browse the issue on Linear")

class LinearExportResponse(BaseModel):
    success: bool = Field(..., description="Whether the issues were successfully exported or simulated")
    message: str = Field(..., description="Completion details and confirmation statement of the export status")
    created_issues: List[LinearIssueInfo] = Field(..., description="List of exported or mock-created Linear issue details")

class SlackExportResponse(BaseModel):
    success: bool = Field(..., description="Whether the Slack message was successfully posted or simulated")
    message: str = Field(..., description="Completion message or description of status")
    payload_sent: dict = Field(..., description="The Block Kit or text payload JSON structured sent or simulated")

class PRAuditCriterion(BaseModel):
    criteria: str = Field(..., description="The acceptance criteria checklist item text")
    satisfied: bool = Field(..., description="Whether this criterion is satisfied by the PR file changes")
    evidence: str = Field(..., description="Reasoning or snippet indicating satisfaction or absence of code changes")

class PRAuditResponse(BaseModel):
    success: bool = Field(..., description="Whether the audit check was executed successfully")
    status: str = Field(..., description="Overall compliance status: 'Pass', 'Fail', or 'Needs Work'")
    criteria_checked: List[PRAuditCriterion] = Field(..., description="Checked checklist results")
    summary: str = Field(..., description="Detailed LLM auditing report summary")

class GitBranchResponse(BaseModel):
    success: bool = Field(..., description="Whether the branch was successfully created or simulated")
    message: str = Field(..., description="Details and confirmation statement of status")
    branch_url: str = Field(..., description="Direct link to the created branch on the remote Git repository")

class QAEvidence(BaseModel):
    requirement: str = Field(..., description="Description of the feature requirement or launch capability assessed")
    status: str = Field(..., description="Satisfaction status: 'Implemented', 'Missing', or 'Partial'")
    file_references: List[str] = Field(..., description="List of source files where evidence was found (or empty)")
    details: str = Field(..., description="Written code-backed verification details or reasons for absence")

class FeatureQAResponse(BaseModel):
    success: bool = Field(..., description="Whether the QA check completed successfully")
    answer: str = Field(..., description="Direct analysis summary addressing the user's specific query")
    compliance_status: str = Field(..., description="Overall compliance status: 'Pass', 'Needs Work', or 'Mismatched'")
    checked_items: List[QAEvidence] = Field(..., description="Checklist assessing specific launch specifications against codebase")

class UpgradeChangelogItem(BaseModel):
    feature: str = Field(..., description="Name of the feature affected")
    action: str = Field(..., description="Transition action: 'Added', 'Modified', or 'Removed'")
    description: str = Field(..., description="Explanation of what changed from the previous version")

class VersionUpgradeResponse(BaseModel):
    success: bool = Field(..., description="Whether the version upgrade PRD generation was successful")
    updated_prd: str = Field(..., description="The copy-paste ready Markdown text of the upgraded v2.0 PRD")
    changelog: List[UpgradeChangelogItem] = Field(..., description="List of direct modifications from previous version requirements")
    migration_complexity: str = Field(..., description="Migration risk and refactoring complexity rating ('Low', 'Medium', 'High')")
    migration_guide: str = Field(..., description="Brief step-by-step developer guidelines for integrating version differences")






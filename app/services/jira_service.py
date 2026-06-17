import base64
import requests
from typing import List, Optional
from app.models.responses import SprintTicket, JiraIssueInfo, JiraExportResponse
from app.config import settings

def export_sprint_to_jira(
    tickets: List[SprintTicket],
    project_key: Optional[str] = None
) -> JiraExportResponse:
    """
    Exports a list of sprint tickets directly to Jira Cloud,
    or runs in Dry-Run simulation mode if Jira settings are unconfigured.
    """
    
    # 1. Determine key settings & resolve overrides
    jira_url = settings.JIRA_URL.rstrip("/")
    jira_email = settings.JIRA_EMAIL
    jira_token = settings.JIRA_API_TOKEN
    proj_key = project_key or settings.JIRA_PROJECT_KEY or "PROJ"
    
    # Check if we should run in dry-run mode
    is_dry_run = not (jira_url and jira_email and jira_token)
    
    created_issues: List[JiraIssueInfo] = []
    
    if is_dry_run:
        # Simulate export
        mock_domain = jira_url if jira_url else "https://mock-company.atlassian.net"
        
        for idx, ticket in enumerate(tickets, 101):
            key = f"{proj_key}-{idx}"
            created_issues.append(
                JiraIssueInfo(
                    id=f"simulated-id-{key}",
                    key=key,
                    url=f"{mock_domain}/browse/{key}"
                )
            )
            
        return JiraExportResponse(
            success=True,
            message=(
                "Dry-Run Mode: Simulation completed successfully. "
                "No issues were uploaded because Jira configuration credentials (URL, Email, API Token) are missing in your .env file."
            ),
            created_issues=created_issues
        )
        
    # 2. Run real Jira API calls (using Basic Auth with API Token)
    # Encode auth string: email:api_token
    auth_str = f"{jira_email}:{jira_token}"
    auth_bytes = auth_str.encode("utf-8")
    auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Priority mapping
    priority_map = {
        "High": "High",
        "Medium": "Medium",
        "Low": "Low"
    }
    
    errors = []
    
    # Process issue creations
    for ticket in tickets:
        # Construct issue payload for Jira REST API v2
        summary = f"[{ticket.id}] {ticket.title}"
        desc = (
            f"**Description:**\n{ticket.description}\n\n"
            f"**Recommended Assignee Role:** {ticket.assignee_role}\n\n"
            f"**Acceptance Criteria:**\n" + "\n".join(f"- {ac}" for ac in ticket.acceptance_criteria)
        )
        
        payload = {
            "fields": {
                "project": {
                    "key": proj_key
                },
                "summary": summary,
                "description": desc,
                "issuetype": {
                    "name": "Task"  # Defaulting to standard 'Task' type
                },
                "priority": {
                    "name": priority_map.get(ticket.priority, "Medium")
                }
            }
        }
        
        # Standard Jira Cloud custom field for Story Points is customfield_10016
        if ticket.story_points:
            payload["fields"]["customfield_10016"] = float(ticket.story_points)

        try:
            # We use rest/api/2/issue because it accepts a simple string for the 'description' field,
            # unlike v3 which requires Atlassian Document Format (ADF) JSON structure.
            api_endpoint = f"{jira_url}/rest/api/2/issue"
            response = requests.post(api_endpoint, headers=headers, json=payload, timeout=15)
            
            if response.status_code in (200, 201):
                res_data = response.json()
                issue_key = res_data.get("key", "")
                issue_id = res_data.get("id", "")
                created_issues.append(
                    JiraIssueInfo(
                        id=issue_id,
                        key=issue_key,
                        url=f"{jira_url}/browse/{issue_key}"
                    )
                )
            else:
                # If customfield_10016 fails (e.g. Story Points field has different custom ID in user's Jira instance),
                # try to fall back by creating the issue without story points
                if "customfield_10016" in payload["fields"]:
                    del payload["fields"]["customfield_10016"]
                    response_fallback = requests.post(api_endpoint, headers=headers, json=payload, timeout=15)
                    if response_fallback.status_code in (200, 201):
                        res_data = response_fallback.json()
                        issue_key = res_data.get("key", "")
                        issue_id = res_data.get("id", "")
                        created_issues.append(
                            JiraIssueInfo(
                                id=issue_id,
                                key=issue_key,
                                url=f"{jira_url}/browse/{issue_key}"
                            )
                        )
                        continue
                
                err_msg = f"Failed to create ticket '{ticket.title}': {response.status_code} - {response.text}"
                print(err_msg)
                errors.append(err_msg)
                
        except Exception as e:
            err_msg = f"Network or exception occurred during ticket '{ticket.title}' creation: {str(e)}"
            print(err_msg)
            errors.append(err_msg)
            
    if errors and not created_issues:
        return JiraExportResponse(
            success=False,
            message=f"Export failed. Errors: {'; '.join(errors[:3])}",
            created_issues=[]
        )
        
    status_msg = f"Successfully exported {len(created_issues)} tickets to Jira project '{proj_key}'."
    if errors:
        status_msg += f" (Note: {len(errors)} errors encountered: {errors[0]})"
        
    return JiraExportResponse(
        success=True,
        message=status_msg,
        created_issues=created_issues
    )

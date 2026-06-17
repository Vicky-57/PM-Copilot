import requests
from typing import List, Optional
from app.models.responses import SprintTicket, LinearIssueInfo, LinearExportResponse
from app.config import settings

def export_sprint_to_linear(
    tickets: List[SprintTicket],
    team_id: Optional[str] = None
) -> LinearExportResponse:
    """
    Exports a list of sprint plan tickets directly to a Linear team,
    or runs in Dry-Run simulation mode if Linear settings are unconfigured.
    """
    linear_key = settings.LINEAR_API_KEY
    target_team = team_id or settings.LINEAR_TEAM_ID
    
    is_dry_run = not (linear_key and target_team)
    
    created_issues: List[LinearIssueInfo] = []
    
    if is_dry_run:
        # Simulate export
        for idx, ticket in enumerate(tickets, 101):
            key = f"MOCK-{idx}"
            created_issues.append(
                LinearIssueInfo(
                    id=f"simulated-linear-id-{key}",
                    key=key,
                    url=f"https://linear.app/issue/{key}"
                )
            )
            
        return LinearExportResponse(
            success=True,
            message=(
                "Dry-Run Mode: Linear export simulated successfully. "
                "No issues were uploaded because Linear configuration credentials (API Key, Team ID) are missing in your .env file."
            ),
            created_issues=created_issues
        )
        
    # GraphQL headers
    headers = {
        "Authorization": linear_key,
        "Content-Type": "application/json"
    }
    
    # Priority mapping: Linear priorities: 1 (Urgent), 2 (High), 3 (Medium), 4 (Low), 0 (No Priority)
    priority_map = {
        "High": 2,
        "Medium": 3,
        "Low": 4
    }
    
    errors = []
    
    # Mutation string
    graphql_query = """
    mutation IssueCreate($input: IssueCreateInput!) {
        issueCreate(input: $input) {
            success
            issue {
                id
                identifier
                url
            }
        }
    }
    """
    
    for ticket in tickets:
        # Construct issue fields
        title = f"[{ticket.id}] {ticket.title}"
        desc = (
            f"**Description:**\n{ticket.description}\n\n"
            f"**Recommended Assignee Role:** {ticket.assignee_role}\n\n"
            f"**Acceptance Criteria:**\n" + "\n".join(f"- {ac}" for ac in ticket.acceptance_criteria)
        )
        
        variables = {
            "input": {
                "title": title,
                "description": desc,
                "teamId": target_team,
                "priority": priority_map.get(ticket.priority, 0),
            }
        }
        
        # Add story points estimate if present
        if ticket.story_points:
            variables["input"]["estimate"] = int(ticket.story_points)
            
        payload = {
            "query": graphql_query,
            "variables": variables
        }
        
        try:
            response = requests.post(
                "https://api.linear.app/graphql",
                headers=headers,
                json=payload,
                timeout=20
            )
            
            if response.status_code == 200:
                res_data = response.json()
                
                # Check for GraphQL query errors
                if "errors" in res_data:
                    err_msg = f"Linear GraphQL error: {res_data['errors'][0]['message']}"
                    errors.append(err_msg)
                    continue
                    
                data = res_data.get("data", {}).get("issueCreate", {})
                success = data.get("success", False)
                issue = data.get("issue")
                
                if success and issue:
                    created_issues.append(
                        LinearIssueInfo(
                            id=issue.get("id", ""),
                            key=issue.get("identifier", ""),
                            url=issue.get("url", "")
                        )
                    )
                else:
                    errors.append(f"Failed to create issue '{ticket.title}' in team. Check permission.")
            else:
                err_msg = f"Linear API HTTP error for '{ticket.title}': {response.status_code} - {response.text}"
                errors.append(err_msg)
                
        except Exception as e:
            err_msg = f"Exception occurred during Linear issue creation for '{ticket.title}': {str(e)}"
            errors.append(err_msg)
            
    if errors and not created_issues:
        return LinearExportResponse(
            success=False,
            message=f"Linear export failed. Errors: {'; '.join(errors[:3])}",
            created_issues=[]
        )
        
    status_msg = f"Successfully exported {len(created_issues)} tickets to Linear Team UUID '{target_team}'."
    if errors:
        status_msg += f" (Note: {len(errors)} errors encountered: {errors[0]})"
        
    return LinearExportResponse(
        success=True,
        message=status_msg,
        created_issues=created_issues
    )

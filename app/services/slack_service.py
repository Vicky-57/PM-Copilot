import requests
from typing import List, Optional
from app.models.responses import SprintTicket, SlackExportResponse
from app.config import settings

def export_to_slack(
    sprint_goal: str,
    tickets: List[SprintTicket] = [],
    custom_message: Optional[str] = None,
    webhook_url: Optional[str] = None
) -> SlackExportResponse:
    """
    Constructs a visual Slack Block Kit payload from sprint details
    and posts to an incoming webhook (or simulates if credentials are missing).
    """
    target_webhook = webhook_url or settings.SLACK_WEBHOOK_URL
    is_dry_run = not target_webhook
    
    # Constructing Slack Block Kit layout
    blocks = []
    
    # 1. Header block
    blocks.append({
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "🎯 New Sprint Backlog Announcement",
            "emoji": True
        }
    })
    
    # 2. Sprint Goal block
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*Sprint Goal:*\n{sprint_goal}"
        }
    })
    
    # 3. Custom message block (if provided)
    if custom_message:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Notice:*\n{custom_message}"
            }
        })
        
    blocks.append({"type": "divider"})
    
    # 4. Tickets listing
    if tickets:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Sprint Tickets Checklist:*"
            }
        })
        
        for ticket in tickets:
            priority_emoji = "🔴" if ticket.priority == "High" else "🟡" if ticket.priority == "Medium" else "🟢"
            ticket_text = (
                f"*[{ticket.id}] {ticket.title}*\n"
                f"• *Estimate:* {ticket.story_points} SP  • *Priority:* {priority_emoji} {ticket.priority}  • *Assignee:* `{ticket.assignee_role}`\n"
            )
            if ticket.acceptance_criteria:
                ticket_text += f"• *Acceptance Criteria:* {len(ticket.acceptance_criteria)} items"
                
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ticket_text
                }
            })
            
        blocks.append({"type": "divider"})
        
    # 5. Context attribution footer
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "🤖 Posted via *AI Product Manager Copilot Backend* | Version 1.0.0"
            }
        ]
    })
    
    payload = {"blocks": blocks}
    
    if is_dry_run:
        return SlackExportResponse(
            success=True,
            message="Dry-Run Mode: Slack webhook simulated successfully. Configure SLACK_WEBHOOK_URL to send real payloads.",
            payload_sent=payload
        )
        
    try:
        response = requests.post(
            target_webhook,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code in (200, 201):
            return SlackExportResponse(
                success=True,
                message=f"Successfully posted to Slack webhook (status code {response.status_code}).",
                payload_sent=payload
            )
        else:
            return SlackExportResponse(
                success=False,
                message=f"Slack API error. Status: {response.status_code}, Body: {response.text}",
                payload_sent=payload
            )
    except Exception as e:
        return SlackExportResponse(
            success=False,
            message=f"Exception during Slack export: {str(e)}",
            payload_sent=payload
        )

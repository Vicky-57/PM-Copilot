import requests
from typing import List, Optional
from app.models.responses import NotionExportResponse
from app.config import settings

def parse_markdown_to_notion_blocks(markdown_content: str) -> List[dict]:
    """
    Parses a standard markdown string into Notion API block objects.
    Supports headings (h1, h2, h3), lists, blockquotes, code blocks, and standard paragraphs.
    """
    blocks = []
    lines = markdown_content.splitlines()
    
    in_code_block = False
    code_content_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # 1. Handle code blocks
        if stripped.startswith("```"):
            if in_code_block:
                # Close code block
                code_text = "\n".join(code_content_lines)
                blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{"type": "text", "text": {"content": code_text}}],
                        "language": "plain"
                    }
                })
                in_code_block = False
                code_content_lines = []
            else:
                # Open code block
                in_code_block = True
                code_content_lines = []
            continue
            
        if in_code_block:
            code_content_lines.append(line)
            continue
            
        # Skip empty lines
        if not stripped:
            continue
            
        # 2. Parse Markdown elements
        if stripped.startswith("# "):
            val = stripped[2:]
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": val}}]
                }
            })
        elif stripped.startswith("## "):
            val = stripped[3:]
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": val}}]
                }
            })
        elif stripped.startswith("### "):
            val = stripped[4:]
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": val}}]
                }
            })
        elif stripped.startswith("> "):
            val = stripped[2:]
            blocks.append({
                "object": "block",
                "type": "quote",
                "quote": {
                    "rich_text": [{"type": "text", "text": {"content": val}}]
                }
            })
        elif stripped.startswith("- ") or stripped.startswith("* "):
            val = stripped[2:]
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": val}}]
                }
            })
        elif stripped[0].isdigit() and stripped.split(".", 1)[0].isdigit() and stripped.split(".", 1)[1].startswith(" "):
            # e.g. "1. "
            parts = stripped.split(".", 1)
            val = parts[1].strip()
            blocks.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": val}}]
                }
            })
        else:
            # Fallback to standard paragraph
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": stripped}}]
                }
            })
            
    # Clean up unclosed code block if present
    if in_code_block and code_content_lines:
        code_text = "\n".join(code_content_lines)
        blocks.append({
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{"type": "text", "text": {"content": code_text}}],
                "language": "plain"
            }
        })
        
    return blocks

def export_prd_to_notion(
    title: str,
    content_markdown: str,
    parent_page_id: Optional[str] = None
) -> NotionExportResponse:
    """
    Exports a markdown PRD document directly to Notion,
    or runs in Dry-Run simulation mode if Notion credentials are unconfigured.
    """
    notion_key = settings.NOTION_API_KEY
    parent_id = parent_page_id or settings.NOTION_PARENT_PAGE_ID
    
    is_dry_run = not (notion_key and parent_id)
    
    if is_dry_run:
        mock_id = "mock-prd-page-773a4d8c92e1"
        return NotionExportResponse(
            success=True,
            message=(
                "Dry-Run Mode: Notion export simulated successfully. "
                "No page was created because Notion configuration credentials (API Key, Parent Page ID) are missing in your .env file."
            ),
            page_url=f"https://notion.so/{mock_id}",
            page_id=mock_id
        )
        
    # Prepare Notion page creation payload
    headers = {
        "Authorization": f"Bearer {notion_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"  # Standard stable Notion API version
    }
    
    # Parse markdown content to children blocks
    children_blocks = parse_markdown_to_notion_blocks(content_markdown)
    
    payload = {
        "parent": {
            "type": "page_id",
            "page_id": parent_id
        },
        "properties": {
            "title": {
                "id": "title",
                "type": "title",
                "title": [
                    {
                        "type": "text",
                        "text": {
                            "content": title
                        }
                    }
                ]
            }
        },
        "children": children_blocks[:100]  # Notion API restricts initial page creations to 100 blocks
    }
    
    try:
        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=payload,
            timeout=20
        )
        
        if response.status_code == 200:
            res_data = response.json()
            page_id = res_data.get("id", "").replace("-", "")
            page_url = res_data.get("url", f"https://notion.so/{page_id}")
            
            return NotionExportResponse(
                success=True,
                message=f"Successfully synced page '{title}' to your Notion workspace.",
                page_url=page_url,
                page_id=page_id
            )
        else:
            return NotionExportResponse(
                success=False,
                message=f"Notion API error: {response.status_code} - {response.text}",
                page_url="",
                page_id=""
            )
    except Exception as e:
        return NotionExportResponse(
            success=False,
            message=f"Failed to query Notion API due to exception: {str(e)}",
            page_url="",
            page_id=""
        )

import json
from typing import Optional, Dict, Any
from app.models.responses import SprintPlanResponse
from app.services.gemini_service import GeminiService

SYSTEM_INSTRUCTION = (
    "You are an expert Scrum Master, Agile Coach, and Technical Project Manager. "
    "Your objective is to decompose a Product Requirement Document (PRD) and a Technical Feasibility Analysis "
    "into a complete, actionable engineering sprint backlog. "
    "You should design individual sprint tickets (user stories, developer tasks, backend/frontend setup, DevOps, QA) "
    "that completely implement the PRD features. "
    "Each ticket must have a clear title, a detailed technical description (referencing relevant files or system modules), "
    "a list of exact acceptance criteria, a Fibonacci story point estimate (1, 2, 3, 5, 8, 13), priority, and assignee role. "
    "Do not bundle massive features into a single ticket; break them down logically into small, independent milestones."
)

def run_sprint_planning(
    prd_content: str,
    feasibility_report: Optional[Dict[str, Any]] = None,
    sprint_duration_weeks: int = 2
) -> SprintPlanResponse:
    """
    Decomposes a PRD and feasibility analysis into structured sprint tickets.
    """
    prompt = (
        "## Sprint Planning Request\n\n"
        f"**Target Sprint Duration:** {sprint_duration_weeks} weeks\n\n"
        "### Product Requirement Document (PRD):\n"
        "```markdown\n"
        f"{prd_content}\n"
        "```\n\n"
    )

    if feasibility_report:
        feasibility_json = json.dumps(feasibility_report, indent=2)
        prompt += (
            "### Technical Feasibility Analysis:\n"
            "Use this report to create highly specific developer tasks referencing modified/new files and architectural changes:\n"
            "```json\n"
            f"{feasibility_json}\n"
            "```\n\n"
        )
    else:
        prompt += "### Technical Feasibility Analysis:\n*No technical feasibility report was provided. Break down the sprint plan based on general web development best practices.*\n\n"

    prompt += (
        "Please generate a complete sprint plan in the SprintPlanResponse schema.\n"
        "Make sure to:\n"
        "1. Define a clear, motivating 'sprint_goal' representing what will be shipped.\n"
        "2. Break down frontend and backend tasks separately if they are independent, or define fullstack tasks where logical.\n"
        "3. Include DevOps tasks (e.g. CI/CD setup, database migrations, server configurations) and QA/Testing tasks if needed.\n"
        "4. In the task descriptions, specify engineering implementation guidelines (e.g., what endpoints to write, validation rules, component designs).\n"
        "5. Assign story points (1, 2, 3, 5, 8, 13) realistically reflecting implementation complexity."
    )

    response = GeminiService.generate_structured_data(
        prompt=prompt,
        schema=SprintPlanResponse,
        system_instruction=SYSTEM_INSTRUCTION,
    )

    return response

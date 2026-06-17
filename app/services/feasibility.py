import os
from typing import Optional
from fastapi import HTTPException
from app.models.responses import FeasibilityResponse
from app.services.code_scanner import scan_directory
from app.services.gemini_service import GeminiService
from app.config import settings

SYSTEM_INSTRUCTION = (
    "You are an expert Software Architect and Technical Lead. Your job is to analyze a product requirement document (PRD)"
    "against an existing codebase and perform a thorough technical feasibility analysis. "
    "You must identify which files need to be modified, created, or deleted, analyze architectural alignment, point out "
    "technical risks/mitigations, list new dependencies, and estimate the effort required in hours. "
    "Be realistic, precise, and highly detail-oriented. Rely strictly on the directory file structure and code files "
    "provided to make your assessments. If no codebase is provided, perform a high-level feasibility review."
)

def run_feasibility_analysis(
    prd_content: str,
    repo_path: Optional[str] = None,
    instructions: Optional[str] = None
) -> FeasibilityResponse:
    """
    Orchestrates technical feasibility analysis of a PRD against a codebase.
    """
    codebase_context = ""
    file_tree = ""
    is_truncated = False

    # 1. Scan codebase if repo_path is provided and exists
    if repo_path:
        # Resolve user home directories or relative paths
        expanded_path = os.path.abspath(os.path.expanduser(repo_path))
        if not os.path.exists(expanded_path):
            raise HTTPException(
                status_code=400,
                detail=f"The specified repository path does not exist: {repo_path}"
            )
        
        try:
            file_tree, file_contents, is_truncated = scan_directory(
                expanded_path, 
                max_tokens=settings.MAX_SCAN_TOKENS
            )
            
            # Format codebase context for the model
            codebase_context = "### Codebase Directory Tree Structure:\n"
            codebase_context += f"```\n{file_tree}\n```\n\n"
            
            if file_contents:
                codebase_context += "### Source Code File Contents:\n"
                for path, content in file_contents.items():
                    codebase_context += f"#### File: `{path}`\n"
                    codebase_context += f"```\n{content}\n```\n\n"
            else:
                codebase_context += "*(Note: No readable text files containing source code were found or read.)*\n\n"
                
            if is_truncated:
                codebase_context += (
                    "*(WARNING: Codebase size exceeds the MAX_SCAN_TOKENS limit. "
                    "Only a subset of source files has been loaded into context. "
                    "Use the directory tree layout to infer architectural placement for other areas.)*\n\n"
                )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error while scanning the repository path: {str(e)}"
            )

    # 2. Build the LLM prompt
    prompt = (
        "## Technical Feasibility Analysis Request\n\n"
        "### Product Requirement Document (PRD):\n"
        "```markdown\n"
        f"{prd_content}\n"
        "```\n\n"
    )

    if codebase_context:
        prompt += f"## Codebase Context:\n{codebase_context}\n"
    else:
        prompt += "## Codebase Context:\n*No repository or existing codebase was provided. Analyze the feasibility generally.*\n\n"

    if instructions:
        prompt += (
            "### Custom Developer Guidelines/Focus Areas:\n"
            f"*{instructions}*\n\n"
        )

    prompt += (
        "Please evaluate the technical feasibility and construct the FeasibilityResponse JSON.\n"
        "Ensure you:\n"
        "1. Carefully map out structural file adjustments ('NEW', 'MODIFY', 'DELETE') using the absolute or relative file structure provided.\n"
        "2. Rate complexity ('Easy', 'Medium', 'Hard') and give clear, logical technical arguments.\n"
        "3. Focus on security, scale, performance and design patterns in 'technical_risks'.\n"
        "4. Estimate total engineering hours (be detailed, matching the file modification workload).\n"
    )

    # 3. Request structured analysis from the configured LLM provider (Claude/Groq/Gemini)
    response = GeminiService.generate_structured_data(
        prompt=prompt,
        schema=FeasibilityResponse,
        system_instruction=SYSTEM_INSTRUCTION,
    )
    
    return response

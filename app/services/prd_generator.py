from typing import List, Optional
from app.models.responses import PRDGenerationResponse
from app.services.gemini_service import GeminiService

SYSTEM_INSTRUCTION = (
    "You are a world-class Principal Product Manager. Your role is to take raw feature concepts, "
    "target user descriptions, business objectives, and key constraints, and generate a comprehensive, "
    "highly detailed, professional Product Requirement Document (PRD). "
    "You should flesh out functional requirements, write structured user stories (As a... I want to... So that...), "
    "define testable acceptance criteria, identify critical edge cases, clarify what is out of scope, "
    "and synthesize all of this into a publication-ready Markdown document in the 'full_markdown' field."
)

def run_prd_generation(
    feature_idea: str,
    target_audience: Optional[str] = None,
    business_objectives: Optional[str] = None,
    key_requirements: Optional[List[str]] = None,
    instructions: Optional[str] = None
) -> PRDGenerationResponse:
    """
    Orchestrates the generation of a detailed Product Requirement Document (PRD) using Gemini.
    """
    
    # 1. Build the prompt
    prompt = (
        "## Product Requirement Document (PRD) Generation Request\n\n"
        f"**Core Feature Concept / Problem Statement:**\n{feature_idea}\n\n"
    )

    if target_audience:
        prompt += f"**Target User Audience:**\n{target_audience}\n\n"
        
    if business_objectives:
        prompt += f"**Key Business Objectives:**\n{business_objectives}\n\n"
        
    if key_requirements:
        prompt += "**Essential Functional Requirements (Must-haves):**\n"
        for req in key_requirements:
            prompt += f"- {req}\n"
        prompt += "\n"
        
    if instructions:
        prompt += f"**Custom PM Instructions / Architecture Notes:**\n{instructions}\n\n"

    prompt += (
        "Please generate a complete, high-quality PRD and format it according to the PRDGenerationResponse schema.\n"
        "Ensure the 'full_markdown' field is a beautifully formatted Markdown document that includes:\n"
        "- A professional Title\n"
        "- Section headers (Executive Summary, Objectives, Target Audience, Functional Requirements, User Stories, Acceptance Criteria, Out of Scope, Edge Cases)\n"
        "- Rich formatting (bolding, lists, code blocks, alerts where appropriate)\n"
        "The document must be copy-paste ready and formatted for Confluence or Notion."
    )

    response = GeminiService.generate_structured_data(
        prompt=prompt,
        schema=PRDGenerationResponse,
        system_instruction=SYSTEM_INSTRUCTION,
    )
    
    return response

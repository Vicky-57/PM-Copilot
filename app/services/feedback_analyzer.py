from typing import List, Optional
from app.models.responses import FeedbackAnalysisResponse
from app.services.gemini_service import GeminiService

SYSTEM_INSTRUCTION = (
    "You are an expert Senior Product Operations Analyst, Customer Insights Lead, and Feedback Specialist. "
    "Your objective is to ingest a collection of customer feedback entries (support tickets, Slack messages, "
    "App Store reviews, or survey responses) and aggregate them into high-level logical themes (clusters). "
    "For each cluster, you must classify the type ('Bug', 'Feature Request', 'Usability Improvement'), "
    "evaluate the dominant user sentiment and urgency, calculate an impact score (1 to 10), summarize the main pain points, "
    "select illustrative user quotes from the input data, and recommend a clear, actionable PM next step."
)

def run_feedback_analysis(
    feedback_items: List[str],
    company_context: Optional[str] = None,
    instructions: Optional[str] = None
) -> FeedbackAnalysisResponse:
    """
    Groups, clusters, and analyzes user feedback items using Gemini.
    """
    total_items = len(feedback_items)
    
    # 1. Compile prompt
    prompt = (
        "## Customer Feedback Analysis Request\n\n"
        f"**Total Feedback Items Processed:** {total_items}\n\n"
    )

    if company_context:
        prompt += f"### Company Context:\n{company_context}\n\n"

    prompt += "### Raw Feedback Logs:\n"
    for idx, item in enumerate(feedback_items, 1):
        prompt += f"Feedback #{idx}: \"\"\"{item.strip()}\"\"\"\n"
    prompt += "\n"

    if instructions:
        prompt += f"### Custom Grouping Guidelines:\n{instructions}\n\n"

    prompt += (
        "Please analyze this data, group the inputs into logical clusters, and return a FeedbackAnalysisResponse JSON object.\n"
        "Ensure you:\n"
        "1. Correctly cluster items by topic. (e.g. if multiple feedbacks complain about slow exports, cluster them together).\n"
        "2. Keep the quotes in 'associated_quotes' verbatim from the feedback logs provided above.\n"
        "3. Provide strategic takeaways in 'key_takeaways'.\n"
        "4. Recommend actionable PM next steps (e.g., 'Generate a PRD for implementing background task scheduling')."
    )

    # 2. Call Gemini
    response = GeminiService.generate_structured_data(
        prompt=prompt,
        schema=FeedbackAnalysisResponse,
        system_instruction=SYSTEM_INSTRUCTION,
    )

    return response

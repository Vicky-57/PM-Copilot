import os
from typing import List, Optional
from app.models.responses import FeatureQAResponse, QAEvidence, VersionUpgradeResponse, UpgradeChangelogItem
from app.services.code_scanner import scan_directory
from app.services.gemini_service import GeminiService

def run_feature_qa(
    feature_specs: List[str],
    repo_path: Optional[str] = None,
    user_query: str = "",
    instructions: Optional[str] = None
) -> FeatureQAResponse:
    """
    Evaluates whether the created feature in the codebase conforms to the product launch event
    specifications, benefits, and capabilities by running code-backed Q&A audits.
    """
    resolved_path = None
    if repo_path:
        expanded_path = os.path.abspath(os.path.expanduser(repo_path))
        if os.path.isdir(expanded_path):
            resolved_path = expanded_path
        else:
            basename = os.path.basename(repo_path)
            fallback_path = os.path.abspath(basename)
            if os.path.isdir(fallback_path):
                resolved_path = fallback_path

    is_dry_run = not resolved_path
    
    if is_dry_run:
        # Simulate dry-run response
        checked_items = []
        for idx, spec in enumerate(feature_specs[:3]):
            checked_items.append(
                QAEvidence(
                    requirement=f"Spec requirement: {spec[:50]}...",
                    status="Implemented" if idx % 2 == 0 else "Partial",
                    file_references=["mock_main.py", "mock_service.py"] if idx % 2 == 0 else ["mock_view.html"],
                    details="Dry-Run: Mock verification has matched requirements to code signatures."
                )
            )
        return FeatureQAResponse(
            success=True,
            answer=(
                f"Dry-Run Mode: You asked: '{user_query}'. "
                f"Since no valid repository directory was provided, the analysis is simulated. "
                f"Generally, the code signatures seem to align with your launch event benefits."
            ),
            compliance_status="Needs Work" if any(item.status == "Partial" for item in checked_items) else "Pass",
            checked_items=checked_items
        )
        
    # Perform codebase scan
    file_tree = ""
    file_contents_str = ""
    try:
        file_tree, file_contents, _ = scan_directory(resolved_path)
        contents_list = []
        for path, content in file_contents.items():
            contents_list.append(f"File: {path}\nContent:\n{content}\n" + "="*40)
        file_contents_str = "\n".join(contents_list)
        if len(file_contents_str) > 60000:
            file_contents_str = file_contents_str[:60000] + "\n...(truncated due to context limits)..."
    except Exception as e:
        file_tree = "Failed to scan repo path"
        file_contents_str = f"Error: {str(e)}"
        
    specs_str = "\n".join(f"Requirement Document {idx+1}:\n{spec}" for idx, spec in enumerate(feature_specs))
    
    prompt = (
        f"You are an AI Product Quality Assurance Agent auditing code compliance against launch event expectations.\n"
        f"Launch Specifications & Benefits:\n"
        f"{specs_str}\n\n"
        f"Created Codebase Structure:\n"
        f"{file_tree}\n\n"
        f"Code Contents:\n"
        f"{file_contents_str}\n\n"
        f"PM's Audit Query: '{user_query}'\n"
        f"Additional verification instructions: {instructions or 'None'}\n\n"
        f"Answer the PM's question referencing code evidence, evaluate checklist items, and determine compliance status."
    )
    
    system_instruction = (
        "Analyze code contents and launch expectations objectively. Return a structured Q&A audit report. "
        "Populate the success field as True in your output."
    )
    
    try:
        qa_result = GeminiService.generate_structured_data(
            prompt=prompt,
            schema=FeatureQAResponse,
            system_instruction=system_instruction
        )
        qa_result.success = True
        return qa_result
    except Exception as e:
        return FeatureQAResponse(
            success=False,
            answer=f"Exception raised during compliance verification: {str(e)}",
            compliance_status="Mismatched",
            checked_items=[]
        )


def run_version_upgrade(
    previous_prd: str,
    upgrade_input: str,
    repo_path: Optional[str] = None,
    additional_context: Optional[List[str]] = None
) -> VersionUpgradeResponse:
    """
    Ingests previous PRD requirements, codebase layout, user instructions, and historical metrics
    to construct a unified version upgrade PRD, transition changelog, and developer migration guide.
    """
    resolved_path = None
    if repo_path:
        expanded_path = os.path.abspath(os.path.expanduser(repo_path))
        if os.path.isdir(expanded_path):
            resolved_path = expanded_path
        else:
            basename = os.path.basename(repo_path)
            fallback_path = os.path.abspath(basename)
            if os.path.isdir(fallback_path):
                resolved_path = fallback_path

    is_dry_run = not resolved_path
    
    file_tree = "Dry-Run: No codebase scanned"
    if not is_dry_run:
        try:
            file_tree, _, _ = scan_directory(resolved_path)
        except Exception as e:
            file_tree = f"Failed to scan repo path: {str(e)}"
            
    context_str = "\n".join(f"Context document {idx+1}:\n{c}" for idx, c in enumerate(additional_context or []))
    
    prompt = (
        f"You are a Senior Principal Product Manager planning the next incremental version upgrade of a product/feature.\n"
        f"Previous Version PRD:\n"
        f"{previous_prd}\n\n"
        f"Existing Codebase Directory structure:\n"
        f"{file_tree}\n\n"
        f"Additional Context (past charts, logs, metrics):\n"
        f"{context_str or 'None'}\n\n"
        f"Upgrade Instructions & Requirements:\n"
        f"{upgrade_input}\n\n"
        f"Draft the upgraded Version PRD (combining previous scope with new modifications cleanly, avoiding redundancies). "
        f"Provide a changelog detailing modified requirements and a step-by-step developer migration guide."
    )
    
    system_instruction = (
        "Draft the next version PRD and build instructions. "
        "Populate the success field as True in your output."
    )
    
    try:
        upgrade_result = GeminiService.generate_structured_data(
            prompt=prompt,
            schema=VersionUpgradeResponse,
            system_instruction=system_instruction
        )
        upgrade_result.success = True
        return upgrade_result
    except Exception as e:
        return VersionUpgradeResponse(
            success=False,
            updated_prd=f"Exception raised during version upgrade generation: {str(e)}",
            changelog=[],
            migration_complexity="High",
            migration_guide="Please try again or inspect parameters."
        )

import requests
from typing import List, Optional
from app.models.responses import PRAuditResponse, PRAuditCriterion, GitBranchResponse
from app.services.gemini_service import GeminiService
from app.config import settings

def audit_pull_request(
    repo_owner: str,
    repo_name: str,
    pr_number: int,
    acceptance_criteria: List[str],
    git_provider: str = "github"
) -> PRAuditResponse:
    """
    Fetches the pull request file changes/diffs from GitHub/GitLab,
    audits them against acceptance criteria using the LLM, and returns the checklist status.
    """
    git_provider = git_provider.lower()
    
    # 1. Determine if credentials exist for the provider
    token = settings.GITHUB_ACCESS_TOKEN if git_provider == "github" else settings.GITLAB_ACCESS_TOKEN
    is_dry_run = not token
    
    if is_dry_run:
        # Simulate PR Auditing
        criteria_checked = []
        for idx, ac in enumerate(acceptance_criteria):
            satisfied = (idx % 2 == 0)  # Alternate for mock
            criteria_checked.append(
                PRAuditCriterion(
                    criteria=ac,
                    satisfied=satisfied,
                    evidence=(
                        "Dry-Run: Found mock modifications in file_abc.py matching requirements."
                        if satisfied else
                        "Dry-Run: No code changes related to this requirement were found in the diff."
                    )
                )
            )
            
        status = "Needs Work" if any(not c.satisfied for c in criteria_checked) else "Pass"
        if not criteria_checked:
            status = "Pass"
            
        return PRAuditResponse(
            success=True,
            status=status,
            criteria_checked=criteria_checked,
            summary=(
                f"Dry-Run Mode: Simulating pull request audit check for {git_provider.capitalize()} PR #{pr_number} "
                f"in repository {repo_owner}/{repo_name}. No real API token was configured in `.env`."
            )
        )
        
    diff_summary = ""
    
    # 2. Fetch diff files from APIs
    try:
        if git_provider == "github":
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/files"
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            res = requests.get(url, headers=headers, timeout=20)
            if res.status_code != 200:
                return PRAuditResponse(
                    success=False,
                    status="Fail",
                    criteria_checked=[],
                    summary=f"GitHub API Error: Received status code {res.status_code} - {res.text}"
                )
            files = res.json()
            
            # Format diff patches
            diff_parts = []
            for f in files:
                filename = f.get("filename", "unknown_file")
                patch = f.get("patch", "(No diff details available)")
                status = f.get("status", "modified")
                diff_parts.append(f"File: {filename} ({status})\nDiff Patch:\n{patch}\n" + "-"*40)
            diff_summary = "\n".join(diff_parts)
            
        elif git_provider == "gitlab":
            proj_id = f"{repo_owner}%2F{repo_name}"
            url = f"https://gitlab.com/api/v4/projects/{proj_id}/merge_requests/{pr_number}/changes"
            headers = {"PRIVATE-TOKEN": token}
            res = requests.get(url, headers=headers, timeout=20)
            if res.status_code != 200:
                return PRAuditResponse(
                    success=False,
                    status="Fail",
                    criteria_checked=[],
                    summary=f"GitLab API Error: Received status code {res.status_code} - {res.text}"
                )
            mr_data = res.json()
            changes = mr_data.get("changes", [])
            
            diff_parts = []
            for c in changes:
                old_path = c.get("old_path", "")
                new_path = c.get("new_path", "")
                diff = c.get("diff", "(No diff details available)")
                filename = new_path if new_path == old_path else f"{old_path} -> {new_path}"
                diff_parts.append(f"File: {filename}\nDiff Patch:\n{diff}\n" + "-"*40)
            diff_summary = "\n".join(diff_parts)
            
        else:
            return PRAuditResponse(
                success=False,
                status="Fail",
                criteria_checked=[],
                summary=f"Unsupported git provider: {git_provider}"
            )
    except Exception as e:
        return PRAuditResponse(
            success=False,
            status="Fail",
            criteria_checked=[],
            summary=f"Exception raised while fetching pull request: {str(e)}"
        )
        
    if not diff_summary:
        diff_summary = "(The pull request contains no file changes or diff patches)"
        
    # Limit characters to avoid exceeding token limits
    if len(diff_summary) > 60000:
        diff_summary = diff_summary[:60000] + "\n...(truncated due to length limits)..."
        
    # 3. Call LLM to evaluate diffs against criteria
    prompt = (
        f"You are a Senior Principal Quality Engineer and Technical Lead auditing code compliance.\n"
        f"Review the following Pull Request / Merge Request changes and determine whether they satisfy the listed Acceptance Criteria.\n\n"
        f"Acceptance Criteria list:\n" + "\n".join(f"- {ac}" for ac in acceptance_criteria) + "\n\n"
        f"PR Diff and Changes:\n"
        f"{diff_summary}\n\n"
        f"Audit each criterion systematically. Determine satisfied status (True/False) and write detailed evidence referencing the files/lines modified."
    )
    
    system_instruction = (
        "Analyze the provided code diffs and objectively audit them against the acceptance criteria list. "
        "Populate the success field as True in your output."
    )
    
    try:
        audit_result = GeminiService.generate_structured_data(
            prompt=prompt,
            schema=PRAuditResponse,
            system_instruction=system_instruction
        )
        audit_result.success = True
        return audit_result
    except Exception as e:
        return PRAuditResponse(
            success=False,
            status="Fail",
            criteria_checked=[],
            summary=f"Exception raised during LLM auditing evaluation: {str(e)}"
        )


def create_git_branch(
    repo_owner: str,
    repo_name: str,
    branch_name: str,
    base_branch: str = "main",
    git_provider: str = "github"
) -> GitBranchResponse:
    """
    Creates a new branch on the remote GitHub/GitLab repository based on base_branch.
    """
    git_provider = git_provider.lower()
    token = settings.GITHUB_ACCESS_TOKEN if git_provider == "github" else settings.GITLAB_ACCESS_TOKEN
    is_dry_run = not token
    
    if is_dry_run:
        if git_provider == "github":
            branch_url = f"https://github.com/{repo_owner}/{repo_name}/tree/{branch_name}"
        else:
            branch_url = f"https://gitlab.com/{repo_owner}/{repo_name}/-/tree/{branch_name}"
            
        return GitBranchResponse(
            success=True,
            message=(
                f"Dry-Run Mode: Branch '{branch_name}' creation simulated successfully off base branch '{base_branch}'. "
                f"No remote branches were created because {git_provider.capitalize()} token is missing."
            ),
            branch_url=branch_url
        )
        
    try:
        if git_provider == "github":
            ref_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/git/ref/heads/{base_branch}"
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            res_ref = requests.get(ref_url, headers=headers, timeout=20)
            if res_ref.status_code != 200:
                return GitBranchResponse(
                    success=False,
                    message=f"GitHub reference retrieval failed: {res_ref.status_code} - {res_ref.text}",
                    branch_url=""
                )
            sha = res_ref.json().get("object", {}).get("sha")
            if not sha:
                return GitBranchResponse(
                    success=False,
                    message="Failed to retrieve base branch SHA reference.",
                    branch_url=""
                )
                
            create_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/git/refs"
            payload = {
                "ref": f"refs/heads/{branch_name}",
                "sha": sha
            }
            res_create = requests.post(create_url, headers=headers, json=payload, timeout=20)
            if res_create.status_code == 201:
                return GitBranchResponse(
                    success=True,
                    message=f"Successfully created GitHub branch '{branch_name}' off base branch '{base_branch}'.",
                    branch_url=f"https://github.com/{repo_owner}/{repo_name}/tree/{branch_name}"
                )
            else:
                return GitBranchResponse(
                    success=False,
                    message=f"GitHub branch creation failed: {res_create.status_code} - {res_create.text}",
                    branch_url=""
                )
                
        elif git_provider == "gitlab":
            proj_id = f"{repo_owner}%2F{repo_name}"
            url = f"https://gitlab.com/api/v4/projects/{proj_id}/repository/branches"
            headers = {"PRIVATE-TOKEN": token}
            payload = {
                "branch": branch_name,
                "ref": base_branch
            }
            res_create = requests.post(url, headers=headers, json=payload, timeout=20)
            if res_create.status_code == 201:
                return GitBranchResponse(
                    success=True,
                    message=f"Successfully created GitLab branch '{branch_name}' off base branch '{base_branch}'.",
                    branch_url=f"https://gitlab.com/{repo_owner}/{repo_name}/-/tree/{branch_name}"
                )
            else:
                return GitBranchResponse(
                    success=False,
                    message=f"GitLab branch creation failed: {res_create.status_code} - {res_create.text}",
                    branch_url=""
                )
        else:
            return GitBranchResponse(
                success=False,
                message=f"Unsupported git provider: {git_provider}",
                branch_url=""
            )
    except Exception as e:
        return GitBranchResponse(
            success=False,
            message=f"Exception raised during branch creation: {str(e)}",
            branch_url=""
        )

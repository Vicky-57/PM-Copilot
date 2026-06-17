import os
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

# Target repository settings (adjust these to test real GitHub branches)
REPO_OWNER = "google"
REPO_NAME = "antigravity"
GIT_PROVIDER = "github"

# Create a local mock repository to simulate a real codebase for scans
MOCK_REPO_DIR = os.path.abspath("./scratch_mock_repo")
if not os.path.exists(MOCK_REPO_DIR):
    os.makedirs(MOCK_REPO_DIR)
    with open(os.path.join(MOCK_REPO_DIR, "exporter.py"), "w") as f:
        f.write(
            "# Celery background task\n\n"
            "def compile_csv_task(rows):\n"
            "    print('Compiling CSV rows in background:', rows)\n"
            "    return True\n"
        )

print(f"Using mock repository for E2E scans: {MOCK_REPO_DIR}")

def make_request(method, path, payload=None):
    url = f"{BASE_URL}{path}"
    # Claude generates rich structured responses — allow up to 3 minutes for LLM calls
    llm_timeout = 180  # seconds
    quick_timeout = 40  # for GET and non-LLM endpoints
    try:
        if method == "GET":
            response = requests.get(url, timeout=quick_timeout)
        else:
            response = requests.post(url, json=payload, timeout=llm_timeout)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error {response.status_code} on {path}: {response.text}")
            return None
    except Exception as e:
        print(f"Request failed: {str(e)}")
        return None


def main():
    print("\n=== STARTING END-TO-END PRODUCT COPILOT FLOW ===")
    
    # ----------------------------------------------------
    # STEP 1: Ingest User Feedback
    # ----------------------------------------------------
    print("\nStep 1: Analyzing customer feedback logs...")
    feedback_payload = {
        "feedback_items": [
            "The CSV downloads time out when we have more than 5,000 users. Major blocker.",
            "CSV export is extremely slow and crashes the page on operations tab."
        ],
        "company_context": "SaaS Operations Dashboard"
    }
    feedback_res = make_request("POST", "/api/analyze-feedback", feedback_payload)
    if not feedback_res or not feedback_res.get("clusters"):
        print("E2E Stopped: Feedback analysis failed.")
        return
        
    cluster = feedback_res["clusters"][0]
    theme = cluster["theme"]
    recommended_action = cluster["recommended_action"]
    print(f"-> Extracted Theme: '{theme}'")
    print(f"-> Recommended Action: '{recommended_action}'")
    
    # ----------------------------------------------------
    # STEP 2: Generate PRD
    # ----------------------------------------------------
    print(f"\nStep 2: Drafting Product Requirement Document (PRD) for '{theme}'...")
    prd_payload = {
        "feature_idea": f"{theme} - {recommended_action}",
        "target_audience": "Operations Managers",
        "business_objectives": "Reduce user wait time and server timeouts",
        "key_requirements": [
            "Process CSV generation in the background",
            "Send email notification once finished"
        ]
    }
    prd_res = make_request("POST", "/api/generate-prd", prd_payload)
    if not prd_res or not prd_res.get("full_markdown"):
        print("E2E Stopped: PRD generation failed.")
        return
        
    prd_markdown = prd_res["full_markdown"]
    prd_title = prd_res["title"]
    print(f"-> PRD generated successfully: '{prd_title}'")
    
    # ----------------------------------------------------
    # STEP 3: Technical Feasibility Audit
    # ----------------------------------------------------
    print("\nStep 3: Evaluating codebase feasibility...")
    feasibility_payload = {
        "prd_content": prd_markdown,
        "repo_path": MOCK_REPO_DIR,
        "instructions": "Focus on background task handler implementation"
    }
    feasibility_res = make_request("POST", "/api/analyze-feasibility", feasibility_payload)
    if not feasibility_res:
        print("E2E Stopped: Feasibility analysis failed.")
        return
        
    complexity = feasibility_res["complexity"]
    effort = feasibility_res["effort_estimate_hours"]
    print(f"-> Complexity Rated: {complexity} ({feasibility_res.get('complexity_rationale')})")
    print(f"-> Estimated Effort: {effort} engineering hours")
    
    # ----------------------------------------------------
    # STEP 4: Decompose Sprint Planning
    # ----------------------------------------------------
    print("\nStep 4: Decomposing PRD and Feasibility into backlog sprint plan...")
    sprint_payload = {
        "prd_content": prd_markdown,
        "feasibility_report": feasibility_res,
        "sprint_duration_weeks": 2
    }
    sprint_res = make_request("POST", "/api/generate-sprint-plan", sprint_payload)
    if not sprint_res or not sprint_res.get("tickets"):
        print("E2E Stopped: Sprint planning failed.")
        return
        
    goal = sprint_res["sprint_goal"]
    tickets = sprint_res["tickets"]
    print(f"-> Sprint Goal: '{goal}'")
    print(f"-> Decomposed into {len(tickets)} sprint backlog tickets.")
    
    # ----------------------------------------------------
    # STEP 5: Exporting & Alerting (Notion, Jira, Linear, Slack)
    # ----------------------------------------------------
    print("\nStep 5: Synergizing integrations backlog sync...")
    
    # Export Notion Page
    notion_payload = {
        "title": prd_title,
        "content_markdown": prd_markdown
    }
    notion_res = make_request("POST", "/api/export-notion", notion_payload)
    if notion_res:
        print(f"-> Notion: {notion_res.get('message')} URL: {notion_res.get('page_url')}")
        
    # Export Jira Backlog
    jira_payload = {
        "tickets": tickets
    }
    jira_res = make_request("POST", "/api/export-jira", jira_payload)
    if jira_res:
        print(f"-> Jira: {jira_res.get('message')}")
        if jira_res.get("created_issues"):
            print(f"   Created Issue URL: {jira_res['created_issues'][0]['url']}")
            
    # Export Linear Backlog
    linear_payload = {
        "tickets": tickets
    }
    linear_res = make_request("POST", "/api/export-linear", linear_payload)
    if linear_res:
        print(f"-> Linear: {linear_res.get('message')}")
        if linear_res.get("created_issues"):
            print(f"   Created Issue URL: {linear_res['created_issues'][0]['url']}")
            
    # Post Slack Announcement
    slack_payload = {
        "sprint_goal": goal,
        "tickets": tickets,
        "custom_message": f"Successfully kicked off Sprint for PRD: {prd_title}."
    }
    slack_res = make_request("POST", "/api/export-slack", slack_payload)
    if slack_res:
        print(f"-> Slack: {slack_res.get('message')}")
        
    # ----------------------------------------------------
    # STEP 6: Dev Staging (Branch Creation & Code Verification QA)
    # ----------------------------------------------------
    print("\nStep 6: Staging developer environments & verifying compliance...")
    
    # Create Git branch
    branch_name = f"feat-{tickets[0]['id'].lower()}-background-csv"
    branch_payload = {
        "repo_owner": REPO_OWNER,
        "repo_name": REPO_NAME,
        "branch_name": branch_name,
        "git_provider": GIT_PROVIDER
    }
    branch_res = make_request("POST", "/api/create-branch", branch_payload)
    if branch_res:
        print(f"-> Branch creation status: {branch_res.get('message')} ({branch_res.get('branch_url')})")
        
    # Run Q&A compliance audit over mock repo
    qa_payload = {
        "feature_specs": prd_res["acceptance_criteria"],
        "repo_path": MOCK_REPO_DIR,
        "user_query": "Does the exporter.py codebase implement background celery compiling task?"
    }
    qa_res = make_request("POST", "/api/qa-feature", qa_payload)
    if qa_res:
        print("\n-> Feature Compliance Check Results:")
        print(f"   Status: {qa_res.get('compliance_status')}")
        print(f"   Answer: {qa_res.get('answer')}")
        
    print("\n=== END-TO-END FLOW RUN COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()

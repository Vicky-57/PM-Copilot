import os
from dotenv import load_dotenv

# Load .env file from workspace root if it exists
load_dotenv()

class Config:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    MAX_SCAN_TOKENS: int = int(os.getenv("MAX_SCAN_TOKENS", "500000"))
    
    # Jira Settings
    JIRA_URL: str = os.getenv("JIRA_URL", "")
    JIRA_EMAIL: str = os.getenv("JIRA_EMAIL", "")
    JIRA_API_TOKEN: str = os.getenv("JIRA_API_TOKEN", "")
    JIRA_PROJECT_KEY: str = os.getenv("JIRA_PROJECT_KEY", "")

    # Notion Settings
    NOTION_API_KEY: str = os.getenv("NOTION_API_KEY", "")
    NOTION_PARENT_PAGE_ID: str = os.getenv("NOTION_PARENT_PAGE_ID", "")

    # Linear Settings
    LINEAR_API_KEY: str = os.getenv("LINEAR_API_KEY", "")
    LINEAR_TEAM_ID: str = os.getenv("LINEAR_TEAM_ID", "")

    # Slack Settings
    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")

    # Git Settings
    GITHUB_ACCESS_TOKEN: str = os.getenv("GITHUB_ACCESS_TOKEN", "")
    GITLAB_ACCESS_TOKEN: str = os.getenv("GITLAB_ACCESS_TOKEN", "")



    @classmethod
    def validate(cls):
        """Simple check if essential API keys are present."""
        if not cls.GROQ_API_KEY and not cls.GEMINI_API_KEY and not cls.CLAUDE_API_KEY:
            # We don't crash, but warn so the user knows they need to configure it
            print("WARNING: No LLM API key found. Please set CLAUDE_API_KEY, GEMINI_API_KEY, or GROQ_API_KEY in your .env file.")

# Instantiate config
settings = Config()
settings.validate()


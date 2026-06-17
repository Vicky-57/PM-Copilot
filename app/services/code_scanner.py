import os
from typing import Dict, List, Tuple, Set

try:
    import pathspec
except ImportError:
    pathspec = None

DEFAULT_IGNORE_DIRS: Set[str] = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "__pycache__",
    "dist",
    "build",
    "target",
    "out",
    ".idea",
    ".vscode",
    ".next",
    ".serverless",
    "coverage",
    "bower_components",
}

DEFAULT_IGNORE_FILES: Set[str] = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Gemfile.lock",
    "Cargo.lock",
    "Pipfile.lock",
    ".DS_Store",
}

# Supported code extensions for context gathering
SUPPORTED_EXTENSIONS: Set[str] = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".rs", 
    ".c", ".cpp", ".h", ".cs", ".rb", ".php", ".sh", ".bat", 
    ".json", ".yaml", ".yml", ".toml", ".ini", ".conf",
    ".html", ".css", ".md", ".txt", ".sql", ".graphql"
}

def load_gitignore(repo_path: str):
    """Load gitignore patterns from the repository if they exist."""
    gitignore_path = os.path.join(repo_path, ".gitignore")
    if not os.path.exists(gitignore_path) or not pathspec:
        return None
    try:
        with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
            spec = pathspec.PathSpec.from_lines("gitwildmatch", f.read().splitlines())
            return spec
    except Exception as e:
        print(f"Error loading gitignore: {e}")
        return None

def is_ignored(rel_path: str, gitignore_spec, is_dir: bool = False) -> bool:
    """Check if file/directory is ignored by gitignore or defaults."""
    # Normalize paths to use forward slash for matching
    norm_path = rel_path.replace("\\", "/")
    parts = norm_path.split("/")
    
    # 1. Check default folder ignores
    for part in parts:
        if part in DEFAULT_IGNORE_DIRS:
            return True
        if not is_dir and part in DEFAULT_IGNORE_FILES:
            return True

    # 2. Check Gitignore if spec is available
    if gitignore_spec:
        # For folders, gitignore matching often requires trailing slash
        match_path = norm_path + "/" if is_dir and not norm_path.endswith("/") else norm_path
        if gitignore_spec.match_file(match_path):
            return True
            
    return False

def scan_directory(repo_path: str, max_tokens: int = 500000) -> Tuple[str, Dict[str, str], bool]:
    """
    Scans a directory recursively.
    Returns:
        - file_tree: A string representation of the directory structure
        - file_contents: A dictionary of {relative_path: file_text_content}
        - is_truncated: Boolean indicating if content reading was stopped due to token limit constraints
    """
    if not os.path.isdir(repo_path):
        raise ValueError(f"Path is not a valid directory: {repo_path}")

    gitignore_spec = load_gitignore(repo_path)
    file_tree_lines: List[str] = []
    file_contents: Dict[str, str] = {}
    
    # Track character count (approx. 4 chars = 1 token)
    max_chars = max_tokens * 4
    current_chars = 0
    is_truncated = False

    # List all files sorted to maintain consistent structure
    for root, dirs, files in os.walk(repo_path, topdown=True):
        # Calculate relative path from root
        rel_root = os.path.relpath(root, repo_path)
        if rel_root == ".":
            rel_root = ""
            
        # Filter directories in-place to avoid traversing ignored subdirs
        filtered_dirs = []
        for d in dirs:
            dir_rel = os.path.join(rel_root, d) if rel_root else d
            if not is_ignored(dir_rel, gitignore_spec, is_dir=True):
                filtered_dirs.append(d)
        dirs[:] = filtered_dirs  # Modifies in-place

        # Add to file tree and read contents
        indent = "  " * (len(rel_root.split(os.sep)) if rel_root else 0)
        
        # Add folder header to file tree
        if rel_root:
            folder_name = os.path.basename(root)
            file_tree_lines.append(f"{indent}📁 {folder_name}/")
            
        # Process files in sorted order
        for file in sorted(files):
            file_rel = os.path.join(rel_root, file) if rel_root else file
            if is_ignored(file_rel, gitignore_spec, is_dir=False):
                continue
                
            file_indent = "  " * ((len(rel_root.split(os.sep)) + 1) if rel_root else 1)
            file_tree_lines.append(f"{file_indent}📄 {file}")
            
            # Read code content if it is a supported extension
            _, ext = os.path.splitext(file.lower())
            if ext in SUPPORTED_EXTENSIONS and not is_truncated:
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        
                    if current_chars + len(content) > max_chars:
                        # Allow partial reading up to the limit
                        remaining_chars = max_chars - current_chars
                        if remaining_chars > 100:
                            file_contents[file_rel] = content[:remaining_chars] + "\n[... Content Truncated ...]"
                        is_truncated = True
                        current_chars = max_chars
                    else:
                        file_contents[file_rel] = content
                        current_chars += len(content)
                except Exception as e:
                    # Log exception silently, skip reading content of this specific file
                    print(f"Skipped reading file {file_rel} due to error: {e}")

    file_tree = "\n".join(file_tree_lines)
    return file_tree, file_contents, is_truncated

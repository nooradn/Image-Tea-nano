import os
import json
import requests
from config import BASE_PATH

def get_app_config():
    config_path = os.path.join(BASE_PATH, "configs", "app_config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_app_config(config):
    config_path = os.path.join(BASE_PATH, "configs", "app_config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def get_dev_github_token():
    token_path = os.path.join(BASE_PATH, "configs", "dev_github_token.json")
    if os.path.exists(token_path):
        with open(token_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["token"]
    return None

def fetch_latest_tag_and_commit():
    config = get_app_config()
    repo_url = config["links"]["repo"]
    if repo_url.endswith("/"):
        repo_url = repo_url[:-1]
    try:
        parts = repo_url.rstrip("/").split("/")
        owner = parts[-2]
        repo = parts[-1]
        api_url = f"https://api.github.com/repos/{owner}/{repo}/tags"
        headers = {}
        dev_token = get_dev_github_token()
        if dev_token:
            headers["Authorization"] = f"token {dev_token}"
        else:
            github_token = os.environ.get("GITHUB_TOKEN")
            if github_token:
                headers["Authorization"] = f"token {github_token}"
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
            print("No tags found in the repository.")
            return None, None
        latest_tag = data[0]["name"]
        latest_commit_sha = data[0]["commit"]["sha"][:7]
        return latest_tag, latest_commit_sha
    except Exception as e:
        print(f"Error fetching latest tag and commit: {e}")
        return None, None

def get_local_tag_and_commit():
    config = get_app_config()
    tag = config.get("tag")
    commit_hash = None
    if tag:
        # Try to get commit hash for this tag from local git if available
        git_dir = os.path.join(BASE_PATH, ".git")
        if os.path.exists(git_dir):
            try:
                import subprocess
                result = subprocess.run(
                    ["git", "-C", BASE_PATH, "rev-list", "-n", "1", tag],
                    capture_output=True, text=True, check=True
                )
                commit_hash = result.stdout.strip()[:7] if result.stdout else None
            except Exception as e:
                print(f"Error getting local commit hash for tag {tag}: {e}")
        # Fallback to config if available
        if not commit_hash:
            commit_hash = config.get("commit_hash", {}).get("local")
            if isinstance(commit_hash, str):
                commit_hash = commit_hash[:7]
    return tag, commit_hash

def update_tags_and_hashes(remote_tag, remote_hash, local_tag, local_hash):
    config = get_app_config()
    config["tag_remote"] = remote_tag
    config["tag"] = local_tag
    if "commit_hash" not in config:
        config["commit_hash"] = {}
    config["commit_hash"]["remote"] = remote_hash
    config["commit_hash"]["local"] = local_hash
    save_app_config(config)

def sync_version_with_tag():
    config = get_app_config()
    remote_hash = config["commit_hash"]["remote"]
    local_hash = config["commit_hash"]["local"]
    tag_remote = config["tag_remote"]
    if remote_hash == local_hash and tag_remote is not None:
        config["version"] = tag_remote
        save_app_config(config)

def check_for_update():
    dev_mode = os.path.exists(os.path.join(BASE_PATH, "configs", "dev_github_token.json"))
    if dev_mode:
        print("Mode: DEV (using dev_github_token.json)")
    else:
        print("Mode: USER (no dev_github_token.json)")
    remote_tag, remote_hash = fetch_latest_tag_and_commit()
    local_tag, local_hash = get_local_tag_and_commit()
    print(f"Remote tag: {remote_tag}")
    print(f"Remote commit hash: {remote_hash}")
    print(f"Local tag: {local_tag}")
    print(f"Local commit hash: {local_hash}")
    update_tags_and_hashes(remote_tag, remote_hash, local_tag, local_hash)
    if remote_tag and local_tag:
        if remote_tag != local_tag:
            print("Update available.")
        else:
            print("Kamu sudah menggunakan versi terbaru.")
    elif not remote_tag:
        print("Failed to fetch remote tag.")
    elif not local_tag:
        print("Local tag not found.")
    sync_version_with_tag()

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

def fetch_remote_commit_hash():
    config = get_app_config()
    repo_url = config["links"]["repo"]
    if repo_url.endswith("/"):
        repo_url = repo_url[:-1]
    # Supports format: https://github.com/{owner}/{repo}
    try:
        parts = repo_url.rstrip("/").split("/")
        owner = parts[-2]
        repo = parts[-1]
        api_url = f"https://api.github.com/repos/{owner}/{repo}/commits/main"
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
        return data["sha"]
    except Exception as e:
        print(f"Error fetching remote commit hash: {e}")
        return None

def get_local_commit_hash():
    config = get_app_config()
    commit_hash = config["commit_hash"]
    return commit_hash["local"]

def update_commit_hashes(remote_hash, local_hash):
    config = get_app_config()
    if "commit_hash" not in config:
        config["commit_hash"] = {}
    config["commit_hash"]["remote"] = remote_hash
    config["commit_hash"]["local"] = local_hash
    save_app_config(config)

def check_for_update():
    dev_mode = os.path.exists(os.path.join(BASE_PATH, "configs", "dev_github_token.json"))
    if dev_mode:
        print("Mode: DEV (using dev_github_token.json)")
    else:
        print("Mode: USER (no dev_github_token.json)")
    remote_hash = fetch_remote_commit_hash()
    local_hash = get_local_commit_hash()
    print(f"Remote commit hash: {remote_hash}")
    print(f"Local commit hash: {local_hash}")
    update_commit_hashes(remote_hash, local_hash)
    if remote_hash and local_hash:
        if remote_hash != local_hash:
            print("Update available.")
        else:
            print("You are already using the latest version.")
    elif not remote_hash:
        print("Failed to fetch remote commit hash.")
    elif not local_hash:
        print("Local commit hash not found.")

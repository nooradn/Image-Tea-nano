import os
import json
import requests
from datetime import datetime
from config import BASE_PATH

def get_app_config():
    config_path = os.path.join(BASE_PATH, "configs", "app_config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_app_config(config):
    config_path = os.path.join(BASE_PATH, "configs", "app_config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def get_update_config():
    update_path = os.path.join(BASE_PATH, "configs", "update_config.json")
    if os.path.exists(update_path):
        with open(update_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_update_config(update_config):
    update_path = os.path.join(BASE_PATH, "configs", "update_config.json")
    with open(update_path, "w", encoding="utf-8") as f:
        json.dump(update_config, f, ensure_ascii=False, indent=4)

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
    version = config["version"]
    tag = version
    if not tag.startswith("v"):
        tag = "v" + tag
    commit_hash = None
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
    return tag, commit_hash

def update_update_config(remote_tag, remote_hash, local_tag, local_hash):
    update_config = get_update_config()
    now_iso = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    if "update" not in update_config:
        update_config["update"] = {}
    update_config["commit_hash"] = {
        "remote": remote_hash,
        "local": local_hash
    }
    update_config["update"]["last_checked"] = now_iso
    if "last_update" not in update_config["update"]:
        update_config["update"]["last_update"] = now_iso
    update_config["tag_remote"] = remote_tag
    update_config["tag_local"] = local_tag
    save_update_config(update_config)

def check_for_update():
    remote_tag, remote_hash = fetch_latest_tag_and_commit()
    local_tag, local_hash = get_local_tag_and_commit()
    update_update_config(remote_tag, remote_hash, local_tag, local_hash)
    if remote_tag and local_tag:
        if remote_tag != local_tag or remote_hash != local_hash:
            print("Update available.")
    elif not remote_tag:
        print("Failed to fetch remote tag.")
    elif not local_tag:
        print("Local tag not found.")
    update_update_config(remote_tag, remote_hash, local_tag, local_hash)
    if remote_tag and local_tag:
        if remote_tag != local_tag:
            print("Update available.")
        else:
            print("You are already using the latest version.")
    elif not remote_tag:
        print("Failed to fetch remote tag.")
    elif not local_tag:
        print("Local tag not found.")

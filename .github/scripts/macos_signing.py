"""Select the newest integrated upstream tag for a personal macOS release."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tool"))
from macos_dmg import TAG_RE, distribution_version
SIGNING_REPOSITORY = "wjlfish/Bugaoshan-macos"
def run(*args, cwd=None, check=True):
    return subprocess.run(args, cwd=cwd, check=check, capture_output=True, text=True)
def git(source, *args):
    return run("git", *args, cwd=source).stdout.strip()
def select(source, requested=""):
    tags = git(source, "for-each-ref", "--sort=-creatordate", "--format=%(refname:short)", "refs/tags/v*").splitlines()
    tags = [tag for tag in tags if TAG_RE.fullmatch(tag)]
    if requested:
        if requested not in tags:
            raise ValueError("Requested upstream tag does not exist")
        tags = [requested]
    if not tags:
        return {"ready": "false"}
    tag = tags[0]
    existing = run("gh", "release", "view", f"macos-{tag}", "--repo", SIGNING_REPOSITORY,
                   "--json", "isDraft", check=False)
    if existing.returncode == 0 and not json.loads(existing.stdout)["isDraft"]:
        return {"ready": "false"}
    if existing.returncode and "not found" not in existing.stderr.lower() and "404" not in existing.stderr:
        raise RuntimeError(f"Cannot check personal release: {existing.stderr}")
    sha = git(source, "rev-parse", f"{tag}^{{commit}}")
    if not any(run("git", "merge-base", "--is-ancestor", sha, f"origin/{branch}",
                   cwd=source, check=False).returncode == 0 for branch in ("main", "preview")):
        raise ValueError("Release tag is outside upstream main/preview")
    config = Path(__file__).resolve().parents[1] / "macos-signing.json"
    version, build = distribution_version(json.loads(config.read_text()))
    return {"tag": tag, "sha": sha, "version": version, "build": build, "ready": "true"}
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("source"))
    parser.add_argument("--tag", default="")
    args = parser.parse_args()
    values = select(args.source, args.tag)
    text = "".join(f"{key}={value}\n" for key, value in values.items())
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
        stream.write(text)
    print(text, end="")
if __name__ == "__main__":
    main()

import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
BRANCHES_FILE = BASE_DIR / "data" / "branches.json"


def load_branches():
    with open(BRANCHES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)["branches"]


def get_branch_by_id(branch_id):
    branches = load_branches()

    for branch in branches:
        if branch["id"] == branch_id:
            return branch

    return None
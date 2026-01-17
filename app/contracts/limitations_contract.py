# app/contracts/limitations_contract.py

def generate_limitations(issues: list[dict]) -> list[str]:
    limitations = []

    for issue in issues:
        if issue["severity"] in ("critical", "high", "medium"):
            limitations.append(issue["description"])

    return sorted(set(limitations))

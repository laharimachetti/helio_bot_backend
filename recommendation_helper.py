from db_help import fetch_cutoffs_all_years


def normalize_branch(branch: str) -> str:
    b = branch.lower()

    if "cse" in b or "computer" in b:
        return "Computer Science"
    if "it" in b or "information" in b:
        return "Information Technology"
    if "ece" in b or "electronics" in b:
        return "Electronics"
    if "eee" in b or "electrical" in b:
        return "Electrical"
    if "mech" in b or "mechanical" in b:
        return "Mechanical"
    if "civil" in b:
        return "Civil"

    return branch


def get_recommendations(rank, branch):
    """
    rank: int (required)
    branch: str (required)
    """

    if not branch:
        return []

    normalized_branch = normalize_branch(branch)

    # ✅ CORRECT ORDER: (branch, rank)
    return fetch_cutoffs_all_years(normalized_branch, rank)

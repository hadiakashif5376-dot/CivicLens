"""Pure workflow rules, free of web and database code so they are easy to test."""

NEXT_STATUS = {"Assigned": "In Progress", "In Progress": "Resolved"}


def can_assign(current: str) -> bool:
    return current == "Submitted"


def can_move(current: str, requested: str) -> bool:
    return NEXT_STATUS.get(current) == requested


def make_ref(row_id: int) -> str:
    return f"SC-{1000 + row_id}"

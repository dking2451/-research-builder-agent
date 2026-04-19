"""Research mode wrapper (prompting handled centrally in `prompts.mode_prompts`)."""


def build_project_context_block(*, title: str, goal: str | None, description: str | None) -> str:
    parts = [f"Title: {title}"]
    if goal:
        parts.append(f"Goal: {goal}")
    if description:
        parts.append(f"Description: {description}")
    return "\n".join(parts)

def build_caption(original: str | None, automation_caption: str | None) -> str | None:
    if automation_caption:
        if original:
            return f"{original}\n\n{automation_caption}"
        return automation_caption
    return original

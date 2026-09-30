def ordered_union(current: list[str] | None, new: list[str] | None) -> list[str]:
    """`current` plus the items of `new` not in it yet, in first-seen order."""
    merged = list(current or [])
    merged += [item for item in new or [] if item not in merged]
    return merged

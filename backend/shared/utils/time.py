def format_time(minutes: int) -> str:
    """Format minutes into readable time string.

    Args:
        minutes: Duration in minutes

    Returns:
        Formatted string like "~25 mins" or "1 h 30 mins"
    """
    if minutes < 60:
        return f"~{minutes} min" if minutes == 1 else f"~{minutes} mins"
    else:
        hours = minutes // 60
        mins = minutes % 60
        if mins == 0:
            return f"{hours} h" if hours == 1 else f"{hours} hrs"
        else:
            h_str = f"{hours} h" if hours == 1 else f"{hours} hrs"
            m_str = f"{mins} min" if mins == 1 else f"{mins} mins"
            return f"{h_str} {m_str}"


def add_buffer_time(minutes: int, buffer_minutes: int = 5) -> int:
    """Add buffer time to duration (for transfers, walking, etc).

    Args:
        minutes: Original duration
        buffer_minutes: Buffer to add (default 5 mins)

    Returns:
        Total time with buffer
    """
    return minutes + buffer_minutes

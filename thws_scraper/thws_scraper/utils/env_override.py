import os


def get_setting(settings, key, default=None, cast=str):
    """
    Load a setting from Scrapy settings,
    then override with ENV variable if available.

    Args:
        settings: Scrapy settings
        key: Setting name (also ENV var name)
        default: Default value if not found
        cast: Function to cast the value (str, bool, int)

    Returns:
        The final value (cast to correct type)
    """
    value = settings.get(key, default)

    # Check if environment variable exists
    env_value = os.getenv(key)
    if env_value is not None:
        value = env_value

    # Try casting the value to correct type
    try:
        if cast == bool:
            value = str(value).lower() in ("1", "true", "yes", "on")
        else:
            value = cast(value)
    except Exception:
        pass  # fallback to raw if casting fails

    return value

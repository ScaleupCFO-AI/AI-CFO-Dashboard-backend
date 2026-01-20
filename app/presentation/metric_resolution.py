from app.presentation.kpi_registry import METRIC_PROXIES

def resolve_metric_or_proxy(
    requested_metric: str,
    available_metrics: set[str]
) -> tuple[str | None, bool]:
    """
    Returns:
    - (metric_to_use, is_proxy)

    If neither metric nor proxy is available → (None, False)
    """

    # Direct metric exists
    if requested_metric in available_metrics:
        return requested_metric, False

    # Try approved proxies
    for proxy in METRIC_PROXIES.get(requested_metric, []):
        if proxy in available_metrics:
            return proxy, True

    return None, False

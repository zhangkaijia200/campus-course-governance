from prometheus_client import Counter, Histogram

HTTP_REQUESTS = Counter(
    "course_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

HTTP_DURATION = Histogram(
    "course_http_request_duration_seconds",
    "HTTP request duration",
    ["method", "path"],
)

SELECTION_RESULTS = Counter(
    "course_selection_results_total",
    "Course selection outcomes",
    ["mode", "result"],
)

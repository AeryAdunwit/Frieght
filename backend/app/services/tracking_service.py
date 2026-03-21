from __future__ import annotations

from ...tracking import (
    build_tracking_context,
    extract_job_number,
    format_tracking_response,
    get_tracking_prompt,
    is_tracking_request,
    lookup_tracking,
)


class TrackingService:
    build_context = staticmethod(build_tracking_context)
    extract_job_number = staticmethod(extract_job_number)
    format_response = staticmethod(format_tracking_response)
    get_prompt = staticmethod(get_tracking_prompt)
    is_tracking_request = staticmethod(is_tracking_request)
    lookup = staticmethod(lookup_tracking)


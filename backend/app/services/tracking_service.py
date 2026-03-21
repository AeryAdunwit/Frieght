from __future__ import annotations

import httpx
from fastapi.responses import HTMLResponse, JSONResponse

from ..config import AppSettings
from ...tracking import (
    build_tracking_context,
    extract_job_number,
    format_tracking_response,
    get_tracking_prompt,
    is_tracking_request,
    lookup_tracking,
)


class TrackingService:
    def __init__(self, settings: AppSettings | None = None):
        self.settings = settings or AppSettings()

    build_context = staticmethod(build_tracking_context)
    extract_job_number = staticmethod(extract_job_number)
    format_response = staticmethod(format_tracking_response)
    get_prompt = staticmethod(get_tracking_prompt)
    is_tracking_request = staticmethod(is_tracking_request)
    lookup = staticmethod(lookup_tracking)

    def get_public_config(self) -> dict[str, str | bool]:
        return {
            "admin_auth_enabled": bool(self.settings.admin_api_key),
            "scg_recaptcha_site_key": self.settings.scg_recaptcha_site_key,
        }

    async def porlor_tracking_search(self, track: str) -> HTMLResponse:
        from ..dependencies import get_security_service

        security_service = get_security_service()

        track = track.strip()
        if not track:
            return HTMLResponse(
                "<div style='padding:16px;font-family:Segoe UI,Tahoma,sans-serif;'>ยังไม่มีเลข DO ให้ค้าบ</div>"
            )

        search_url = "https://rfe.co.th/hc_rfeweb/trackingweb/search"
        popup_absolute = "https://rfe.co.th/hc_rfeweb/trackingweb/popupImg?AWB_CODE="

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                response = await client.post(
                    search_url,
                    data={"awb": "", "trackID": track, "page_no": "1", "per_page": "10"},
                    headers={
                        "Origin": "https://rfe.co.th",
                        "Referer": "https://rfe.co.th/hc_rfeweb/trackingweb",
                        "User-Agent": "Mozilla/5.0",
                    },
                )
                response.raise_for_status()
            except Exception as exc:
                security_service.log_server_error("porlor_tracking_search", exc)
                return HTMLResponse(
                    (
                        "<div style='padding:16px;font-family:Segoe UI,Tahoma,sans-serif;'>"
                        "ยังดึงผลค้นหา Porlor ไม่ได้ค้าบ ลองเปิดเว็บต้นทางอีกครั้งได้เลย"
                        "</div>"
                    ),
                    status_code=502,
                )

        html = response.text
        html = html.replace("Trackingweb/popupImg?AWB_CODE=", popup_absolute)
        html = html.replace(
            "window.open('Trackingweb/popupImg?AWB_CODE=' + AWB_CODE, 'popup-name',",
            "window.open('https://rfe.co.th/hc_rfeweb/trackingweb/popupImg?AWB_CODE=' + AWB_CODE, '_blank',",
        )
        html = html.replace(
            "<head>",
            "<head><base href='https://rfe.co.th/hc_rfeweb/' target='_self'>",
        )

        return HTMLResponse(html)

    async def scg_tracking(self, number: str, token: str) -> JSONResponse | dict[str, object]:
        from ..dependencies import get_security_service

        security_service = get_security_service()

        number = number.strip()
        token = token.strip()

        if not number:
            return JSONResponse(status_code=400, content={"error": "number is required"})
        if not token:
            return JSONResponse(status_code=400, content={"error": "token is required"})

        api_url = "https://www.scgjwd.com/nx/API/get_tracking"
        headers = {
            "Origin": "https://www.scgjwd.com",
            "Referer": f"https://www.scgjwd.com/tracking?tracking_number={number}",
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest",
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                response = await client.post(
                    api_url,
                    data={"number": number, "token": token},
                    headers=headers,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                security_service.log_server_error("scg_tracking_status", exc)
                return JSONResponse(
                    status_code=502,
                    content={"error": "SCG tracking request failed"},
                )
            except Exception as exc:
                security_service.log_server_error("scg_tracking", exc)
                return JSONResponse(
                    status_code=502,
                    content={"error": "SCG tracking request failed"},
                )

        try:
            payload = response.json()
        except ValueError as exc:
            security_service.log_server_error("scg_tracking_non_json", exc)
            return JSONResponse(
                status_code=502,
                content={"error": "SCG tracking response was not JSON"},
            )

        return {"ok": True, "number": number, "payload": payload}

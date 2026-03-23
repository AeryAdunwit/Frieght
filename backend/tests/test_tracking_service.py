import unittest
from unittest.mock import patch

import httpx
from fastapi.responses import HTMLResponse, JSONResponse

from backend.app.services.tracking_service import TrackingService


class _FakeResponse:
    def __init__(self, *, text: str = "", json_payload=None, status_error: Exception | None = None):
        self.text = text
        self._json_payload = json_payload if json_payload is not None else {}
        self._status_error = status_error

    def raise_for_status(self):
        if self._status_error:
            raise self._status_error

    def json(self):
        return self._json_payload


class _FakeAsyncClient:
    def __init__(self, response_or_error):
        self._response_or_error = response_or_error

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs):
        if isinstance(self._response_or_error, Exception):
            raise self._response_or_error
        return self._response_or_error


class TrackingServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_porlor_tracking_search_returns_502_on_request_error(self):
        service = TrackingService()
        request = httpx.Request("POST", "https://rfe.co.th/hc_rfeweb/trackingweb/search")
        error = httpx.ConnectError("network down", request=request)

        with patch("backend.app.services.tracking_service.httpx.AsyncClient", return_value=_FakeAsyncClient(error)):
            response = await service.porlor_tracking_search("1314640315")

        self.assertIsInstance(response, HTMLResponse)
        self.assertEqual(response.status_code, 502)

    async def test_scg_tracking_returns_502_on_http_error(self):
        service = TrackingService()
        request = httpx.Request("POST", "https://www.scgjwd.com/nx/API/get_tracking")
        response = httpx.Response(500, request=request)
        fake_response = _FakeResponse(status_error=httpx.HTTPStatusError("boom", request=request, response=response))

        with patch("backend.app.services.tracking_service.httpx.AsyncClient", return_value=_FakeAsyncClient(fake_response)):
            result = await service.scg_tracking("1314639759", "token")

        self.assertIsInstance(result, JSONResponse)
        self.assertEqual(result.status_code, 502)

    async def test_scg_tracking_returns_payload_on_success(self):
        service = TrackingService()
        fake_response = _FakeResponse(json_payload={"status": "ok", "tracking_number": "1314639759"})

        with patch("backend.app.services.tracking_service.httpx.AsyncClient", return_value=_FakeAsyncClient(fake_response)):
            result = await service.scg_tracking("1314639759", "token")

        self.assertEqual(result.ok, True)
        self.assertEqual(result.number, "1314639759")
        self.assertEqual(result.payload["status"], "ok")


if __name__ == "__main__":
    unittest.main()

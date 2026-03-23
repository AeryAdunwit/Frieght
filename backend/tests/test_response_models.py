import unittest

from backend.app.models.responses import (
    BasicHealthResponse,
    ChatOverviewResponse,
    DeepHealthResponse,
    HealthCheckItem,
    PublicConfigResponse,
    ScgTrackingResponse,
    VisitMetricsResponse,
)


class ResponseModelsTestCase(unittest.TestCase):
    def test_basic_health_response_dump(self):
        payload = BasicHealthResponse(status="ok")
        self.assertEqual(payload.model_dump(), {"status": "ok"})

    def test_public_config_response_dump(self):
        payload = PublicConfigResponse(
            admin_auth_enabled=True,
            scg_recaptcha_site_key="site-key",
        )
        self.assertTrue(payload.admin_auth_enabled)
        self.assertEqual(payload.scg_recaptcha_site_key, "site-key")

    def test_visit_metrics_response_dump(self):
        payload = VisitMetricsResponse(count=10, page_views_total=10, unique_visitors_total=3)
        self.assertEqual(payload.model_dump()["unique_visitors_total"], 3)

    def test_deep_health_response_nested_models(self):
        payload = DeepHealthResponse(
            status="ok",
            service="frieght-backend",
            checked_at="2026-03-22T00:00:00+00:00",
            checks={
                "supabase": HealthCheckItem(status="ok", configured=True, rows_checked=1),
                "gemini": HealthCheckItem(status="ok", configured=True),
            },
        )
        self.assertEqual(payload.checks["supabase"].rows_checked, 1)
        self.assertEqual(payload.model_dump()["checks"]["gemini"]["status"], "ok")

    def test_scg_tracking_response_payload(self):
        payload = ScgTrackingResponse(ok=True, number="1314639759", payload={"status": "ok"})
        self.assertEqual(payload.payload["status"], "ok")

    def test_chat_overview_response_dump(self):
        payload = ChatOverviewResponse(
            generated_at="2026-03-23T00:00:00+00:00",
            days=7,
            filters={"intent_name": "solar"},
            totals={"chat_messages": 10},
            daily_workflow={"review_date": "2026-03-23"},
            weekly_summary={"period_days": 7},
            sla_dashboard={"under_1d": 3},
            top_unresolved_reasons=[{"label": "tracking not found", "count": 2}],
            repository_errors=["fetch_feedback_rows: timeout"],
        )
        dumped = payload.model_dump()
        self.assertEqual(dumped["days"], 7)
        self.assertEqual(dumped["repository_errors"][0], "fetch_feedback_rows: timeout")


if __name__ == "__main__":
    unittest.main()

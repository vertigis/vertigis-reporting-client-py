# pylint: disable=line-too-long,missing-class-docstring,missing-function-docstring

import json
import unittest
# Swap for unittest.IsolatedAsyncioTestCase if we drop Python < 3.8
import aiounittest
import responses

from geocortex.reporting.client import run

MOCK_PORTAL_ITEM_ID = "mock-portal-item-id"
MOCK_PORTAL_TOKEN = "mock-portal-token"

MOCK_REPORTING_TOKEN = "mock-reporting-token"
MOCK_REPORT_TICKET = "mock-report-ticket"
MOCK_REPORT_TAG = "mock-report-tag"

DEFAULT_REPORTING_URL = "https://apps.geocortex.com/reporting"
DEFAULT_PORTAL_URL = "https://www.arcgis.com"


def setup_default_responses(
    rsps, *, reporting_url=DEFAULT_REPORTING_URL, portal_url=DEFAULT_PORTAL_URL,
):
    rsps.add(
        responses.GET,
        f"{portal_url}/sharing/rest/content/items/{MOCK_PORTAL_ITEM_ID}?f=json",
        json={"access": "public", "url": f"{reporting_url}/"},
        status=200,
    )

    rsps.add(
        responses.GET,
        f"{reporting_url}/service/job/artifacts?ticket={MOCK_REPORT_TICKET}",
        json={
            "results": [
                {
                    "$type": "JobResult",
                    "contentType": "application/pdf",
                    "tag": MOCK_REPORT_TAG,
                    "length": 24003,
                },
                {"$type": "JobQuit", "kind": "Run"},
            ],
        },
        status=200,
    )

    rsps.add(
        responses.POST,
        f"{reporting_url}/service/job/run",
        json={"response": {"$type": "TokenResponse", "ticket": MOCK_REPORT_TICKET}},
        status=200,
    )


class TestReporting(aiounittest.AsyncTestCase):
    async def test_basic(self):
        with responses.RequestsMock() as rsps:
            setup_default_responses(rsps)

            report = await run(MOCK_PORTAL_ITEM_ID, use_polling=True)

            self.assertEqual(
                report,
                f"{DEFAULT_REPORTING_URL}/service/job/result?ticket={MOCK_REPORT_TICKET}&tag={MOCK_REPORT_TAG}",
            )

    async def test_with_token(self):
        with responses.RequestsMock() as rsps:
            setup_default_responses(rsps)
            rsps.remove(
                responses.GET,
                f"{DEFAULT_PORTAL_URL}/sharing/rest/content/items/{MOCK_PORTAL_ITEM_ID}?f=json",
            )
            rsps.add(
                responses.GET,
                f"{DEFAULT_PORTAL_URL}/sharing/rest/content/items/{MOCK_PORTAL_ITEM_ID}?f=json&token={MOCK_PORTAL_TOKEN}",
                json={"access": "private", "url": f"{DEFAULT_REPORTING_URL}/",},
                status=200,
            )
            rsps.add(
                responses.POST,
                f"{DEFAULT_REPORTING_URL}/service/auth/token/run",
                json={"response": {"token": MOCK_REPORTING_TOKEN}},
                status=200,
            )

            report = await run(
                MOCK_PORTAL_ITEM_ID, use_polling=True, token=MOCK_PORTAL_TOKEN
            )

            self.assertEqual(
                report,
                f"{DEFAULT_REPORTING_URL}/service/job/result?ticket={MOCK_REPORT_TICKET}&tag={MOCK_REPORT_TAG}",
            )
            job_run_call = next(
                x
                for x in rsps.calls
                if x.request.url == f"{DEFAULT_REPORTING_URL}/service/job/run"
            )
            self.assertEqual(
                job_run_call.request.headers["Authorization"],
                f"Bearer {MOCK_REPORTING_TOKEN}",
                "Sends bearer token in job run request",
            )

    async def test_param_forwarding(self):
        with responses.RequestsMock() as rsps:
            setup_default_responses(rsps)

            await run(
                MOCK_PORTAL_ITEM_ID,
                use_polling=True,
                # Following should be passed in job params
                bool=True,
                dict={"foo": "bar"},
                list=["foo", "bar"],
                num=42,
                str="foo",
                tuple=(1, 2),
            )

            job_run_call = next(
                x
                for x in rsps.calls
                if x.request.url == f"{DEFAULT_REPORTING_URL}/service/job/run"
            )
            self.assertEqual(
                json.loads(job_run_call.request.body),
                {
                    "template": {
                        "itemId": MOCK_PORTAL_ITEM_ID,
                        "portalUrl": DEFAULT_PORTAL_URL,
                    },
                    "parameters": [
                        {
                            "name": "bool",
                            "containsMultipleValues": False,
                            "value": True,
                        },
                        {
                            "name": "dict",
                            "containsMultipleValues": False,
                            "value": {"foo": "bar"},
                        },
                        {
                            "name": "list",
                            "containsMultipleValues": True,
                            "values": ["foo", "bar"],
                        },
                        {"name": "num", "containsMultipleValues": False, "value": 42,},
                        {
                            "name": "str",
                            "containsMultipleValues": False,
                            "value": "foo",
                        },
                        {
                            "name": "tuple",
                            "containsMultipleValues": True,
                            "values": [1, 2],
                        },
                    ],
                },
            )

    async def test_passes_culture_as_job_arg(self):
        with responses.RequestsMock() as rsps:
            setup_default_responses(rsps)

            await run(MOCK_PORTAL_ITEM_ID, use_polling=True, culture="fr-CA")

            job_run_call = next(
                x
                for x in rsps.calls
                if x.request.url == f"{DEFAULT_REPORTING_URL}/service/job/run"
            )
            self.assertEqual(
                json.loads(job_run_call.request.body),
                {
                    "template": {
                        "itemId": MOCK_PORTAL_ITEM_ID,
                        "portalUrl": DEFAULT_PORTAL_URL,
                    },
                    "parameters": [],
                    "culture": "fr-CA",
                },
            )

    async def test_uses_result_name_in_template(self):
        with responses.RequestsMock() as rsps:
            setup_default_responses(rsps)

            await run(MOCK_PORTAL_ITEM_ID, use_polling=True, result_name="My Report")

            job_run_call = next(
                x
                for x in rsps.calls
                if x.request.url == f"{DEFAULT_REPORTING_URL}/service/job/run"
            )
            self.assertEqual(
                json.loads(job_run_call.request.body),
                {
                    "template": {
                        "itemId": MOCK_PORTAL_ITEM_ID,
                        "portalUrl": DEFAULT_PORTAL_URL,
                        "title": "My Report"
                    },
                    "parameters": [],
                },
            )

    async def test_uses_reporting_service_url(self):
        with responses.RequestsMock() as rsps:
            reporting_url = "https://on-prem/reporting"
            setup_default_responses(rsps, reporting_url=reporting_url)

            report = await run(MOCK_PORTAL_ITEM_ID, use_polling=True)

            self.assertEqual(
                report,
                f"{reporting_url}/service/job/result?ticket={MOCK_REPORT_TICKET}&tag={MOCK_REPORT_TAG}",
            )

    async def test_uses_portal_url(self):
        with responses.RequestsMock() as rsps:
            portal_url = "https://on-prem-portal"
            setup_default_responses(rsps, portal_url=portal_url)

            report = await run(
                MOCK_PORTAL_ITEM_ID, portal_url=portal_url, use_polling=True
            )

            self.assertEqual(
                report,
                f"{DEFAULT_REPORTING_URL}/service/job/result?ticket={MOCK_REPORT_TICKET}&tag={MOCK_REPORT_TAG}",
            )

    async def test_raises_when_portal_item_not_found(self):
        with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
            setup_default_responses(rsps)
            rsps.replace(
                responses.GET,
                f"{DEFAULT_PORTAL_URL}/sharing/rest/content/items/{MOCK_PORTAL_ITEM_ID}?f=json",
                json={
                    "error": {
                        "code": 400,
                        "messageCode": "CONT_0001",
                        "message": "Item does not exist or is inaccessible.",
                        "details": [],
                    }
                },
                status=200,
            )

            with self.assertRaises(Exception) as context_manager:
                await run(MOCK_PORTAL_ITEM_ID, use_polling=True)

            self.assertEqual(
                str(context_manager.exception),
                "Error retrieving portal item: Item does not exist or is inaccessible.",
            )

    async def test_raises_when_job_finishes_without_artifact(self):
        with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
            setup_default_responses(rsps)
            rsps.replace(
                responses.GET,
                f"{DEFAULT_REPORTING_URL}/service/job/artifacts?ticket={MOCK_REPORT_TICKET}",
                json={
                    "results": [
                        # 'JobResult' is missing from results
                        {"$type": "JobQuit", "kind": "Run"},
                    ],
                },
                status=200,
            )

            with self.assertRaises(Exception,) as context_manager:
                await run(MOCK_PORTAL_ITEM_ID, use_polling=True)

            self.assertEqual(
                str(context_manager.exception),
                f"Report job failed to produce an artifact. See the logs for more details: {DEFAULT_REPORTING_URL}/service/job/logs?ticket={MOCK_REPORT_TICKET}",
            )


class TestPrinting(aiounittest.AsyncTestCase):
    async def test_passes_dpi_as_job_arg(self):
        with responses.RequestsMock() as rsps:
            setup_default_responses(rsps)

            await run(MOCK_PORTAL_ITEM_ID, use_polling=True, dpi=42)

            job_run_call = next(
                x
                for x in rsps.calls
                if x.request.url == f"{DEFAULT_REPORTING_URL}/service/job/run"
            )
            self.assertEqual(
                json.loads(job_run_call.request.body),
                {
                    "template": {
                        "itemId": MOCK_PORTAL_ITEM_ID,
                        "portalUrl": DEFAULT_PORTAL_URL,
                    },
                    "parameters": [],
                    "dpi": 42,
                },
            )


if __name__ == "__main__":
    unittest.main()

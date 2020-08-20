import json
import requests
import responses
import unittest
import websockets

from unittest import mock

from geocortex.reporting.client import run

MOCK_PORTAL_ITEM_ID = "mock-portal-item-id"
MOCK_PORTAL_TOKEN = "mock-portal-token"

MOCK_REPORTING_TOKEN = "mock-reporting-token"
MOCK_REPORT_TICKET = "mock-report-ticket"
MOCK_REPORT_TAG = "mock-report-tag"

DEFAULT_REPORTING_URL = "https://apps.geocortex.com/reporting"
DEFAULT_PORTAL_URL = "https://www.arcgis.com"


def setupDefaultResponses(
    rsps, reportingUrl=DEFAULT_REPORTING_URL, portalUrl=DEFAULT_PORTAL_URL,
):
    rsps.add(
        responses.GET,
        f"{portalUrl}/sharing/rest/content/items/{MOCK_PORTAL_ITEM_ID}?f=json",
        json={"access": "public", "url": f"{reportingUrl}/"},
        status=200,
    )

    rsps.add(
        responses.GET,
        f"{reportingUrl}/service/job/artifacts?ticket={MOCK_REPORT_TICKET}",
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
        f"{reportingUrl}/service/job/run",
        json={"response": {"$type": "TokenResponse", "ticket": MOCK_REPORT_TICKET}},
        status=200,
    )


class TestReporting(unittest.IsolatedAsyncioTestCase):
    async def test_basic(self):
        with responses.RequestsMock() as rsps:
            setupDefaultResponses(rsps)

            report = await run(MOCK_PORTAL_ITEM_ID, usePolling=True)

            self.assertEqual(
                report,
                f"{DEFAULT_REPORTING_URL}/service/job/result?ticket={MOCK_REPORT_TICKET}&tag={MOCK_REPORT_TAG}",
            )

    async def test_with_token(self):
        with responses.RequestsMock() as rsps:
            setupDefaultResponses(rsps)
            rsps.replace(
                responses.GET,
                f"{DEFAULT_PORTAL_URL}/sharing/rest/content/items/{MOCK_PORTAL_ITEM_ID}?f=json",
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
                MOCK_PORTAL_ITEM_ID, usePolling=True, token=MOCK_PORTAL_TOKEN
            )

            self.assertEqual(
                report,
                f"{DEFAULT_REPORTING_URL}/service/job/result?ticket={MOCK_REPORT_TICKET}&tag={MOCK_REPORT_TAG}",
            )
            jobRunCall = next(
                x
                for x in rsps.calls
                if x.request.url == f"{DEFAULT_REPORTING_URL}/service/job/run"
            )
            self.assertEqual(
                jobRunCall.request.headers["Authorization"],
                f"Bearer {MOCK_REPORTING_TOKEN}",
                "Sends bearer token in job run request",
            )

    async def test_param_forwarding(self):
        with responses.RequestsMock() as rsps:
            setupDefaultResponses(rsps)

            await run(
                MOCK_PORTAL_ITEM_ID,
                usePolling=True,
                # Following should be passed in job params
                bool=True,
                dict={"foo": "bar"},
                list=["foo", "bar"],
                num=42,
                str="foo",
                tuple=(1, 2),
            )

            jobRunCall = next(
                x
                for x in rsps.calls
                if x.request.url == f"{DEFAULT_REPORTING_URL}/service/job/run"
            )
            self.assertEqual(
                json.loads(jobRunCall.request.body),
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
            setupDefaultResponses(rsps)

            await run(MOCK_PORTAL_ITEM_ID, usePolling=True, culture="fr-CA")

            jobRunCall = next(
                x
                for x in rsps.calls
                if x.request.url == f"{DEFAULT_REPORTING_URL}/service/job/run"
            )
            self.assertEqual(
                json.loads(jobRunCall.request.body),
                {
                    "template": {
                        "itemId": MOCK_PORTAL_ITEM_ID,
                        "portalUrl": DEFAULT_PORTAL_URL,
                    },
                    "parameters": [],
                    "culture": "fr-CA",
                },
            )

    async def test_uses_reporting_service_url(self):
        with responses.RequestsMock() as rsps:
            reportingUrl = "https://on-prem/reporting"
            setupDefaultResponses(rsps, reportingUrl=reportingUrl)

            report = await run(MOCK_PORTAL_ITEM_ID, usePolling=True)

            self.assertEqual(
                report,
                f"{reportingUrl}/service/job/result?ticket={MOCK_REPORT_TICKET}&tag={MOCK_REPORT_TAG}",
            )

    async def test_uses_portal_url(self):
        with responses.RequestsMock() as rsps:
            portalUrl = "https://on-prem-portal"
            setupDefaultResponses(rsps, portalUrl=portalUrl)

            report = await run(
                MOCK_PORTAL_ITEM_ID, portalUrl=portalUrl, usePolling=True
            )

            self.assertEqual(
                report,
                f"{DEFAULT_REPORTING_URL}/service/job/result?ticket={MOCK_REPORT_TICKET}&tag={MOCK_REPORT_TAG}",
            )

    async def test_raises_when_portal_item_not_found(self):
        with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
            setupDefaultResponses(rsps)
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

            with self.assertRaises(Exception) as cm:
                await run(MOCK_PORTAL_ITEM_ID, usePolling=True)

            self.assertEqual(
                str(cm.exception),
                "Error retrieving portal item: Item does not exist or is inaccessible.",
            )

    async def test_raises_when_job_finishes_without_artifact(self):
        with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
            setupDefaultResponses(rsps)
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

            with self.assertRaises(Exception,) as cm:
                await run(MOCK_PORTAL_ITEM_ID, usePolling=True)

            self.assertEqual(
                str(cm.exception),
                f"Report job failed to produce an artifact. See the logs for more details: {DEFAULT_REPORTING_URL}/service/job/logs?ticket={MOCK_REPORT_TICKET}",
            )


class TestPrinting(unittest.IsolatedAsyncioTestCase):
    async def test_passes_dpi_as_job_arg(self):
        with responses.RequestsMock() as rsps:
            setupDefaultResponses(rsps)

            await run(MOCK_PORTAL_ITEM_ID, usePolling=True, dpi=42)

            jobRunCall = next(
                x
                for x in rsps.calls
                if x.request.url == f"{DEFAULT_REPORTING_URL}/service/job/run"
            )
            self.assertEqual(
                json.loads(jobRunCall.request.body),
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

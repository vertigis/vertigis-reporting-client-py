import requests
import unittest
import websockets

from unittest import mock

from geocortex.reporting.client import runReport

MOCK_PORTAL_ITEM_ID = "mock-item-id"
MOCK_PORTAL_TOKEN = "mock-portal-token"

MOCK_REPORTING_TOKEN = "mock-reporting-token"
MOCK_REPORT_TICKET = "mock-ticket"
MOCK_REPORT_TAG = "mock-tag"


class MockResponse:
    def __init__(self, url, json_data, status_code):
        self.url = url
        self.json_data = json_data
        self.status_code = status_code

    def raise_for_status(self):
        http_error_msg = ""
        if 400 <= self.status_code < 500:
            http_error_msg = f"{self.status_code} Client Error for url: {self.url}"
        elif 500 <= self.status_code < 600:
            http_error_msg = f"{self.status_code} Server Error for url: {self.url}"

        if http_error_msg:
            raise requests.exceptions.HTTPError(http_error_msg)

    def json(self):
        return self.json_data


def mocked_request(defaultResponses, args, kwargs):
    otherResponses = kwargs.get("responses", {})
    responses = {**defaultResponses, **otherResponses}

    url = args[0]

    matchingResponse = responses.get(url, None)
    if matchingResponse:
        return MockResponse(
            url, matchingResponse["json"], matchingResponse["status_code"]
        )

    return MockResponse(url, None, 404)


def get_mocked_requests_get(responses={}):
    def mocked_requests_get(*args, **kwargs):
        defaultResponses = {
            f"https://www.arcgis.com/sharing/rest/content/items/{MOCK_PORTAL_ITEM_ID}?f=json": {
                "json": {
                    "access": "public",
                    "url": "https://apps.geocortex.com/reporting/",
                },
                "status_code": 200,
            },
            f"https://apps.geocortex.com/reporting/service/job/artifacts?ticket={MOCK_REPORT_TICKET}": {
                "json": {
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
                "status_code": 200,
            },
        }

        return mocked_request({**defaultResponses, **responses}, args, kwargs)

    return mocked_requests_get


def get_mocked_requests_post(responses={}):
    def mocked_requests_post(*args, **kwargs):
        defaultResponses = {
            "https://apps.geocortex.com/reporting/service/job/run": {
                "json": {"response": {"$type": "TokenResponse", "ticket": MOCK_REPORT_TICKET}},
                "status_code": 200,
            },
        }

        return mocked_request({**defaultResponses, **responses}, args, kwargs)

    return mocked_requests_post


# def mocked_websockets_connect(*args, **kwargs):
#     class MockWebsocketConnect


class TestReporting(unittest.IsolatedAsyncioTestCase):
    @mock.patch("requests.get", side_effect=get_mocked_requests_get())
    @mock.patch("requests.post", side_effect=get_mocked_requests_post())
    async def test_basic(self, mock_post, mock_get):
        report = await runReport(MOCK_PORTAL_ITEM_ID, usePolling=True)

        self.assertEqual(
            report,
            f"https://apps.geocortex.com/reporting/service/job/result?ticket={MOCK_REPORT_TICKET}&tag={MOCK_REPORT_TAG}",
        )

    @mock.patch(
        "requests.get",
        side_effect=get_mocked_requests_get(
            {
                f"https://www.arcgis.com/sharing/rest/content/items/{MOCK_PORTAL_ITEM_ID}?f=json": {
                    "json": {
                        "access": "private",
                        "url": "https://apps.geocortex.com/reporting/",
                    },
                    "status_code": 200,
                }
            }
        ),
    )
    @mock.patch(
        "requests.post",
        side_effect=get_mocked_requests_post(
            {
                "https://apps.geocortex.com/reporting/service/auth/token/run": {
                    "json": {"response": {"token": MOCK_REPORTING_TOKEN}},
                    "status_code": 200,
                }
            }
        ),
    )
    async def test_with_token(self, mock_post, mock_get):
        report = await runReport(
            MOCK_PORTAL_ITEM_ID, usePolling=True, token=MOCK_PORTAL_TOKEN
        )

        self.assertEqual(
            report,
            f"https://apps.geocortex.com/reporting/service/job/result?ticket={MOCK_REPORT_TICKET}&tag={MOCK_REPORT_TAG}",
        )

        # Provided a reporting token to the job run endpoint.
        mock_post.assert_any_call(
            "https://apps.geocortex.com/reporting/service/job/run",
            headers={"Authorization": f"Bearer {MOCK_REPORTING_TOKEN}"},
            json={
                "template": {
                    "itemId": MOCK_PORTAL_ITEM_ID,
                    "portalUrl": "https://www.arcgis.com",
                },
                "parameters": [],
            },
        )


if __name__ == "__main__":
    unittest.main()

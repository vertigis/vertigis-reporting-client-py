import requests
import unittest
import websockets

from unittest import mock

from geocortex.reporting.client import runReport

MOCK_TICKET = "eyJhbGciOiJub25lIiwiemlwIjoiREVGIn0.q1ZKzs9TsqpWUimpLEhVslLyKi8JyUzOTi1xzs8rSc0rUdJRyspP8kwBSeUnFRvpp6YkmiYaGluYpFmmmpibGSZaJienGJqYGpiaGSeZp5gr1dYCAA."
MOCK_TAG = "e88aca6843c346acbd5999d9c017a587"


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


def mocked_requests_get(*args, **kwargs):
    defaultResponses = {
        "https://www.arcgis.com/sharing/rest/content/items/abc123?f=json": {
            "json": {
                "access": "public",
                "url": "https://apps.geocortex.com/reporting/",
            },
            "status_code": 200,
        },
        f"https://apps.geocortex.com/reporting/service/job/artifacts?ticket={MOCK_TICKET}": {
            "json": {
                "results": [
                    {
                        "$type": "JobResult",
                        "contentType": "application/pdf",
                        "tag": MOCK_TAG,
                        "length": 24003,
                    },
                    {"$type": "JobQuit", "kind": "Run"},
                ],
            },
            "status_code": 200,
        },
    }

    return mocked_request(defaultResponses, args, kwargs)


def mocked_requests_post(*args, **kwargs):
    defaultResponses = {
        "https://apps.geocortex.com/reporting/service/job/run": {
            "json": {"response": {"$type": "TokenResponse", "ticket": MOCK_TICKET}},
            "status_code": 200,
        },
    }

    return mocked_request(defaultResponses, args, kwargs)


# def mocked_websockets_connect(*args, **kwargs):
#     class MockWebsocketConnect


class TestReporting(unittest.IsolatedAsyncioTestCase):
    @mock.patch("requests.get", side_effect=mocked_requests_get)
    @mock.patch("requests.post", side_effect=mocked_requests_post)
    async def test_polling(self, mock_get, mock_post):
        report = await runReport("abc123", usePolling=True)
        self.assertEqual(
            report,
            f"https://apps.geocortex.com/reporting/service/job/result?ticket={MOCK_TICKET}&tag={MOCK_TAG}",
        )


if __name__ == "__main__":
    unittest.main()

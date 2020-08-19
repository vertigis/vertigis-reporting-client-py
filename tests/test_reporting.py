import requests
import unittest
import websockets

from unittest import mock

import geocortex.reporting


def mocked_requests_get(*args, **kwargs):
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

    responses = {
        "https://www.arcgis.com/sharing/rest/content/items/abc123?f=json": {
            "json": {
                "access": "public",
                "url": "https://apps.geocortex.com/reporting/",
            },
            "status_code": 200,
        }
    }

    otherResponses = kwargs.get("responses", {})
    responses.update(otherResponses)

    url = args[0]

    matchingResponse = responses.get(url, None)
    if matchingResponse:
        return MockResponse(
            url, matchingResponse["json"], matchingResponse["status_code"]
        )

    return MockResponse(url, None, 404)


# def mocked_websockets_connect(*args, **kwargs):
#     class MockWebsocketConnect


class TestReporting(unittest.IsolatedAsyncioTestCase):
    @mock.patch("requests.get", side_effect=mocked_requests_get)
    async def test_foo(self, mock_get):
        report = await geocortex.reporting.runReport("abc123", usePolling=True)
        # self.assertEqual(1, 2)


if __name__ == "__main__":
    unittest.main()

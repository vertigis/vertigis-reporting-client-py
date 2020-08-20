import json
import requests
import time
import typing
import websockets

from .portal_utils import getPortalItem


def _checkJobStatus(serviceUrl: str, ticket: str, jobStatus: dict) -> str:
    jobResults = jobStatus.get("results", None)

    # If there's a 'JobQuit' result we know the job is done
    if jobResults and any(x["$type"] == "JobQuit" for x in jobResults):
        jobResult = next(filter(lambda x: x["$type"] == "JobResult", jobResults), None)

        # The job finished but didn't produce any artifacts.
        if not jobResult:
            logsUrl = f"{serviceUrl}/job/logs?ticket={ticket}"
            raise Exception(
                f"Report job failed to produce an artifact. See the logs for more details: {logsUrl}"
            )

        tag = jobResult["tag"]
        # The job finished successfully.
        return f"{serviceUrl}/job/result?ticket={ticket}&tag={tag}"

    # Job not finished yet.
    return ""


def _getServiceUrlFromPortalItem(portalItem: dict) -> str:
    serviceUrl = portalItem.get("url", "")
    if not serviceUrl:
        # Fall back to the well-know SaaS URL.
        serviceUrl = "https://apps.geocortex.com/reporting"

    # TODO: Do we need to do the fragment stripping as GXWF activity does?

    return serviceUrl.strip("/") + "/service"


def _getReportingTokenIfNeeded(token: str, portalItem: dict, serviceUrl: str) -> str:
    if token and portalItem["access"] != "public":
        json = {"accessToken": token}
        response = requests.post(serviceUrl + "/auth/token/run", json=json)
        response.raise_for_status()
        responseJson = response.json()
        return responseJson["response"]["token"]

    return ""


def _buildJobArgs(itemId: str, portalUrl: str, args: dict) -> dict:
    parameters = []

    for key, value in args.items():
        param = {"name": key}

        if type(value) in [list, tuple]:
            param["containsMultipleValues"] = True
            param["values"] = value
        else:
            param["containsMultipleValues"] = False
            param["value"] = value

        parameters.append(param)

    return {
        "template": {"itemId": itemId, "portalUrl": portalUrl},
        "parameters": parameters,
    }


def _startJob(serviceUrl: str, jobArgs: dict, token: str) -> str:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.post(f"{serviceUrl}/job/run", headers=headers, json=jobArgs)
    response.raise_for_status()

    runResult = response.json()
    ticket = runResult["response"]["ticket"]
    return ticket


def _waitForJobResultHttp(serviceUrl: str, ticket: str) -> str:
    artifactUrl = ""

    while not artifactUrl:
        response = requests.get(f"{serviceUrl}/job/artifacts?ticket={ticket}")
        response.raise_for_status()
        jobStatus = response.json()
        artifactUrl = _checkJobStatus(serviceUrl, ticket, jobStatus)

        if not artifactUrl:
            time.sleep(1)

    return artifactUrl


async def _waitForJobResultWs(serviceUrl: str, ticket: str) -> str:
    # Note that a 'https' url will result in 'wss' after the string replace
    # which is what we want.
    wsServiceUrl = serviceUrl.replace("http", "ws")
    artifactsUrl = f"{wsServiceUrl}/job/artifacts?ticket={ticket}"

    async with websockets.connect(artifactsUrl, ssl=True) as websocket:
        message = await websocket.recv()
        jobStatus = json.loads(message)
        artifactUrl = _checkJobStatus(serviceUrl, ticket, jobStatus)
        if artifactUrl:
            return artifactUrl


async def runReport(
    itemId: str,
    portalUrl="https://www.arcgis.com",
    token="",
    usePolling=False,
    **kwargs,
):
    portalUrl = portalUrl.strip("/")
    portalItem = getPortalItem(itemId, portalUrl)
    serviceUrl = _getServiceUrlFromPortalItem(portalItem)

    reportingToken = _getReportingTokenIfNeeded(token, portalItem, serviceUrl)
    jobArgs = _buildJobArgs(itemId, portalUrl, kwargs)
    ticket = _startJob(serviceUrl, jobArgs, reportingToken)

    if usePolling == True:
        return _waitForJobResultHttp(serviceUrl, ticket)
    else:
        return await _waitForJobResultWs(serviceUrl, ticket)

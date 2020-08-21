import json
import time
import requests
import websockets

from .portal_utils import get_portal_item


def _check_job_status(service_url: str, ticket: str, job_status: dict) -> str:
    job_results = job_status.get("results", None)

    # If there's a 'JobQuit' result we know the job is done
    if job_results and any(x["$type"] == "JobQuit" for x in job_results):
        job_result = next(
            filter(lambda x: x["$type"] == "JobResult", job_results), None
        )

        # The job finished but didn't produce any artifacts.
        if not job_result:
            logs_url = f"{service_url}/job/logs?ticket={ticket}"
            raise Exception(
                f"Report job failed to produce an artifact. See the logs for more details: {logs_url}" # pylint: disable=line-too-long
            )

        tag = job_result["tag"]
        # The job finished successfully.
        return f"{service_url}/job/result?ticket={ticket}&tag={tag}"

    # Job not finished yet.
    return ""


def _get_service_url_from_portal_item(portal_item: dict) -> str:
    service_url = portal_item.get("url", "")
    if not service_url:
        # Fall back to the well-know SaaS URL.
        service_url = "https://apps.geocortex.com/reporting"

    # TODO: Do we need to do the fragment stripping as GXWF activity does?

    return service_url.strip("/") + "/service"


def _get_reporting_token_if_needed(
    token: str, portal_item: dict, service_url: str
) -> str:
    if token and portal_item["access"] != "public":
        token_args = {"accessToken": token}
        response = requests.post(service_url + "/auth/token/run", json=token_args)
        response.raise_for_status()
        response_json = response.json()
        return response_json["response"]["token"]

    return ""


def _build_job_args(
    item_id: str, portal_url: str, args: dict, culture: str, dpi: int
) -> dict:
    job_args = {
        "template": {"itemId": item_id, "portalUrl": portal_url},
        "parameters": [],
    }

    for key, value in args.items():
        param = {"name": key}

        if type(value) in [list, tuple]:
            param["containsMultipleValues"] = True
            param["values"] = value
        else:
            param["containsMultipleValues"] = False
            param["value"] = value

        job_args["parameters"].append(param)

    if culture:
        job_args["culture"] = culture
    if dpi:
        job_args["dpi"] = dpi

    return job_args


def _start_job(service_url: str, job_args: dict, token: str) -> str:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.post(f"{service_url}/job/run", headers=headers, json=job_args)
    response.raise_for_status()

    run_result = response.json()
    ticket = run_result["response"]["ticket"]
    return ticket


def _wait_for_job_result_http(service_url: str, ticket: str) -> str:
    artifact_url = ""

    while not artifact_url:
        response = requests.get(f"{service_url}/job/artifacts?ticket={ticket}")
        response.raise_for_status()
        job_status = response.json()
        artifact_url = _check_job_status(service_url, ticket, job_status)

        # TODO: Do we want to bail after retrying a certain number of times?
        if not artifact_url:
            time.sleep(1)

    return artifact_url


async def _wait_for_job_result_ws(service_url: str, ticket: str) -> str:
    # Note that a 'https' url will result in 'wss' after the string replace
    # which is what we want.
    ws_service_url = service_url.replace("http", "ws")
    artifacts_service_url = f"{ws_service_url}/job/artifacts?ticket={ticket}"

    async with websockets.connect(artifacts_service_url, ssl=True) as websocket:
        message = await websocket.recv()
        job_status = json.loads(message)
        artifact_url = _check_job_status(service_url, ticket, job_status)
        if artifact_url:
            return artifact_url


async def run(
    item_id: str,
    *,
    portal_url="https://www.arcgis.com",
    token="",
    culture="",
    dpi=0,
    use_polling=False,
    **kwargs,
):
    """Runs a report job and returns a URL to the report artifact.

    Args:
        item_id (str): The portal item ID of the Reporting or Printing item.
        portal_url (str, optional) The URL of the ArcGIS Portal instance to use.
            Defaults to `https://www.arcgis.com`.
        token (str, optional) The Portal access token to be used to access secured resources.
            If not provided requests to secured resources will fail.
        culture (str, optional) The culture to use for localization.
        dpi (str) The DPI to use when rendering a map print. Defaults to `96`.
        use_polling (bool) When `True`, the job service will be polled periodically for results.
            When `False`, connect to the job service using WebSockets to listen for results.
            It's recommended to use WebSockets if possible.
            Defaults to `False`.
        **kwargs: Other parameters to pass to the job.
            These are commonly used to parameterize your template.

    Returns:
        A URL to the report artifact.
    """

    portal_url = portal_url.strip("/")
    portal_item = get_portal_item(item_id, portal_url)
    service_url = _get_service_url_from_portal_item(portal_item)

    reporting_token = _get_reporting_token_if_needed(token, portal_item, service_url)
    job_args = _build_job_args(item_id, portal_url, kwargs, culture, dpi)
    ticket = _start_job(service_url, job_args, reporting_token)

    if use_polling:
        return _wait_for_job_result_http(service_url, ticket)

    return await _wait_for_job_result_ws(service_url, ticket)

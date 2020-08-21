import requests


def _get_portal_rest_url(portal_url: str) -> str:
    return f"{portal_url}/sharing/rest"


def _get_portal_item_url(item_id: str, portal_url: str) -> str:
    return f"{_get_portal_rest_url(portal_url)}/content/items/{item_id}"


def get_portal_item(item_id: str, portal_url: str):
    """Retrieve a portal item by id."""

    item_url = _get_portal_item_url(item_id, portal_url)
    response = requests.get(f"{item_url}?f=json")
    response.raise_for_status()
    portal_item = response.json()

    if "error" in portal_item:
        message = portal_item["error"]["message"]
        raise Exception(f"Error retrieving portal item: {message}")

    return portal_item


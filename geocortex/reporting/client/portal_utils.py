import requests


def _getPortalRestUrl(portalUrl: str) -> str:
    return f"{portalUrl}/sharing/rest"


def _getPortalItemUrl(itemId: str, portalUrl: str) -> str:
    return f"{_getPortalRestUrl(portalUrl)}/content/items/{itemId}"


def getPortalItem(itemId: str, portalUrl: str):
    itemUrl = _getPortalItemUrl(itemId, portalUrl)
    response = requests.get(f"{itemUrl}?f=json")
    response.raise_for_status()
    portalItem = response.json()

    if "error" in portalItem:
        message = portalItem["error"]["message"]
        raise Exception(f"Error retrieving portal item: {message}")

    return portalItem


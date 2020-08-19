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

    if hasattr(portalItem, "error"):
        raise Exception(portalItem["error"])

    return portalItem


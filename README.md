# Geocortex Reporting Client for Python

![CI/CD](https://github.com/geocortex/geocortex-reporting-client-py/workflows/CI/CD/badge.svg)

This Python library makes it easy to run [Geocortex Reporting](https://www.geocortex.com/products/geocortex-reporting/) or [Geocortex Printing](https://www.geocortex.com/products/geocortex-printing/) jobs.

## Requirements

- Python 3.6 or later

## Installing the package

```bash
pip install geocortex-reporting-client
```

## Generating a report

The client exports a `run` async function that will return a url to the report upon completion.

```py
from geocortex.reporting.client import run

url = await run("itemid", [... other arguments])
```

### Arguments

`item_id` is required. All other arguments are optional.

| Argument       | Type | Description                                                                                                                                                                                                                    |
| -------------- | ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| item_id        | str  | The portal item ID of the Reporting or Printing item.                                                                                                                                                                          |
| portal_url     | str  | The URL of the ArcGIS Portal instance to use. Defaults to ArcGIS Online: `"https://www.arcgis.com"`                                                                                                                            |
| token          | str  | The Portal access token to be used to access secured resources. If not provided requests to secured resources will fail.                                                                                                       |
| culture        | str  | The culture to use for localization. For example `"en-US"`.                                                                                                                                                                    |
| dpi            | int  | The DPI to use when rendering a map print. Defaults to `96`.                                                                                                                                                                   |
| use_polling    | bool | When `True`, the job service will be polled periodically for results. When `False`, connect to the job service using WebSockets to listen for results. It's recommended to use WebSockets where possible. Defaults to `False`. |
| \*\*kwargs\*\* | any  | Other parameters to pass to the job. These are commonly used to parameterize your template. For example `run("itemid", FeatureIds=[1, 2, 3])`                                                                              |

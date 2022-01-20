# VertiGIS Studio Reporting Client for Python

![CI](https://github.com/geocortex/vertigis-reporting-client-py/workflows/CI/badge.svg) ![PyPI](https://img.shields.io/pypi/v/geocortex-reporting-client)

This Python library makes it easy to run [VertiGIS Studio Reporting](https://www.vertigisstudio.com/products/geocortex-reporting/) or [VertiGIS Studio Printing](https://www.vertigisstudio.com/products/geocortex-printing/) jobs.

## Requirements

- Python 3.6.1 or later

## Installing the package

This package is published to [PyPi](https://pypi.org/project/geocortex-reporting-client/), and can be installed using `pip`:

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
| result_file_name    | str  | The name assigned to the output file. It is used as the suggested name when downloading the result.  |
| dpi            | int  | The DPI to use when rendering a map print. Defaults to `96`.                                                                                                                                                                   |
| use_polling    | bool | When `True`, the job service will be polled periodically for results. When `False`, connect to the job service using WebSockets to listen for results. It's recommended to use WebSockets where possible. Defaults to `False`. |
| \*\*kwargs\*\* | any  | Other parameters to pass to the job. These are commonly used to parameterize your template. For example `run("itemid", FeatureIds=[1, 2, 3])`                                                                                  |

## Documentation

Find [further documentation on the SDK](https://developers.geocortex.com/docs/reporting/sdk-overview/) on the [VertiGIS Studio Developer Center](https://developers.geocortex.com/docs/reporting/overview/)

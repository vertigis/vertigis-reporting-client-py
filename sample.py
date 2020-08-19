import asyncio
import geocortex.reporting


async def f():
    reportUrl = await geocortex.reporting.runReport(
        "eabbd585f8d44c09acb2986b1293f2f8", FeatureIds=[3903]
    )
    print(reportUrl)


loop = asyncio.get_event_loop()
loop.run_until_complete(f())
loop.close()

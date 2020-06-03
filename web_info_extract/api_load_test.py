"""
Test the api gateway by having simultaneous api calls
"""
import sys
import asyncio
import requests

sample_response = {
    "title": "Six Rapporteurs address Human Rights Commission under debate on civil and political rights",
    "date": "2003-04-08",
    "country": "Afghanistan",
    "source": "redhum",
    "website": "redhum.org",
    "author": "United Nations Commission on Human Rights",
}

WEB_EXTRACT_ENDPOINT = 'https://services.thedeep.io/web-info-extract/?url=https://reddit.com'


async def main(n=1):
    loop = asyncio.get_event_loop()
    futures = [
        loop.run_in_executor(None, requests.get, WEB_EXTRACT_ENDPOINT)
        for _ in range(n)
    ]
    for i, response in enumerate(await asyncio.gather(*futures)):
        print("response", i+1,  response.text)


if __name__ == '__main__':
    args = sys.argv
    if len(args) > 1:
        num_requests = int(args[1])
    else:
        num_requests = 1

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(num_requests))

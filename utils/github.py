import asyncio
import itertools
import re
import urllib.parse
from datetime import datetime

import aiohttp
import requests
from django.conf import settings


class APIException(Exception):

    def __init__(self, response, *args, **kwargs):
        self.response = response
        super().__init__(*args, **kwargs)


class Client:
    base_url = 'https://api.github.com'

    def __init__(self, access_token=settings.GITHUB_ACCESS_TOKEN):
        if not access_token:
            raise APIException("Incorrect token")

        self.access_token = access_token

    def _request(self, url, **params):
        response = requests.get(
            self.base_url + url,
            params=params,
            headers=self.headers
        )
        if response.status_code == 200:
            return response
        raise APIException(response=response)

    async def _async_request(self, session, url):
        response = await session.get(url)
        if response.status == 200:
            return await response.json()
        raise APIException(response=response)

    async def _get_other_pages(self, urls):
        async with aiohttp.ClientSession(headers=self.headers) as session:
            return await asyncio.gather(*[self._async_request(session, url) for url in urls])

    def get_commits(self, owner, repository, *, author=None, since=None, until=None):
        if since and isinstance(since, datetime):
            since = since.isoformat()
        if until and isinstance(until, datetime):
            until = until.isoformat()

        response = self._request(f'/repos/{owner}/{repository}/commits', author=author, since=since, until=until,
                                 per_page=100)
        data: list = response.json()

        pages = response.headers.get('Link')
        if pages:
            last = pages.split(',')[-1]
            url = re.search('<(?P<url>[^>]*)', last).groupdict()['url']
            parsed_url = urllib.parse.urlparse(url)
            pages_number = int(urllib.parse.parse_qs(parsed_url.query)['page'][0])
            next_page_urls = [
                url.replace(f'page={pages_number}', f'page={i}') for i in range(2, pages_number + 1)
            ]

            next_pages_data = asyncio.run(self._get_other_pages(next_page_urls))
            data.extend(itertools.chain(*next_pages_data))

        return data

    @property
    def headers(self):
        return {'Authorization': f'token {self.access_token}'}

import asyncio
import datetime
import os

from extracts import PublicUrl
from extracts.converters import excel_to_csv

_today = datetime.datetime.today()
formatstr = '%Y-%m-%d'
datestamp = _today.strftime( formatstr )

output_dir = os.path.expanduser( '~/extract_dump' )


def seven_hundred_report():

    name = '0700_report'
    url = f'https://report.boonecountymo.org/mrcjava/servlet/SH01_MP.R00070s?run=1&outfmt=13&D_DETAIL=1&R001={datestamp}&R001={datestamp}'

    headers = {

        'Host': 'report.boonecountymo.org',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:68.0) Gecko/20100101 Firefox/68.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://report.boonecountymo.org/mrcjava/servlet/SH01_MP.I00080s',

        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    return PublicUrl( name, url, output_dir,
                      headers=headers,
                      output_converter=excel_to_csv,
    )

def current_detainees():

    name = 'current_detainees'
    url = 'https://report.boonecountymo.org/mrcjava/servlet/SH01_MP.R00250s?run=2'

    headers = {
        'Host': 'report.boonecountymo.org',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:68.0) Gecko/20100101 Firefox/68.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://report.boonecountymo.org/mrcjava/servlet/SH01_MP.I00290s',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    return PublicUrl( name, url, output_dir,
                      headers=headers,
                      output_converter=excel_to_csv,
    )


fetches = [

    seven_hundred_report(),
    current_detainees(),
]

async def _run_all():
    await asyncio.gather( *( p.fetch() for p in fetches ) )

loop = asyncio.get_event_loop()
loop.run_until_complete( _run_all() )


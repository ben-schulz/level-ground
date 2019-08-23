import sys
import os
import pathlib
import datetime
import asyncio
import requests
import csv
import xlrd


def datestamp_filename_today( name, suffix=None ):
    _today = datetime.datetime.today()
    formatstr = '%Y-%m-%d'
    stamp = _today.strftime( formatstr )

    if suffix is not None:
        return f'{name}_{stamp}.{suffix}'
    else:
        return f'{name}_{stamp}'


def exp_backoff( initial_seconds=4,
                 backoff_factor=1.1,
                 max_wait_seconds=sys.maxsize
):

    next_delay = initial_seconds
    while True:
        yield min( next_delay, max_wait_seconds )
        next_delay = int( ( next_delay * backoff_factor ) + 1 )


def excel_to_csv( source_path, dest_path ):

    workbook = xlrd.open_workbook( source_path )

    sheets = workbook.sheets()

    def _sheet_to_csv( sheet, out_path ):
        with open( out_path, 'w' ) as f:
            output_writer = csv.writer( f, quoting=csv.QUOTE_ALL )
            for row in sheet.get_rows():
                output_writer.writerow( row )

    if 1 == len( sheets ):
        _sheet_to_csv( sheets[ 0 ], dest_path )

    else:        
        for number, sheet in enumerate( sheets ):
            _sheet_to_csv( sheet, f'{dest_path}.{number}'  )
    

class PublicUrl:

    allowed_verbs = ( 'GET', 'POST' )

    def is_allowed_verb( v ):

        return ( isinstance( v, str )
                 and v.upper() in ( 'GET', 'POST' ) )


    def __init__( self, name, url, output_dir,
                  http_verb='GET',
                  headers=None,
                  request_body=None,
                  retry_horizon=None,
                  output_converter=None,
    ):

        if not PublicUrl.is_allowed_verb( http_verb ):
            error_text = ( '\'http_verb\' must be one of: '
                           f'{PublicUrl.allowed_verbs}' )
            raise ValueError( error_text )

        self.output_dir = pathlib.Path( output_dir )
        if not self.output_dir.exists():
            os.mkdir( self.output_dir )

        self.name = name
        self.url = url
        self.output_dir = output_dir
        self.verb = http_verb.upper()
        self.headers = headers or dict()

        self.convert_output = output_converter
        self.converted_suffix = 'csv'

        twelve_hours = datetime.timedelta( hours=12 ).total_seconds()
        self.retry_horizon = ( retry_horizon or twelve_hours )


    def write_result( self, response ):

        outfile_basename = datestamp_filename_today( self.name )
        out_path = os.path.join( self.output_dir, outfile_basename )

        with open( out_path, 'wb' ) as f:
            f.write( response )

        if self.convert_output is not None:
            converted_out_path = f'{out_path}.{self.converted_suffix}'
            self.convert_output( out_path, converted_out_path )


    async def fetch( self ):

        done = False

        delay = exp_backoff()

        while not done:

            if 'GET' == self.verb:
                rsp = requests.get( self.url, headers=self.headers )

            elif 'POST' == self.verb:
                rsp = requests.post( self.url, headers=self.headers )

            if rsp.ok:
                done = True

            else:
                retry_delay = next( delay )
                if retry_delay > self.retry_horizon:
                    done = True
                else:
                    await asyncio.sleep( retry_delay )

        self.write_result( rsp.content )


if '__main__' == __name__:

    _today = datetime.datetime.today()
    formatstr = '%Y-%m-%d'
    datestamp = _today.strftime( formatstr )

    name = '0700_report'
    url=f'https://report.boonecountymo.org/mrcjava/servlet/SH01_MP.R00070s?run=1&outfmt=13&D_DETAIL=1&R001={datestamp}&R001={datestamp}'

    output_dir = os.path.join( os.path.dirname( __file__), 'okwow' )

    headers = {
 
        'Host': 'report.boonecountymo.org',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:68.0) Gecko/20100101 Firefox/68.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://report.boonecountymo.org/mrcjava/servlet/SH01_MP.I00080s',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Cookie': 'SH01_MPI00070maxrows=120; JSESSIONID=0BA219728D60754CB329B3C0EB563AC7; nmstat=1565577962084',
        'Upgrade-Insecure-Requests': '1',
    }

    p = PublicUrl( name, url, output_dir,
                   headers=headers,
                   output_converter=excel_to_csv,
    )

    async def _run_all():
        await asyncio.gather( p.fetch() )

    asyncio.run( _run_all() )

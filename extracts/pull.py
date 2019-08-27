import sys
import os
import pathlib
import datetime
import asyncio
import requests

from extracts.converters import excel_to_csv


def _today():
    _day = datetime.datetime.today()
    formatstr = '%Y-%m-%d'
    return _day.strftime( formatstr )
    

def datestamp_filename_today( name, suffix=None ):

    stamp = _today()
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
                  datestamp=None,
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

        self.datestamp = datestamp or _today()

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

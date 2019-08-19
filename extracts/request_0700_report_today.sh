#!/bin/bash

# pull the "0700 Report"
# for Boone County Jail,
# from County Sheriff publis site,
# and convert to date-stamped csv.
#
# (2019.08.19) \0

datestamp=$(date +%Y-%m-%d)

url="https://report.boonecountymo.org/mrcjava/servlet/SH01_MP.R00070s?run=1&outfmt=13&D_DETAIL=1&R001=$datestamp&R001=$datestamp"

wget_out_path="0700_report_$datestamp.xml"
result_path="0700_report_$datestamp.csv"

headers="'Host:report.boonecountymo.org'
'Accept:text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
'Accept-Language:en-US,en;q=0.5'
'Accept-Encoding:gzip,deflate,br'
'Referer:https://report.boonecountymo.org/mrcjava/servlet/SH01_MP.I00080s'
'DNT:1'
'Connection:keep-alive'
'Cookie:SH01_MPI00070maxrows=120;JSESSIONID=E702A96537C47DB799A4DF3F02A11A66;nmstat=1565577962084'
'Upgrade-Insecure-Requests:1'
"

opts=''
for h in $headers; do
    header_flag="--header=$h"
    opts="$opts $header_flag"
done

opts="$opts --output-document=$wget_out_path"

wget $opts $url

ssconvert --export-type=Gnumeric_stf:stf_csv $wget_out_path $result_path

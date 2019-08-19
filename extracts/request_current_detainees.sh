#!/bin/bash

# pull "Current Detainees of Boone County Jail"
# from Boone County Sheriff public site
# and convert to date-stamped csv.
#
# (2019.08.18) \0

datestamp=$(date +%Y-%m-%d)

url='https://report.boonecountymo.org/mrcjava/servlet/SH01_MP.R00250s?run=2'
wget_out_path="current_detainees_$datestamp.xml"
result_path="current_detainees_$datestamp.csv"

headers="'Host:report.boonecountymo.org'
'Accept:text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
'Accept-Language:en-US,en;q=0.5'
'Accept-Encoding:gzip,deflate,br'
'Referer:https://report.boonecountymo.org/mrcjava/servlet/SH01_MP.I00290s'
'DNT:1'
'Connection:keep-alive'
'Cookie:SH01_MPI00070maxrows=120;JSESSIONID=C38F68AD57DB065697BCFE1F620FFF5E;nmstat=1565577962084'
'Upgrade-Insecure-Requests:1'"

opts=''
for h in $headers; do
    header_flag="--header=$h"
    opts="$opts $header_flag"
done

opts="$opts --output-document=$wget_out_path"

wget $opts $url

ssconvert --export-type=Gnumeric_stf:stf_csv $wget_out_path $result_path

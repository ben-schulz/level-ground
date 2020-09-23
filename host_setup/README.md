# steps

## host
this currently runs as an RHEL instance on AWS

## system packages
- copy the text of the script at `./jail_extract_server.sh` to the server, e.g. as `~/setup.sh`
- run: `chmod +x setup.py`
- run: `sudo ~/setup.sh`

## initializing the extract
- clone this repo
- create the python environment with `python -m venv env`
- update pip: `pip install --upgrade pip`
- install the requirements: `pip install -r requirements.txt`
- set a path for the extract output as the value of `EXTRACT_DUMP`
- verify that the extract script runs and writes output `EXTRACT_DUMP`
- set up the crontab
  - the executable should be an absolute path to the python in the virtual environment
  - specify the value of `EXTRACT_DUMP` at the top of the crontab
  - be sure to give the times in UTC (the system default) _or_ set the appropriate local time

## keeping in sync
- do `ssh-keygen` to produce a ssh keypair
- add the public key to the repo permissions, so that any tweaks on the server can persist upstream

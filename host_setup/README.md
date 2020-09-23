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
- set a path for the extract output as the value of `EXTRACT_DUMP`
- verify that the extract script runs and writes output `EXTRACT_DUMP`
- set up the crontab
  - the executable should be an absolute path to the python in the virtual environment
  - specify the value of `EXTRACT_DUMP` at the top of the crontab

## keeping in sync
- do `ssh-keygen` to produce a ssh keypair
- add the public key to the repo permissions, so that any tweaks on the server can persist upstream

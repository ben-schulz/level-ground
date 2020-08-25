# level-ground

## build

using the usual python idioms:

```
python -m venv env
. env/bin/activate
pip install -r requirements.txt
```

## run

```
. env/bin/activate
python run_jail_extracts.py
```

this will hit the target reports on the public-facing site.

on unsuccessful HTTP status, the request will retry (with an exponential back-off).

on success, the resulting files save to `~/extract_dump` on the local machine (yes, i know this is bad practice; the days are just so short though).

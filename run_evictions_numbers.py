import time
import datetime
import json
import csv

from api.mocasenet import case_numbers_by_date, case_by_number

#
# phase 0: fetch case numbers for all cases categorized as evictions
#

start_date = datetime.datetime(2022, 1, 6)
end_date = datetime.datetime.now()

case_numbers_outfile = "case_numbers.json"
case_numbers_by_date(start_date, end_date, outfile=case_numbers_outfile)

#
# phase 1: use those case numbers to query individual records
#

with open(case_numbers_outfile, "r") as f:
    case_numbers = json.load(f)

max_attempts = 10

record_count = 0
record_total = len(case_numbers)

start_time = datetime.datetime.now()

case_info_outfile = "case_info.json"
with open(case_info_outfile, "w") as f:
    f.write("[")

success_delay = 0.5
fail_delay_seconds = 10.0

fetches = list()

for case_number in case_numbers:

    # this may seem like a strangely arbitrary wait criterion,
    # but extensive trial and error currently suggests
    # that this is exactly the threshold at which Case.net
    # throws an HTTP 429.
    # in current practice, this criterion
    # seem to approach an optimal fetch-to-wait ratio.
    #
    # (2022.01.07) \0
    if 0 == (record_count % 4):
        time.sleep(30.0)

    attempts = 0

    fail_delay = fail_delay_seconds
    while attempts < max_attempts:
        attempts += 1
        now = datetime.datetime.now()
        try:
            record = case_by_number(case_number)

            with open(case_info_outfile, "a") as f:
                if record_count > 0:
                    f.write(",")
                f.write(json.dumps(record))

            record_count += 1

            elapsed_minutes = (now - start_time).total_seconds() / 60
            elapsed_hours = int(elapsed_minutes / 60)
            rem_minutes = int(elapsed_minutes - (elapsed_hours * 60))

            print(
                f"retrieved record {record_count} of {record_total}\t{format(elapsed_hours, '02')}:{format(rem_minutes, '02')} elapsed"
            )

            time.sleep(success_delay)

            fetches.append((now.timestamp(), True))

            break
        except Exception as e:
            fetches.append((now.timestamp(), False))

            print(f"{type(e)}: {e}")
            print(f"retrying {case_number}...")

            time.sleep(fail_delay)
            fail_delay *= 1.2

            if attempts == max_attempts:
                error_message = f"unrecoverable failure at index {record_count}, case number {case_number}"
                print("")
                print(error_message)
                print("")

                with open(case_info_outfile, "a") as f:
                    f.write("//")
                    f.write(error_message)

with open(case_info_outfile, "a") as f:
    f.write("]")

print(f"wrote {record_count} case records to '{case_info_outfile}'.")

with open("fetch_timeseries.json", "w") as f:
    f.write(json.dumps(fetches))

print(f"wrote fetch time series to 'fetch_timeseries.json'")



#
# phase 2: write the JSON to a CSV format
#
with open(case_info_outfile, "r") as f:
    records = json.load(f)


fields = set()
for record in records:
    fields = fields.union(record.keys())

csv_outfile = "case_info.csv"
with open(csv_outfile, "w+") as f:
    writer = csv.DictWriter(f, fieldnames=list(fields))

    writer.writeheader()
    for record in records:
        writer.writerow(record)

print(f"wrote CSV to {csv_outfile}")

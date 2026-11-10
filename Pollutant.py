
# ============================================================
# CPCB INDIA - ALL STATIONS RAW POLLUTANT DOWNLOADER
# VAYUAYAN 0.3.0
# ============================================================
#
# Downloads raw CPCB pollutant observations.
#
# YEAR DISCOVERY:
#   Queries each year individually (blank year does not work).
#
# DEFAULT FREQUENCY:
#   15-minute measurements
#
# FEATURES:
#   - All discovered stations
#   - Individual station/year CSV files
#   - Automatic year checking
#   - Resume after interruption
#   - Retry failed requests
#   - Stop safely if CPCB becomes unavailable
#   - Incremental download log
#
# ============================================================

import os
import re
import csv
import time
import logging

from pathlib import Path
from datetime import datetime

import pandas as pd
from vayuayan import CPCBHistorical


# ============================================================
# SETTINGS
# ============================================================

OUTPUT_ROOT = Path(
    r"C:\Users\Bibin\Downloads\CPCB_India_Raw_Pollutant_Data"
)

DATA_FOLDER = OUTPUT_ROOT / "Station_Year_Files"
LOG_FOLDER = OUTPUT_ROOT / "Logs"

STATION_FILE = OUTPUT_ROOT / "all_india_stations.csv"

DOWNLOAD_LOG = LOG_FOLDER / "download_log.csv"
PROCESS_LOG = LOG_FOLDER / "process.log"

# Historical year range
START_YEAR = 2015
END_YEAR = datetime.now().year

# Available raw frequencies:
#
# "15_minute": "15M"  = 15-minute data
# "hourly":    "1H"   = Hourly data
# "daily":     "1D"   = Daily data
#
# Default: 15-minute data only.
#
# To download all three, use:
# FREQUENCIES = {
#     "15_minute": "15M",
#     "hourly": "1H",
#     "daily": "1D"
# }

FREQUENCIES = {
    "daily": "1D"
}

MAX_RETRIES = 3
RETRY_DELAY = 10
REQUEST_DELAY = 0.3


# ============================================================
# CREATE FOLDERS
# ============================================================

OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
DATA_FOLDER.mkdir(parents=True, exist_ok=True)
LOG_FOLDER.mkdir(parents=True, exist_ok=True)


# ============================================================
# PROCESS LOG
# ============================================================

logging.basicConfig(
    filename=str(PROCESS_LOG),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8"
)


# ============================================================
# INITIALIZE CLIENT
# ============================================================

client = CPCBHistorical()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_name(value):

    value = str(value or "Unknown")

    value = re.sub(
        r'[<>:"/\\|?*]',
        "_",
        value
    )

    value = re.sub(
        r"\s+",
        "_",
        value.strip()
    )

    return value[:120]


def log_result(
    station,
    year,
    frequency,
    status,
    attempts=0,
    file_path="",
    message=""
):

    row = {
        "Station_ID": station["station_id"],
        "Station_Name": station["station_name"],
        "State": station["state"],
        "City": station["city"],
        "Year": year,
        "Frequency": frequency,
        "Status": status,
        "Attempts": attempts,
        "File_Path": str(file_path),
        "Message": str(message),
        "Timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }

    file_exists = DOWNLOAD_LOG.exists()

    with open(
        DOWNLOAD_LOG,
        "a",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=list(row.keys())
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


def is_valid_file(path):

    try:

        if not path.exists():
            return False

        if path.stat().st_size < 10:
            return False

        df = pd.read_csv(
            path,
            nrows=5
        )

        return (
            not df.empty
            and len(df.columns) >= 2
        )

    except Exception:
        return False


# ============================================================
# DISCOVER ALL STATIONS
# ============================================================

print("\nDISCOVERING ALL CPCB STATIONS...")
print("=" * 70)

stations_dict = {}

for state_entry, city_entry, station_entry in client.iter_stations():

    station_id = str(
        station_entry.get("station_id", "")
    ).strip()

    if not station_id:
        continue

    stations_dict[station_id] = {

        "station_id": station_id,

        "station_name": str(
            station_entry.get("station_name", "")
        ),

        "state": str(
            state_entry.get("state_name", "")
        ),

        "city": str(
            city_entry.get("city_name", "")
        )
    }


# Supplement with RSS stations

try:

    for state_entry, city_entry, station_entry in client._rss_directory():

        station_id = str(
            station_entry.get("station_id", "")
        ).strip()

        if not station_id:
            continue

        if station_id not in stations_dict:

            stations_dict[station_id] = {

                "station_id": station_id,

                "station_name": str(
                    station_entry.get("station_name", "")
                ),

                "state": str(
                    state_entry.get("state_name", "")
                ),

                "city": str(
                    city_entry.get("city_name", "")
                )
            }

except Exception as e:

    logging.warning(
        f"RSS station discovery failed: {e}"
    )


stations = list(stations_dict.values())

if not stations:

    raise RuntimeError(
        "No CPCB stations discovered."
    )


pd.DataFrame(stations).to_csv(
    STATION_FILE,
    index=False
)

print("Stations discovered:", len(stations))
print("Years:", START_YEAR, "-", END_YEAR)
print("Frequencies:", FREQUENCIES)
print("Station list:", STATION_FILE)


# ============================================================
# DOWNLOAD COUNTERS
# ============================================================

total_checks = 0
successful = 0
skipped = 0
no_data = 0
failed = 0


# ============================================================
# MAIN DOWNLOAD PROCESS
# ============================================================

for station_number, station in enumerate(stations, start=1):

    print("\n" + "=" * 75)

    print(
        f"STATION {station_number}/{len(stations)}"
    )

    print("Station:", station["station_name"])
    print("ID:", station["station_id"])
    print("City:", station["city"])
    print("State:", station["state"])

    print("=" * 75)

    station_id = station["station_id"]


    # --------------------------------------------------------
    # OUTPUT DIRECTORY
    # --------------------------------------------------------

    station_folder = (
        DATA_FOLDER
        / safe_name(station["state"])
        / safe_name(station["city"])
        / (
            safe_name(station["station_name"])
            + "_"
            + safe_name(station_id)
        )
    )

    station_folder.mkdir(
        parents=True,
        exist_ok=True
    )


    # --------------------------------------------------------
    # CHECK EACH FREQUENCY
    # --------------------------------------------------------

    for frequency_name, frequency_code in FREQUENCIES.items():

        print("\nFREQUENCY:", frequency_name)

        for year in range(START_YEAR, END_YEAR + 1):

            year = str(year)

            total_checks += 1

            output_file = (
                station_folder
                / f"{safe_name(station_id)}_{year}_{frequency_name}.csv"
            )

            temp_file = output_file.with_suffix(".tmp.csv")


            # ------------------------------------------------
            # RESUME: SKIP EXISTING VALID FILE
            # ------------------------------------------------

            if is_valid_file(output_file):

                print(
                    f"SKIP {year}: Already downloaded"
                )

                skipped += 1

                continue


            # ------------------------------------------------
            # EXPLICIT YEAR API REQUEST
            # ------------------------------------------------

            payload = {

                "station_id": station_id,

                "station_name": station["station_name"],

                "state": station["state"],

                "city": station["city"],

                "year": year,

                "frequency": frequency_code,

                "dataType": "raw"
            }


            entries = None
            last_error = ""
            attempts = 0


            # ------------------------------------------------
            # RETRY API REQUEST
            # ------------------------------------------------

            for attempt in range(1, MAX_RETRIES + 1):

                attempts = attempt

                try:

                    result = client._new_api_json(
                        "post",
                        client.new_file_path_endpoint,
                        json_data=payload
                    )

                    if not isinstance(result, dict):

                        raise RuntimeError(
                            "Unexpected CPCB API response"
                        )

                    if result.get("status") == "success":

                        entries = result.get("data", [])

                        break

                    elif result.get("status") == "failed":

                        # Explicit year query returned no files.
                        # This is treated as no data, not a network failure.

                        entries = []

                        break

                    else:

                        raise RuntimeError(
                            f"Unexpected response: {result}"
                        )


                except Exception as e:

                    last_error = str(e)

                    print(
                        f"  API attempt {attempt}/{MAX_RETRIES} "
                        f"failed: {last_error}"
                    )

                    logging.exception(
                        f"API error: {station_id}, {year}, "
                        f"{frequency_name}"
                    )

                    if attempt < MAX_RETRIES:

                        time.sleep(
                            RETRY_DELAY * attempt
                        )


            # ------------------------------------------------
            # STOP IF CPCB CONNECTION IS UNAVAILABLE
            # ------------------------------------------------

            if entries is None:

                log_result(
                    station,
                    year,
                    frequency_name,
                    "API_CONNECTION_FAILED",
                    attempts,
                    output_file,
                    last_error
                )

                failed += 1

                raise RuntimeError(
                    "\nCPCB API is unavailable after retries. "
                    "Download stopped safely.\n"
                    "Restart this script later. Existing valid "
                    "files will be skipped."
                )


            # ------------------------------------------------
            # NO DATA FOR THIS YEAR
            # ------------------------------------------------

            if not entries:

                print(
                    f"  NO DATA: {year}"
                )

                no_data += 1

                time.sleep(REQUEST_DELAY)

                continue


            # ------------------------------------------------
            # DOWNLOAD ALL FILE ENTRIES FOR THIS YEAR
            # ------------------------------------------------

            try:

                frames = []

                for entry in entries:

                    filepath = entry.get("filepath")

                    if not filepath:
                        continue

                    print(
                        f"  Downloading: {filepath}"
                    )

                    df = client._read_repository_csv(
                        str(filepath)
                    )

                    if df is None or df.empty:
                        continue

                    frames.append(df)


                if not frames:

                    raise RuntimeError(
                        "No readable raw CSV files returned"
                    )


                # Combine if CPCB returns multiple files

                final_df = pd.concat(
                    frames,
                    ignore_index=True
                )


                if final_df.empty:

                    raise RuntimeError(
                        "Downloaded dataset is empty"
                    )


                # Save to temporary file first

                final_df.to_csv(
                    temp_file,
                    index=False
                )


                if not is_valid_file(temp_file):

                    raise RuntimeError(
                        "Downloaded CSV validation failed"
                    )


                # Replace final file atomically

                os.replace(
                    temp_file,
                    output_file
                )


                print(
                    f"  SUCCESS: {year} | "
                    f"Rows: {len(final_df):,} | "
                    f"Columns: {len(final_df.columns)}"
                )


                log_result(
                    station,
                    year,
                    frequency_name,
                    "SUCCESS",
                    attempts,
                    output_file,
                    (
                        f"Rows={len(final_df)}; "
                        f"Columns={len(final_df.columns)}"
                    )
                )


                successful += 1

                time.sleep(REQUEST_DELAY)


            except Exception as e:

                print(
                    f"  DOWNLOAD FAILED: {year} | {e}"
                )

                logging.exception(
                    f"Download failed: {station_id}, {year}"
                )

                if temp_file.exists():

                    try:
                        temp_file.unlink()
                    except Exception:
                        pass


                log_result(
                    station,
                    year,
                    frequency_name,
                    "DOWNLOAD_FAILED",
                    attempts,
                    output_file,
                    str(e)
                )

                failed += 1


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n")
print("=" * 75)
print("ALL INDIA RAW POLLUTANT DOWNLOAD COMPLETED")
print("=" * 75)

print("Stations:", len(stations))
print("Total station-year checks:", total_checks)
print("Successful downloads:", successful)
print("Skipped existing files:", skipped)
print("Years with no data:", no_data)
print("Failed downloads:", failed)

print("\nOUTPUT:")
print(OUTPUT_ROOT)

print("\nDOWNLOAD LOG:")
print(DOWNLOAD_LOG)

print("\nPROCESS LOG:")
print(PROCESS_LOG)

print("=" * 75)

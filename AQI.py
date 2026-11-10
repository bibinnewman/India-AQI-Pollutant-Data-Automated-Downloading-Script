
# ============================================================
# DOWNLOAD ALL INDIA CPCB HISTORICAL DAILY AQI DATA
# USING VAYUAYAN
#
# DATA TYPE:
#   Daily historical station-level AQI
#
# OUTPUT:
#   Separate CSV for each station and year
#
# FEATURES:
#   1. Automatically discovers all states, cities and stations
#   2. Discovers available years for each station
#   3. Downloads all available historical daily AQI files
#   4. Resumes interrupted downloads
#   5. Skips successfully downloaded files
#   6. Maintains success and failure logs
#   7. Saves station metadata
# ============================================================

import os
import re
import csv
import time
import logging

import pandas as pd

from pathlib import Path
from datetime import datetime
from vayuayan import CPCBHistorical


# ============================================================
# 1. SETTINGS
# ============================================================

OUTPUT_DIR = Path(
    r"C:\Users\Bibin\Downloads\CPCB_India_Historical_Daily_AQI"
)

DATA_DIR = OUTPUT_DIR / "Station_Year_Files"

LOG_DIR = OUTPUT_DIR / "Logs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

DOWNLOAD_LOG = LOG_DIR / "download_log.csv"
STATION_LIST_FILE = LOG_DIR / "all_india_stations.csv"

# Delay between downloads (seconds)
DOWNLOAD_DELAY = 0.5

# Retry attempts
MAX_RETRIES = 3

# ============================================================
# 2. LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(
            LOG_DIR / "download_process.log",
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

def safe_name(value):

    value = str(value).strip()

    value = re.sub(
        r'[<>:"/\\|?*]',
        "_",
        value
    )

    value = re.sub(
        r"\s+",
        "_",
        value
    )

    return value[:120]


def initialize_download_log():

    if not DOWNLOAD_LOG.exists():

        with open(
            DOWNLOAD_LOG,
            "w",
            newline="",
            encoding="utf-8"
        ) as f:

            writer = csv.writer(f)

            writer.writerow([
                "station_id",
                "station_name",
                "state",
                "city",
                "year",
                "status",
                "output_file",
                "message",
                "downloaded_at"
            ])


def write_log(
    station,
    year,
    status,
    output_file="",
    message=""
):

    with open(
        DOWNLOAD_LOG,
        "a",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            station["station_id"],
            station["station_name"],
            station["state"],
            station["city"],
            year,
            status,
            str(output_file),
            str(message),
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ])


def is_valid_existing_file(path):

    if not path.exists():
        return False

    if path.stat().st_size == 0:
        return False

    try:

        # Verify that the CSV can be read
        pd.read_csv(path, nrows=5)

        return True

    except Exception:

        return False


# ============================================================
# 4. INITIALIZE CPCB CLIENT
# ============================================================

logger.info("Initializing Vayuayan CPCB client...")

client = CPCBHistorical()

initialize_download_log()


# ============================================================
# 5. DISCOVER ALL INDIA STATIONS
# ============================================================

logger.info("Discovering all India stations...")

stations = {}

for state_entry, city_entry, station_entry in client.iter_stations():

    station_id = str(
        station_entry.get("station_id", "")
    ).strip()

    station_name = str(
        station_entry.get("station_name", "")
    ).strip()

    if not station_id:
        continue

    stations[station_id] = {

        "station_id": station_id,

        "station_name": station_name,

        "state": str(
            state_entry.get("state_name", "")
        ),

        "city": str(
            city_entry.get("city_name", "")
        )
    }


# Include stations present in the latest public RSS feed
# but absent from the bundled station directory.

try:

    for state_entry, city_entry, station_entry in client._rss_directory():

        station_id = str(
            station_entry.get("station_id", "")
        ).strip()

        if station_id and station_id not in stations:

            stations[station_id] = {

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

    logger.warning(
        f"Could not supplement station directory with RSS: {e}"
    )


logger.info(
    f"Total unique stations discovered: {len(stations)}"
)


# ============================================================
# 6. SAVE COMPLETE STATION LIST
# ============================================================

station_df = pd.DataFrame(
    list(stations.values())
)

station_df.to_csv(
    STATION_LIST_FILE,
    index=False
)

logger.info(
    f"Station list saved: {STATION_LIST_FILE}"
)


# ============================================================
# 7. DISCOVER AVAILABLE YEARS FOR EACH STATION
# ============================================================

logger.info(
    "Starting station-wise historical year discovery..."
)

total_stations = len(stations)

total_downloaded = 0
total_skipped = 0
total_failed = 0
total_no_data = 0

for station_number, station in enumerate(
    stations.values(),
    start=1
):

    station_id = station["station_id"]

    station_name = station["station_name"]

    state = station["state"]

    city = station["city"]

    logger.info("=" * 70)

    logger.info(
        f"[STATION {station_number}/{total_stations}] "
        f"{station_name} | {city} | {state} | {station_id}"
    )

    # --------------------------------------------------------
    # REQUEST ALL AVAILABLE DAILY AQI FILE PATHS
    # --------------------------------------------------------

    try:

        file_entries = client.get_file_path(

            station_id=station_id,

            station_name=station_name,

            state=state,

            city=city,

            year="",

            frequency="daily",

            data_type="stationLevel"

        )

    except Exception as e:

        logger.error(
            f"Year discovery failed for {station_id}: {e}"
        )

        write_log(
            station,
            "ALL",
            "DISCOVERY_FAILED",
            message=e
        )

        total_failed += 1

        continue


    if not file_entries:

        logger.warning(
            f"No historical AQI files found: {station_id}"
        )

        write_log(
            station,
            "ALL",
            "NO_DATA",
            message="No available file entries"
        )

        total_no_data += 1

        continue


    # --------------------------------------------------------
    # EXTRACT AVAILABLE YEARS
    # --------------------------------------------------------

    available_years = sorted({

        str(entry.get("year")).strip()

        for entry in file_entries

        if entry.get("year") is not None
        and str(entry.get("year")).strip()

    })


    if not available_years:

        logger.warning(
            f"No years identified for station {station_id}"
        )

        write_log(
            station,
            "ALL",
            "NO_YEARS",
            message="No year information in file entries"
        )

        total_no_data += 1

        continue


    logger.info(
        f"Available years: {', '.join(available_years)}"
    )


    # ========================================================
    # 8. DOWNLOAD EACH AVAILABLE YEAR
    # ========================================================

    for year in available_years:

        output_folder = (
            DATA_DIR
            / safe_name(state)
            / safe_name(city)
        )

        output_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        filename = (
            f"{safe_name(station_name)}_"
            f"{station_id}_"
            f"{year}_Daily_AQI.csv"
        )

        output_file = output_folder / filename

        temp_file = output_folder / (
            filename + ".part.csv"
        )


        # ----------------------------------------------------
        # RESUME: SKIP COMPLETED DOWNLOADS
        # ----------------------------------------------------

        if is_valid_existing_file(output_file):

            logger.info(
                f"SKIPPED (already downloaded): "
                f"{station_id} | {year}"
            )

            total_skipped += 1

            continue


        # Remove incomplete temporary files
        if temp_file.exists():

            temp_file.unlink()


        # ----------------------------------------------------
        # DOWNLOAD WITH RETRIES
        # ----------------------------------------------------

        success = False

        for attempt in range(
            1,
            MAX_RETRIES + 1
        ):

            try:

                logger.info(
                    f"Downloading {station_id} | {year} "
                    f"(Attempt {attempt}/{MAX_RETRIES})"
                )


                # Vayuayan downloads the station-level
                # historical daily AQI workbook and saves
                # the complete data as CSV.

                client.download_past_year_aqi_data_station_level(

                    station_id=station_id,

                    year=year,

                    save_location=str(temp_file)

                )


                # Verify downloaded file
                if not is_valid_existing_file(temp_file):

                    raise ValueError(
                        "Downloaded file is empty or invalid"
                    )


                # Move completed file into final location
                os.replace(
                    temp_file,
                    output_file
                )


                logger.info(
                    f"SUCCESS: {output_file}"
                )


                write_log(
                    station,
                    year,
                    "SUCCESS",
                    output_file
                )


                total_downloaded += 1

                success = True

                break


            except Exception as e:

                logger.warning(
                    f"Attempt {attempt} failed for "
                    f"{station_id} | {year}: {e}"
                )

                if temp_file.exists():

                    try:
                        temp_file.unlink()
                    except Exception:
                        pass

                if attempt < MAX_RETRIES:

                    time.sleep(
                        2 * attempt
                    )


        # ----------------------------------------------------
        # RECORD FINAL FAILURE
        # ----------------------------------------------------

        if not success:

            logger.error(
                f"FINAL FAILURE: {station_id} | {year}"
            )

            write_log(
                station,
                year,
                "FAILED",
                output_file,
                "All retry attempts failed"
            )

            total_failed += 1


        time.sleep(
            DOWNLOAD_DELAY
        )


    logger.info(
        f"Completed station: {station_id}"
    )


# ============================================================
# 9. FINAL SUMMARY
# ============================================================

logger.info("=" * 70)

logger.info("ALL INDIA CPCB DAILY AQI DOWNLOAD FINISHED")

logger.info("=" * 70)

logger.info(
    f"Total stations discovered : {total_stations}"
)

logger.info(
    f"Successful downloads      : {total_downloaded}"
)

logger.info(
    f"Already existing/skipped  : {total_skipped}"
)

logger.info(
    f"Failed downloads          : {total_failed}"
)

logger.info(
    f"Stations/queries no data  : {total_no_data}"
)

logger.info(
    f"Output directory          : {DATA_DIR}"
)

logger.info(
    f"Download log              : {DOWNLOAD_LOG}"
)

logger.info("=" * 70)

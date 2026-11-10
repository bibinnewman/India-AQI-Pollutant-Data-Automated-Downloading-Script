# VAYUAYAN 0.3.0
## CPCB India – Historical Daily AQI Data Downloader

An automated Python-based downloader for collecting historical **daily Air Quality Index (AQI) data** from Central Pollution Control Board (CPCB) monitoring stations across India using the `vayuayan` Python library.

The script automatically discovers available monitoring stations, identifies the historical years available for each station, and downloads station-level daily AQI datasets into individual CSV files.

It includes automatic station discovery, year discovery, download retries, resume functionality, file validation, and incremental logging.

---

## 1. Overview

This project automates the collection of historical daily AQI data from CPCB monitoring stations across India.

Unlike raw pollutant data downloads, this script specifically retrieves historical station-level AQI datasets using the Vayuayan historical AQI download functionality.

The downloader:

- Discovers CPCB monitoring stations across India.
- Supplements station records using the CPCB RSS directory.
- Identifies available historical years for individual stations.
- Downloads daily station-level AQI datasets.
- Saves separate CSV files for each station and year.
- Skips previously downloaded valid files.
- Automatically retries failed downloads.
- Resumes interrupted download sessions.
- Maintains success, failure, and discovery logs.
- Exports a complete station metadata file.

### Key specifications

| Parameter | Configuration |
|---|---|
| Data source | Central Pollution Control Board (CPCB), India |
| Python library | `vayuayan` |
| Data type | Historical station-level AQI |
| Temporal resolution | Daily |
| Station coverage | All stations discovered through available directories |
| Year selection | Automatically discovered per station |
| Output format | CSV |
| Download organization | Station-wise and year-wise |
| Resume support | Yes |
| Retry mechanism | Yes |
| Download logging | CSV and process log |

---

## 2. Features

### 2.1 Automatic CPCB Station Discovery

The script discovers available monitoring stations using two sources:

**Primary station directory**

```python
client.iter_stations()
```

**Supplementary RSS directory**

```python
client._rss_directory()
```

The RSS directory is used to supplement the primary station directory with additional station records.

Stations are indexed using their unique station IDs to avoid duplicate entries.

The following metadata are collected:

- Station ID
- Station name
- State
- City

The complete station list is exported as:

`all_india_stations.csv`

### 2.2 Automatic Historical Year Discovery

Unlike a downloader that checks a fixed year range, this script attempts to discover the available historical AQI years individually for each station.

It uses:

```python
client.get_file_path(
    station_id=station_id,
    station_name=station_name,
    state=state,
    city=city,
    year="",
    frequency="daily",
    data_type="stationLevel"
)
```

The returned file entries are used to identify the years available for each monitoring station.

For example:

```text
Station A:
2015, 2016, 2017, 2018, 2019, 2020

Station B:
2018, 2019, 2020, 2021, 2022

Station C:
2020, 2021, 2022, 2023, 2024
```

Each station is therefore processed according to its discovered historical data availability.

This avoids making unnecessary requests for years for which no files are listed.

### 2.3 Historical Daily AQI Download

The script downloads historical station-level daily AQI datasets using:

```python
client.download_past_year_aqi_data_station_level(
    station_id=station_id,
    year=year,
    save_location=str(temp_file)
)
```

The downloaded files are saved separately for each station and year.

Example:

```text
Station_Name_STATION_ID_2020_Daily_AQI.csv
```

**Important:** This script is designed to retrieve CPCB-provided historical AQI data. It does not calculate AQI independently from raw PM2.5, PM10, NO2, SO2, CO or other pollutant observations.

### 2.4 Automatic Resume Functionality

The script checks whether a previously downloaded CSV file exists and can be read before initiating another download.

The validation checks:

1. File existence.
2. Non-zero file size.
3. Successful CSV reading.

If the file passes validation, the corresponding station-year download is skipped.

This makes it possible to restart the script after:

- Internet interruptions.
- System shutdowns.
- Manual termination.
- CPCB service interruptions.
- Other execution failures.

Previously downloaded valid files are retained.

### 2.5 Automatic Retry Mechanism

Failed downloads are retried automatically.

Default configuration:

```python
MAX_RETRIES = 3
```

The retry delay increases with each failed attempt:

| Attempt | Waiting time before next attempt |
|---|---|
| 1 | 2 seconds |
| 2 | 4 seconds |
| 3 | No further retry |

After all retry attempts fail, the failure is recorded in the download log and processing continues with the next station-year combination.

### 2.6 Download Logging

Two log files are maintained.

**A. Download log**

`Logs/download_log.csv`

Records:

- Station ID
- Station name
- State
- City
- Year
- Download status
- Output file path
- Error or status message
- Download timestamp

Possible statuses include:

| Status | Description |
|---|---|
| SUCCESS | Historical AQI file downloaded successfully |
| FAILED | All download retry attempts failed |
| DISCOVERY_FAILED | Historical year discovery request failed |
| NO_DATA | No historical AQI files were returned |
| NO_YEARS | File entries were returned without identifiable years |

**B. Process log**

`Logs/download_process.log`

Maintains execution information, station processing messages, warnings, and error details.

---

## 3. Repository Structure

```text
VAYUAYAN-CPCB-Historical-AQI/
│
├── script.py
│
├── README.md
│
└── CPCB_India_Historical_Daily_AQI/
    │
    ├── Station_Year_Files/
    │   │
    │   ├── State/
    │   │   ├── City/
    │   │   │   ├── Station_Name_STATION_ID_2015_Daily_AQI.csv
    │   │   │   ├── Station_Name_STATION_ID_2016_Daily_AQI.csv
    │   │   │   └── ...
    │   │   │
    │   │   └── ...
    │   │
    │   └── ...
    │
    └── Logs/
        │
        ├── all_india_stations.csv
        ├── download_log.csv
        └── download_process.log
```

The output directory structure is generated automatically during execution.

---

## 4. Requirements

### Software requirements

- Python 3.9 or later recommended.
- Internet connection.
- Access to the CPCB historical AQI data service.
- Windows, Linux, or macOS.

### Python dependencies

- `vayuayan`
- `pandas`

The following modules are included in the Python standard library:

- `os`
- `re`
- `csv`
- `time`
- `logging`
- `pathlib`
- `datetime`

### Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/VAYUAYAN-CPCB-Historical-AQI.git
```

Navigate to the repository:

```bash
cd VAYUAYAN-CPCB-Historical-AQI
```

Install dependencies:

```bash
pip install pandas vayuayan
```

---

## 5. Configuration

Review the settings section in `script.py` before execution.

### Output directory

Default Windows configuration:

```python
OUTPUT_DIR = Path(
    r"C:\Users\Bibin\Downloads\CPCB_India_Historical_Daily_AQI"
)
```

For Linux systems:

```python
OUTPUT_DIR = Path(
    "/data/CPCB_India_Historical_Daily_AQI"
)
```

The script automatically creates the following directories:

```text
Station_Year_Files/
Logs/
```

### Download delay

```python
DOWNLOAD_DELAY = 0.5
```

Controls the waiting period between station-year downloads.

### Retry attempts

```python
MAX_RETRIES = 3
```

Defines the maximum number of attempts for an individual historical AQI file.

---

## 6. Execution

Execute the script using:

```bash
python script.py
```

The downloader performs the following operations:

1. Initializes the Vayuayan CPCB client.
2. Discovers monitoring stations.
3. Supplements station information using RSS records.
4. Removes duplicate station IDs.
5. Exports station metadata.
6. Requests historical daily AQI file information for each station.
7. Extracts the available historical years.
8. Checks whether each station-year file already exists.
9. Downloads the available historical AQI datasets.
10. Validates the downloaded CSV files.
11. Saves the final station-year files.
12. Updates the download log.
13. Displays the final execution summary.

---

## 7. Download Workflow

```text
                START
                  |
                  v
          Initialize CPCB Client
                  |
                  v
         Discover CPCB Stations
                  |
                  v
        Supplement RSS Directory
                  |
                  v
         Remove Duplicate Stations
                  |
                  v
        Export Station Metadata
                  |
                  v
         Iterate Through Stations
                  |
                  v
       Discover Available AQI Years
                  |
                  v
          Extract Available Years
                  |
                  v
        Iterate Through Station-Years
                  |
                  v
         Check Existing CSV File
                  |
             +----+----+
             |         |
           Valid    Missing/
             |      Invalid
             v         |
            Skip       v
                  Download Daily AQI
                         |
                         v
                  Validate CSV File
                         |
                    +----+----+
                    |         |
                  Valid     Invalid
                    |         |
                    v         v
                Save CSV   Retry Download
                    |
                    v
               Update Log
                    |
                    v
              Next Station-Year
                    |
                    v
                   END
```

---

## 8. Output Data

The script generates separate CSV files for each station and available historical year.

Example:

```text
CPCB_India_Historical_Daily_AQI/
│
├── Station_Year_Files/
│   │
│   ├── Haryana/
│   │   │
│   │   ├── Faridabad/
│   │   │   ├── Station_A_1234_2019_Daily_AQI.csv
│   │   │   ├── Station_A_1234_2020_Daily_AQI.csv
│   │   │   └── Station_A_1234_2021_Daily_AQI.csv
│   │   │
│   │   └── Gurugram/
│   │       ├── Station_B_5678_2019_Daily_AQI.csv
│   │       └── Station_B_5678_2020_Daily_AQI.csv
│   │
│   └── Delhi/
│       └── Delhi/
│           └── ...
│
└── Logs/
    ├── all_india_stations.csv
    ├── download_log.csv
    └── download_process.log
```

The actual column structure depends on the CSV data returned by the CPCB historical AQI service and the Vayuayan download method.

The script does not independently modify the AQI values or calculate new AQI categories.

---

## 9. Error Handling and Data Integrity

The downloader includes several safeguards.

| Situation | Script behaviour |
|---|---|
| Existing valid CSV | Skips download |
| Missing CSV | Initiates download |
| Invalid existing CSV | Attempts download again |
| No historical file entries | Records NO_DATA |
| No identifiable years | Records NO_YEARS |
| Year discovery exception | Records DISCOVERY_FAILED |
| Download exception | Retries up to three times |
| All retries exhausted | Records FAILED |
| Successful download | Atomically replaces final file |

### Temporary file handling

Files are first downloaded using a temporary filename:

```text
Station_ID_2020_Daily_AQI.csv.part.csv
```

After successful CSV validation, the temporary file is renamed to its final filename.

```python
os.replace(
    temp_file,
    output_file
)
```

This helps prevent incomplete downloads from being mistaken for completed datasets.

---

## 10. Final Execution Summary

After processing all discovered stations, the script displays a summary similar to:

```text
======================================================================
ALL INDIA CPCB DAILY AQI DOWNLOAD FINISHED
======================================================================

Total stations discovered : [Total stations]
Successful downloads      : [Successful]
Already existing/skipped  : [Skipped]
Failed downloads          : [Failed]
Stations/queries no data  : [No data]

Output directory          : Station_Year_Files/
Download log              : Logs/download_log.csv

======================================================================
```

The summary helps assess the overall download process and identify stations or years requiring further investigation.

---

## 11. Intended Applications

The collected historical daily AQI datasets can support:

- Historical AQI assessment across Indian cities.
- Long-term air-quality trend analysis.
- Spatial and temporal AQI comparisons.
- State-wise and city-wise air-quality assessments.
- Historical AQI category distribution analysis.
- Identification of high-pollution periods.
- Seasonal AQI variation studies.
- Environmental epidemiology.
- Population-level air-pollution exposure research.
- Integration with geospatial monitoring station databases.
- Comparison with independently calculated AQI from raw pollutant observations.

---

## 12. Important Notes and Limitations

1. **Historical availability:** Not every CPCB monitoring station has historical AQI records for every year.

2. **Dynamic year discovery:** Available years are determined using the file entries returned by the CPCB service at execution time.

3. **Station coverage:** The script covers stations discoverable through the primary station directory and supplementary RSS directory. It cannot guarantee complete coverage of all historically operational CPCB stations.

4. **API dependency:** Downloading depends on CPCB service availability and compatibility with the installed Vayuayan library.

5. **Internal library methods:** The script uses `_rss_directory()`, an internal method that may change between library versions.

6. **CSV validation:** Basic CSV validation confirms readability but does not guarantee that every AQI observation has been downloaded or that the dataset is complete.

7. **Resume behaviour:** Existing readable CSV files are skipped without rechecking their contents against CPCB.

8. **Historical AQI interpretation:** CPCB-reported AQI values should be distinguished from AQI independently calculated using pollutant concentrations.

9. **No additional processing:** The script does not perform AQI recalculation, pollutant imputation, temporal aggregation, or statistical analysis.

10. **Download logging:** Existing valid files skipped during execution are not added as new SUCCESS records to the download log.

---

## 13. Data Source and Acknowledgements

**Primary data source:**

Central Pollution Control Board (CPCB), Ministry of Environment, Forest and Climate Change, Government of India.

Website: https://cpcb.nic.in/

The `vayuayan` Python library is used to access the CPCB historical AQI data service.

This repository is an independent data retrieval workflow and is not an official CPCB application or affiliated with or endorsed by CPCB.

Users should follow applicable CPCB data-use conditions and acknowledge CPCB as the original data source in research publications.

---

## 14. License

The repository license does not supersede the terms governing the original CPCB datasets or the Vayuayan library.

---

**VAYUAYAN 0.3.0 | CPCB India Historical Daily AQI Downloader**

*Automating the collection of historical daily Air Quality Index observations across India.*

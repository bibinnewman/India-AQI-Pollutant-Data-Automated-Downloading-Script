# VAYUAYAN 0.3.0
## CPCB India – All Stations Raw Pollutant Data Downloader

A Python-based automated downloader for retrieving historical raw air-quality pollutant observations from the **Central Pollution Control Board (CPCB), India**, using the `vayuayan` Python library.

The script discovers available CPCB monitoring stations across India and downloads pollutant observations for individual stations and years, organizing the resulting datasets into structured CSV files.

It supports automatic station discovery, year-wise data retrieval, retry mechanisms, download logging, and resuming interrupted downloads.

---

## 1. Overview

The CPCB Historical Data Downloader automates the collection of historical air-quality observations from CPCB monitoring stations across India.

Instead of manually downloading historical datasets station by station, this script:

- Discovers available CPCB monitoring stations.
- Supplements station discovery using the CPCB RSS directory.
- Queries historical data availability for each station and year individually.
- Downloads raw pollutant observation CSV files.
- Combines multiple CSV files returned for a station-year combination.
- Organizes downloaded data into individual station-year files.
- Skips previously downloaded and valid files.
- Retries failed API requests.
- Maintains an incremental download log.
- Stops safely when the CPCB API becomes unavailable after repeated attempts.

### Key specifications

| Parameter | Configuration |
|---|---|
| Data source | Central Pollution Control Board (CPCB), India |
| Python library | `vayuayan` |
| Data type | Raw pollutant observations |
| Default frequency | Daily |
| Historical start year | 2015 |
| Historical end year | Current year |
| Station coverage | All stations discovered through available directories |
| Output format | CSV |
| Download organization | Station-wise and year-wise |
| Resume support | Yes |
| Retry mechanism | Yes |
| Download logging | CSV and process log |

---

## 2. Features

### 2.1 Automatic CPCB Station Discovery

The script automatically retrieves available monitoring stations using:

- `client.iter_stations()` – Main CPCB station directory.
- `client._rss_directory()` – Additional RSS station directory.

Station records are indexed using their unique station IDs to avoid duplicate entries.

The station metadata includes:

- Station ID
- Station name
- State
- City

The complete discovered station list is exported as:

`all_india_stations.csv`

### 2.2 Individual Year-wise Data Retrieval

CPCB historical data availability is queried separately for each year.

The script checks every combination of:

`Station × Frequency × Year`

For example:

- Station A – 2015
- Station A – 2016
- Station A – 2017
- Station B – 2015
- Station B – 2016

This explicit year-wise approach avoids relying on blank-year API requests.

### 2.3 Multiple Data Frequencies

The script supports three configurable historical data frequencies.

| Frequency | API code | Description |
|---|---|---|
| 15-minute | `15M` | 15-minute observations |
| Hourly | `1H` | Hourly observations |
| Daily | `1D` | Daily observations |

**Default configuration:** Daily observations only.

The frequency can be changed in `script.py`.

To download daily observations:

```python
FREQUENCIES = {
    "daily": "1D"
}
```

To download hourly observations:

```python
FREQUENCIES = {
    "hourly": "1H"
}
```

To download 15-minute observations:

```python
FREQUENCIES = {
    "15_minute": "15M"
}
```

To download all three frequencies:

```python
FREQUENCIES = {
    "15_minute": "15M",
    "hourly": "1H",
    "daily": "1D"
}
```

**Note:** The selected frequency is passed to the CPCB API. Actual data availability depends on the station and historical period.

### 2.4 Automatic Resume After Interruption

The downloader checks whether an output CSV already exists and passes basic validation before requesting the corresponding station-year dataset again.

The validation checks:

1. File existence.
2. File size greater than 10 bytes.
3. Successful CSV reading.
4. At least two columns.
5. At least one data row in the first five rows.

If the file passes validation, the download is skipped.

This allows the script to be restarted after:

- Internet disconnection.
- System shutdown.
- Manual interruption.
- CPCB server downtime.
- Other execution interruptions.

Previously downloaded valid files are retained.

### 2.5 Automatic Retry Mechanism

Failed API requests are retried automatically.

Default configuration:

```python
MAX_RETRIES = 3
RETRY_DELAY = 10
REQUEST_DELAY = 0.3
```

The retry delay increases with each attempt:

| Attempt | Waiting time before next attempt |
|---|---|
| 1 | 10 seconds |
| 2 | 20 seconds |
| 3 | No further retry |

If all attempts fail, the script records the error and stops execution safely.

This prevents the downloader from continuing through thousands of station-year combinations when the CPCB API is unavailable.

### 2.6 Incremental Logging

Two log files are maintained.

**Download log: `download_log.csv`**

Records individual station-year download outcomes, including:

- Station ID
- Station name
- State
- City
- Year
- Frequency
- Download status
- Number of API attempts
- Output file path
- Error message
- Timestamp

Possible recorded statuses include:

- `SUCCESS`
- `API_CONNECTION_FAILED`
- `DOWNLOAD_FAILED`

**Process log: `process.log`**

Maintains detailed execution information and error tracebacks for troubleshooting.

---

## 3. Repository Structure

```text
VAYUAYAN-CPCB-Downloader/
│
├── script.py
│
├── README.md
│
└── CPCB_India_Raw_Pollutant_Data/
    │
    ├── all_india_stations.csv
    │
    ├── Station_Year_Files/
    │   │
    │   ├── State/
    │   │   ├── City/
    │   │   │   ├── Station_Name_STATION_ID/
    │   │   │   │   ├── STATION_ID_2015_daily.csv
    │   │   │   │   ├── STATION_ID_2016_daily.csv
    │   │   │   │   ├── STATION_ID_2017_daily.csv
    │   │   │   │   └── ...
    │   │   │   │
    │   │   └── ...
    │   │
    │   └── ...
    │
    └── Logs/
        │
        ├── download_log.csv
        │
        └── process.log
```

The output directory is created automatically when the script runs.

---

## 4. Requirements

### Software requirements

- Python 3.9 or later recommended.
- Internet connection.
- Access to the CPCB historical data service.
- Windows, Linux, or macOS.

### Python dependencies

- `vayuayan`
- `pandas`

Other imported modules (`os`, `re`, `csv`, `time`, `logging`, `pathlib`, and `datetime`) are part of the Python standard library.

### Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/VAYUAYAN-CPCB-Downloader.git
```

Navigate into the repository:

```bash
cd VAYUAYAN-CPCB-Downloader
```

Install the dependencies:

```bash
pip install pandas vayuayan
```

If `vayuayan` is already installed, only the remaining dependencies need to be installed.

---

## 5. Configuration

Before executing the script, review the settings section in `script.py`.

### Output directory

Default configuration:

```python
OUTPUT_ROOT = Path(
    r"C:\Users\Bibin\Downloads\CPCB_India_Raw_Pollutant_Data"
)
```

Change this path according to your system.

For example, on Linux:

```python
OUTPUT_ROOT = Path(
    "/data/CPCB_India_Raw_Pollutant_Data"
)
```

### Historical year range

```python
START_YEAR = 2015
END_YEAR = datetime.now().year
```

The script automatically determines the current year.

For example, in 2026, it will check years 2015–2026.

### Frequency selection

```python
FREQUENCIES = {
    "daily": "1D"
}
```

Modify this dictionary to select the desired observation frequency.

### Request and retry settings

```python
MAX_RETRIES = 3
RETRY_DELAY = 10
REQUEST_DELAY = 0.3
```

These parameters control retry attempts and request delays.

---

## 6. Execution

Run the downloader using:

```bash
python script.py
```

The script performs the following operations:

1. Initializes the CPCB historical data client.
2. Discovers CPCB monitoring stations.
3. Supplements the station directory using RSS records.
4. Removes duplicate station IDs.
5. Exports the station metadata.
6. Creates station-wise output directories.
7. Queries each selected year individually.
8. Downloads available raw CSV files.
9. Combines multiple files belonging to the same station-year.
10. Validates and saves the resulting CSV.
11. Updates the download log.
12. Displays the final download summary.

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
       Remove Duplicate IDs
               |
               v
       Export Station Metadata
               |
               v
       Iterate Through Stations
               |
               v
       Select Data Frequency
               |
               v
       Iterate Through Years
               |
               v
       Check Existing CSV File
               |
          +----+----+
          |         |
        Valid     Invalid/
          |       Missing
          v         |
         Skip       v
                 Query CPCB API
                      |
                      v
                 Data Available?
                  /         \
                No           Yes
                |             |
                v             v
             Continue    Download CSV Files
                              |
                              v
                       Combine Dataframes
                              |
                              v
                       Validate Dataset
                              |
                              v
                       Save Final CSV
                              |
                              v
                       Update Download Log
                              |
                              v
                       Next Station-Year
                              |
                              v
                             END
```

---

## 8. Output Data

Each successful station-year download produces an individual CSV file.

Example:

```text
Station_Year_Files/
└── Haryana/
    └── Faridabad/
        └── Station_Name_STATION_ID/
            ├── STATION_ID_2015_daily.csv
            ├── STATION_ID_2016_daily.csv
            ├── STATION_ID_2017_daily.csv
            └── STATION_ID_2018_daily.csv
```

The downloaded CSV files retain the original pollutant observation columns returned by CPCB.

If multiple repository CSV files are returned for the same station-year combination, they are combined into a single dataframe and saved as one output CSV.

The script does not perform additional pollutant cleaning, unit conversion, temporal aggregation, missing-value imputation, or air-quality index calculation.

The downloaded observations are therefore intended to serve as raw input for subsequent air-quality data processing and analysis.

---

## 9. Error Handling and Data Integrity

The downloader implements several mechanisms to reduce incomplete downloads.

| Situation | Script behaviour |
|---|---|
| Existing valid CSV | Skips download |
| Missing output CSV | Requests data |
| Invalid existing CSV | Attempts download again |
| CPCB returns no data | Continues to next year |
| API request fails | Retries up to configured limit |
| API unavailable after retries | Logs failure and stops |
| Empty downloaded dataset | Records download failure |
| Temporary file validation fails | Rejects temporary output |
| Successful download | Atomically replaces final output file |

### Temporary file handling

Data are first written to a temporary file:

```text
STATION_ID_2020_daily.tmp.csv
```

After successful validation, the temporary file is renamed to:

```text
STATION_ID_2020_daily.csv
```

This reduces the risk of leaving partially written final CSV files after an interrupted save operation.

---

## 10. Important Notes and Limitations

1. **CPCB data availability:** Not every station has observations for every year or frequency.

2. **Station coverage:** The downloader retrieves stations returned by the CPCB station directory and supplementary RSS directory. It does not guarantee that every historically existing CPCB station is discoverable.

3. **API dependency:** The downloader depends on CPCB API availability and the internal methods exposed by the installed `vayuayan` library.

4. **API compatibility:** Methods prefixed with an underscore, such as `_new_api_json`, `_rss_directory`, and `_read_repository_csv`, are internal library methods and may change between library versions.

5. **No-data handling:** Years without available files are skipped. They are counted in the final execution summary but are not individually written to `download_log.csv`.

6. **Download retries:** The retry mechanism applies to the API year-discovery request. Individual repository CSV download failures are logged, but are not automatically retried by the current implementation.

7. **Resume validation:** Existing files are checked using basic CSV validation. This does not establish that every observation in a previously downloaded file is complete or correct.

8. **Request frequency:** Download delays should be configured responsibly to avoid excessive requests to CPCB services.

9. **Raw observations:** The script preserves the returned observation columns and does not independently verify pollutant units, measurement methods, or station-level data quality.

---

## 11. Final Execution Summary

After processing all discovered stations, the script displays:

```text
===========================================================================
ALL INDIA RAW POLLUTANT DOWNLOAD COMPLETED
===========================================================================

Stations:                  [Total stations]
Total station-year checks: [Total checks]
Successful downloads:     [Successful]
Skipped existing files:    [Skipped]
Years with no data:        [No data]
Failed downloads:          [Failed]

OUTPUT:
CPCB_India_Raw_Pollutant_Data

DOWNLOAD LOG:
Logs/download_log.csv

PROCESS LOG:
Logs/process.log

===========================================================================
```

The summary provides an overview of the download process and helps identify missing or failed station-year datasets.

---

## 12. Intended Applications

The downloaded datasets can be used as input for:

- Historical air-quality assessment across Indian cities.
- Long-term pollutant trend analysis.
- Spatial and temporal air pollution studies.
- Station-wise pollutant availability assessment.
- PM2.5, PM10, NO2, SO2, CO, O3 and other pollutant analyses, where available.
- Development of national air-quality databases.
- Environmental epidemiology and exposure assessment.
- Air pollution modelling and machine-learning applications.
- Integration with geospatial monitoring station databases.

---

## 13. Acknowledgements and Data Source

**Primary data source:**

Central Pollution Control Board (CPCB), Ministry of Environment, Forest and Climate Change, Government of India.

Website: https://cpcb.nic.in/

The `vayuayan` Python library is used to interact with the CPCB historical data service.

This repository provides an automated data retrieval workflow. It is not an official CPCB application and is not affiliated with or endorsed by CPCB.

Users should consult CPCB's applicable data-use conditions and acknowledge the original data source in any resulting research or publication.

---


## 14. License

The repository license does not supersede the terms governing the original CPCB datasets or the Vayuayan library

This repository contains an independent Python script for downloading historical CPCB data using the `vayuayan` Python package.

The script does not claim ownership of CPCB datasets or the`vayuayan` package. Their respective terms and licenses apply.



**VAYUAYAN 0.3.0 | CPCB India Historical Raw Pollutant Data Downloader**

*Automating the collection of historical air-quality observations across India.*

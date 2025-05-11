# ETL Pipeline: Mental Health and OECD Indicators Integration

![ETL Pipeline](https://img.shields.io/badge/process-ETL-%230075ff)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Pandas](https://img.shields.io/badge/pandas-1.3%2B-orange)

This project implements an ETL (Extract, Transform, Load) pipeline to integrate OECD economic indicators with mental health survey data from 2014 and 2016.

##  Project Overview

The pipeline performs:
- Extraction of raw data from multiple sources
- Data cleaning and standardization
- Feature engineering and transformation
- Integration of datasets
- Data quality validation
- Output generation for analysis

##  Project Structure

```bash
etl-project/
│── data/
│   ├── raw/          # Original data files (input)
│   ├── processed/    # Cleaned intermediate data
│   └── outputs/      # Final integrated datasets
│── docs/             # Documentation
│── notebooks/        # Jupyter notebooks for analysis
│── src/
│   ├── etl.py        # Main ETL pipeline
│   ├── config.py     # Configuration parameters
│   └── tests/        # Unit tests
│── requirements.txt  # Python dependencies
│── README.md         # This file
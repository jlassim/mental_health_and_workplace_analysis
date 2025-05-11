# Architecture Technique du Pipeline ETL

## Diagramme du Flux de Données




##  Overview

This ETL pipeline is designed to:
1. Load raw data from surveys (2014, 2016) and OECD (2024)
2. Clean and standardize disparate formats
3. Transform and engineer new features
4. Integrate datasets across years and sources
5. Validate the quality of integrated data
6. Output the processed data for downstream use

---

## 🗂️ Directory Structure

etl-project/
│── data/
│   ├── raw/               # oecd_2024.csv, survey_2014.csv, survey_2016.csv
│   ├── processed/         # Généré par le pipeline
│   └── outputs/          # Généré par le pipeline
│── docs/
│   ├── architecture.md    # Documentation technique
│   └── data_sources.md   # Détails des sources
│── notebooks/
│   └── exploration.ipynb # Analyses exploratoires
│── src/
│   ├── etl.py            # Script principal 
│   ├── config.py         # Configuration centralisée
│   ├── utils.py          # Fonctions utilitaires
│   └── tests/
│       ├── test_etl.py
│          
│── README.md             # Documentation complète
│── requirements.txt      # Dépendances

---

##  Step-by-Step Architecture

### 1.  Data Loading
- Load CSV files from `data/raw` directory using `pandas.read_csv()`
- Returns three DataFrames: `df_oecd`, `df_2014`, and `df_2016`

### 2. Data Cleaning

#### OECD Dataset:
- Drop null/duplicate or irrelevant columns
- Standardize column names and types
- Rename columns for clarity

#### Survey 2014:
- Standardize lowercase columns
- Fill missing values in key columns (`state`, `work_interfere`, etc.)
- Handle outlier ages and convert timestamps

#### Survey 2016:
- Normalize column names (snake_case, no special chars)
- Fill missing values based on percentage threshold
- Clean and validate age column

---

### 3. Data Transformation

#### OECD:
- Pivot data to wide format (indicators as columns)
- Compute composite score (average across indicators)
- Rank countries based on each indicator

#### Survey 2014 & 2016:
- Normalize country names (e.g., US → USA)
- Standardize gender categories (e.g., 'f', 'female' → 'Female')
- Map qualitative answers to numerical scores:
  - 2014: `mh_impact_score`
  - 2016: `has_benefits` flag

---

### 4.  Data Integration

- Aggregate survey data by country:
  - Mean age, treatment rate, benefit access
  - Most frequent gender per country
- Merge survey aggregates with OECD data using `country_code`
- Derive new metrics like:
  - `avg_age`
  - `benefit_coverage_change` between 2014 and 2016

---

### 5.  Data Validation

- Check for:
  - Missing values
  - Age values outside expected ranges
  - Invalid benefit rates (not between 0 and 1)

- Return dictionary of issues for debugging or logging

---

### 6.  Output

- Save the final cleaned and validated DataFrame to `data/outputs/`
- Output format: CSV or serialized `pickle` (optional)

---

## Technologies Used

- Python 3.10+
- pandas
- numpy
- scikit-learn (for imputation and scaling)
- JSON (for configuration or reporting)

---

##  Example Outputs

- `final_dataset.csv`: Fully integrated dataset
- `validation_report.json`: Summary of quality checks

"""
ETL Pipeline for Mental Health and OECD Data Integration

This script performs:
1. Data loading from multiple sources
2. Data cleaning and standardization
3. Data transformation and feature engineering
4. Data integration
5. Data quality validation
6. Saving processed data
"""

# Step 0: Install & Import
import os
import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer
from sklearn.preprocessing import StandardScaler
import json

# Configuration
DATA_RAW_PATH = os.path.join('..', 'data', 'raw')
DATA_PROCESSED_PATH = os.path.join('..', 'data', 'processed')
OUTPUTS_PATH = os.path.join('..', 'data', 'outputs')

# Step 1: Data Loading Functions
def load_datasets():
    """Load raw datasets from data/raw directory"""
    df_oecd = pd.read_csv(os.path.join(DATA_RAW_PATH, 'oecd_2024.csv'))
    df_2014 = pd.read_csv(os.path.join(DATA_RAW_PATH, 'survey_2014.csv'))
    df_2016 = pd.read_csv(os.path.join(DATA_RAW_PATH, 'survey_2016.csv'))
    return df_oecd, df_2014, df_2016

# Step 2: Data Cleaning Functions
def clean_oecd(df_oecd):
    """Clean OECD dataset"""
    # Drop unnecessary columns(all null)
    df_oecd.drop(['BASE_PER', 'Base reference period','Inequality','Observation Status','Observation Value'], axis=1, inplace=True)
    # Handle duplicate columns (indicator, measure, inequality, etc.)
    df_oecd = df_oecd.loc[:,~df_oecd.columns.duplicated()]

    # Strip leading/trailing spaces
    df_oecd.columns = df_oecd.columns.str.strip()# Remove any extra spaces

    # rename columns for clarity
    df_oecd.rename(columns={
        'STRUCTURE': 'structure_type',
        'STRUCTURE_ID': 'structure_identifier',
        'STRUCTURE_NAME': 'structure_name',
        'ACTION': 'action_type',
        'LOCATION': 'location_code',
        'Country': 'country_code',
        'INDICATOR': 'indicator_code',
        'Indicator': 'indicator_name',# Make sure there’s no duplication in column names
        'MEASURE':'measure_type1',
        'Measure': 'measure_type2',
        'Inequality': 'inequality_level',
        'OBS_VALUE': 'observed_value',
        'OBS_STATUS': 'status',
        'UNIT_MEASURE': 'unit_of_measurement',
        'Unit of Measures': 'unit_of_measurement_full',
        'UNIT_MULT': 'multiplier',
    }, inplace=True)
    return df_oecd

def clean_survey_2014(df_2014):
    """Clean 2014 survey data"""
    # Standardize column names
    df_2014.columns = df_2014.columns.str.lower()

    # Handle missing values
    df_2014['state'].fillna('Unknown', inplace=True)
    df_2014['self_employed'].fillna('Unknown', inplace=True)
    df_2014['work_interfere'].fillna('Unknown', inplace=True)
    df_2014['comments'].fillna('No comments', inplace=True)

    # Convert timestamp to datetime
    df_2014['timestamp'] = pd.to_datetime(df_2014['timestamp'])

    # Clean age column (check for outliers)
    df_2014['age'] = df_2014['age'].apply(lambda x: x if 18 <= x <= 100 else np.nan)
    df_2014['age'].fillna(df_2014['age'].median(), inplace=True)
    return df_2014

def clean_survey_2016(df_2016):
    """Clean 2016 survey data"""
    # Standardize column names
    df_2016.columns = df_2016.columns.str.lower().str.replace(' ', '_').str.replace('?', '').str.replace('/', '_')

    # Handle missing values for key columns
    df_2016['how_many_employees_does_your_company_or_organization_have'].fillna('Unknown', inplace=True)
    df_2016['is_your_employer_primarily_a_tech_company_organization'].fillna('Unknown', inplace=True)

    # For columns with many missing values, consider creating a "missing" category
    cols_with_many_nulls = [col for col in df_2016.columns if df_2016[col].isnull().mean() > 0.3]
    for col in cols_with_many_nulls:
        df_2016[col].fillna('Not specified', inplace=True)

    # Clean age column
    df_2016['what_is_your_age'] = pd.to_numeric(df_2016['what_is_your_age'], errors='coerce')
    df_2016['what_is_your_age'] = df_2016['what_is_your_age'].apply(lambda x: x if 18 <= x <= 100 else np.nan)
    df_2016['what_is_your_age'].fillna(df_2016['what_is_your_age'].median(), inplace=True)
    return df_2016

# Step 3: Data Transformation Functions
def transform_oecd(df_oecd):
    """Transform OECD data"""
    # Pivot OECD data to have indicators as columns
    oecd_pivot = df_oecd.pivot_table(
        index=['country_code', 'location_code'],
        columns='indicator_code',
        values='observed_value',
        aggfunc='first'  # Takes first value if duplicates exist
    ).reset_index()

    # Create composite indices (example: average of all indicators)
    numeric_cols = oecd_pivot.select_dtypes(include=[np.number]).columns
    oecd_pivot['composite_score'] = oecd_pivot[numeric_cols].mean(axis=1)

    # Add rank columns
    for col in numeric_cols:
        oecd_pivot[f'{col}_rank'] = oecd_pivot[col].rank(ascending=False, method='min')
    return oecd_pivot

def transform_surveys(df_2014, df_2016):
    """Transform survey data"""
    # Standardize country names across all datasets
    country_mapping = {
        'United States': 'USA',
        'United States of America': 'USA',
        'US': 'USA',
        'United Kingdom': 'UK',
        'UK': 'UK',
        'CA': 'Canada',
        'DE': 'Germany'
    }

    df_2014['country'] = df_2014['country'].replace(country_mapping)
    df_2016['what_country_do_you_live_in'] = df_2016['what_country_do_you_live_in'].replace(country_mapping)

    # Create consistent age column
    df_2016 = df_2016.rename(columns={'what_is_your_age': 'age'})

    # Standardize gender values
    gender_mapping = {
        'female': 'Female',
        'male': 'Male',
        'f': 'Female',
        'm': 'Male',
        'woman': 'Female',
        'man': 'Male'
    }

    df_2014['gender'] = df_2014['gender'].replace(gender_mapping, regex=True).fillna('Other')
    df_2016['what_is_your_gender'] = df_2016['what_is_your_gender'].replace(gender_mapping, regex=True).fillna('Other')

    # Create mental health impact score (2014)
    df_2014['mh_impact_score'] = df_2014['work_interfere'].map({
        'Never': 0,
        'Rarely': 1,
        'Sometimes': 2,
        'Often': 3,
        'Unknown': 1
    })

    # Create benefit coverage flag (2016)
    df_2016['has_benefits'] = df_2016['does_your_employer_provide_mental_health_benefits_as_part_of_healthcare_coverage'].map({
        'Yes': 1,
        'No': 0,
        'I don\'t know': 0,
        'Not eligible for coverage / N/A': 0
    })
    return df_2014, df_2016

# Step 4: Data Integration Function
def merge_datasets(oecd_pivot, df_2014, df_2016):
    """Merge all datasets"""
    # Convert Yes/No to 1/0
    df_2014['treatment'] = df_2014['treatment'].map({'Yes': 1, 'No': 0})

    # Or if it's already numeric but stored as strings:
    df_2014['treatment'] = pd.to_numeric(df_2014['treatment'], errors='coerce')
    # Aggregate survey data by country
    survey_2014_agg = df_2014.groupby('country').agg({
        'treatment': 'mean',
        'mh_impact_score': 'mean',
        'age': 'mean',
        'gender': lambda x: x.mode()[0] if not x.mode().empty else 'Unknown'
    }).add_prefix('2014_')

    survey_2016_agg = df_2016.groupby('what_country_do_you_live_in').agg({
        'has_benefits': 'mean',
        'age': 'mean',
        'what_is_your_gender': lambda x: x.mode()[0] if not x.mode().empty else 'Unknown'
    }).add_prefix('2016_').rename_axis('country')

    # Step 3: Merge datasets
    final_df = oecd_pivot.merge(
        survey_2014_agg,
        left_on='country_code',
        right_index=True,
        how='left'
    ).merge(
        survey_2016_agg,
        left_on='country_code',
        right_index=True,
        how='left'
    )

    # Calculate derived metrics
    final_df['avg_age'] = final_df[['2014_age', '2016_age']].mean(axis=1)
    final_df['benefit_coverage_change'] = final_df['2016_has_benefits'] - final_df['2014_treatment']
    return final_df

# Step 5: Data Quality Validation
def validate_data(df):
    """Validate data quality"""
    results = {}

    # Check for missing values
    results['missing_values'] = df.isnull().sum()[df.isnull().sum() > 0].to_dict()

    # Check age ranges
    results['invalid_ages'] = {
        '2014': df[~df['2014_age'].between(18, 70)].shape[0],
        '2016': df[~df['2016_age'].between(18, 70)].shape[0]
    }

    # Check benefit coverage rates
    results['invalid_benefit_rates'] = df[
        ~df['2016_has_benefits'].between(0, 1, inclusive='both')
    ].shape[0]

    return results

def clean_data(df):
    """Additional cleaning for final dataframe"""
    # --- Rename columns for clarity
    rename_map = {
        "CG_SENG": "Gender_Equality_in_STEM",
        "CG_VOTO": "Women_Voter_Turnout",
        "EQ_AIRP": "Air_Pollution_Index",
        "EQ_WATER": "Water_Quality_Index",
        "ES_EDUA": "Adult_Education_Level",
        "ES_EDUEX": "Public_Education_Expenditure",
        "ES_STCS": "Student_Performance_Score",
        "HO_BASE": "Access_to_Basic_Housing",
        "HO_HISH": "High_Housing_Cost_Burden",
        "HO_NUMR": "Average_Number_of_Rooms",
        "HS_LEB": "Life_Expectancy",
        "HS_SFRH": "Self_Reported_Health",
        "IW_HADI": "Household_Disposable_Income",
        "IW_HNFW": "Net_Financial_Wealth",
        "JE_EMPL": "Employment_Rate",
        "JE_LMIS": "Job_Market_Insecurity",
        "JE_LTUR": "Long_Term_Unemployment_Rate",
        "JE_PEARN": "Average_Earnings"
    }

    df = df.rename(columns=rename_map)

    # --- Convert numerical columns to float ---
    num_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors='coerce')

    # --- Handle missing values using KNN Imputer ---
    imputer = KNNImputer(n_neighbors=3)
    df[num_cols] = imputer.fit_transform(df[num_cols])

    # --- Normalize numerical features (optional, useful for modeling) ---
    scaler = StandardScaler()
    df[num_cols] = scaler.fit_transform(df[num_cols])

    # --- Ensure country and location codes are uppercase and clean ---
    df['country_code'] = df['country_code'].str.strip().str.upper()
    df['location_code'] = df['location_code'].str.strip().str.upper()

    return df

# Step 6: Save Outputs
def save_outputs(final_df, df_oecd, df_2014, df_2016, validation_results, prefix=''):
    """Save processed data and metadata"""
    # Create directories if they don't exist
    os.makedirs(DATA_PROCESSED_PATH, exist_ok=True)
    os.makedirs(OUTPUTS_PATH, exist_ok=True)
    
    # Save CSV files
    final_df.to_csv(os.path.join(OUTPUTS_PATH, f'{prefix}mental_health_oecd_integrated.csv'), index=False)
    df_oecd.to_csv(os.path.join(DATA_PROCESSED_PATH, f'{prefix}cleaned_oecd_data.csv'), index=False)
    df_2014.to_csv(os.path.join(DATA_PROCESSED_PATH, f'{prefix}cleaned_survey_2014.csv'), index=False)
    df_2016.to_csv(os.path.join(DATA_PROCESSED_PATH, f'{prefix}cleaned_survey_2016.csv'), index=False)

    # Save metadata
    metadata = {
        'created_date': pd.Timestamp.now().isoformat(),
        'data_sources': [
            'OECD 2024',
            'Mental Health Survey 2014',
            'Mental Health Survey 2016'
        ],
        'processing_steps': [
            'Column standardization',
            'Missing value imputation',
            'Data type conversion',
            'Feature engineering',
            'Country-level aggregation'
        ],
        'validation_results': validation_results
    }

    with open(os.path.join(OUTPUTS_PATH, f'{prefix}metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=4)

    print(f"Data and metadata saved to: {OUTPUTS_PATH}")

# Main ETL Pipeline
def run_etl():
    """
    Execute the complete ETL pipeline:
    1. Load raw data
    2. Clean and transform each dataset
    3. Integrate data
    4. Validate data quality
    5. Save results
    """
    print("=== Starting ETL Pipeline ===")

    # Step 1: Data Loading
    print("Loading datasets...")
    df_oecd, df_2014, df_2016 = load_datasets()

    # Step 2: Data Cleaning
    print("Cleaning OECD data...")
    df_oecd = clean_oecd(df_oecd)

    print("Cleaning 2014 survey data...")
    df_2014 = clean_survey_2014(df_2014)

    print("Cleaning 2016 survey data...")
    df_2016 = clean_survey_2016(df_2016)

    # Step 3: Data Transformation
    print("Transforming OECD data...")
    oecd_pivot = transform_oecd(df_oecd)

    print("Transforming survey data...")
    df_2014, df_2016 = transform_surveys(df_2014, df_2016)

    # Step 4: Data Integration
    print("Merging datasets...")
    final_df = merge_datasets(oecd_pivot, df_2014, df_2016)

    # Additional cleaning
    final_df = clean_data(final_df)

    # Step 5: Data Validation
    print("Validating data quality...")
    validation_results = validate_data(final_df)

    # Step 6: Save Results
    print("Saving results...")
    save_outputs(
        final_df,
        df_oecd,
        df_2014,
        df_2016,
        validation_results,
        prefix='final_'
    )

    print("=== ETL Pipeline completed successfully ===")
    return final_df, validation_results

if __name__ == "__main__":
    final_data, validation = run_etl()

    # Display results
    print("\nFinal data preview:")
    print(final_data.head())

    print("\nValidation results:")
    for check, result in validation.items():
        print(f"{check}: {result}")
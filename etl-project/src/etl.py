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


def load_google_form_survey():
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR3vkqIO5V9IO3ap6X7RSPVScbBp8J02ZnOKRu3vnrvQOha_9pKEJ7_bUilHiB3hgrJ1UWUZGZNR_CS/pub?gid=1966309919&single=true&output=csv"
    print("Loading survey responses from Google Sheets CSV URL...")
    df_survey = pd.read_csv(csv_url)
    return df_survey

# Step 1: Data Loading Functions
def load_datasets():
    """Load raw datasets from data/raw directory"""
    df_survey=load_google_form_survey()
    df_2014 = pd.read_csv(os.path.join(DATA_RAW_PATH, 'survey_2014.csv'))
    df_2016 = pd.read_csv(os.path.join(DATA_RAW_PATH, 'survey_2016.csv'))
    return df_survey, df_2014, df_2016

# Step 2: Data Cleaning Functions

def clean_survey_2014(df_2014):
    """Clean 2014 mental health survey data"""
    
    # Standardize column names
    df_2014.columns = df_2014.columns.str.lower()

    # Handle missing values
    df_2014['state'].fillna('Unknown', inplace=True)
    df_2014['self_employed'].fillna('Unknown', inplace=True)
    df_2014['work_interfere'].fillna('Unknown', inplace=True)
    df_2014['comments'].fillna('No comments', inplace=True)

    # Convert timestamp to datetime
    df_2014['timestamp'] = pd.to_datetime(df_2014['timestamp'])

    # Clean age column (filter outliers and replace with median)
    df_2014['age'] = df_2014['age'].apply(lambda x: x if 18 <= x <= 100 else np.nan)
    df_2014['age'].fillna(df_2014['age'].median(), inplace=True)

    # Clean gender column with internal function
    def clean_gender(gender):
        gender = str(gender).strip().lower()

        male_keywords = ['trans male', 'trans man', 'male', 'm', 'cis male', 'man', 'male (cis)', 'malr', 'cis man', 'make', 'mail']
        female_keywords = ['trans woman', 'female (trans)', 'cis female', 'trans-female', 'female', 'f', 'woman', 'female (cis)', 'cis woman']

        if any(keyword in gender for keyword in male_keywords):
            return 'male'
        elif any(keyword in gender for keyword in female_keywords):
            return 'female'
        else:
            return 'other'

    df_2014['gender'] = df_2014['gender'].apply(clean_gender)

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
def clean_survey_2025(df_survey):
    """Clean 2025 mental health survey data to align with 2014 schema"""
    
    # Create copy to avoid SettingWithCopyWarning
    df_2025 = df_survey.copy()

    # First normalize all column names to lowercase for consistent handling
    df_2025.columns = [col.strip().lower() for col in df_2025.columns]
    
    # Rename mapping with lowercase keys to match normalized columns
    rename_map = {
        'horodateur': 'timestamp',
        'age': 'age',
        'gender': 'gender',
        'country': 'country',
        'are you self-employed?': 'self_employed',
        'do you have a family history of mental illness?': 'family_history',
        'have you sought treatment for a mental health condition?': 'treatment',
        'if you have a mental health condition, do you feel that it interferes with your work?': 'work_interfere',
        'do you work remotely (outside of an office) at least 50% of the time?': 'remote_work',
        'is your employer primarily a tech company/organization?': 'tech_company',
        'does your employer provide mental health benefits?': 'benefits',
        'do you know the options for mental health care your employer provides?': 'care_options',
        'has your employer ever discussed mental health as part of an employee wellness program?': 'wellness_program',
        'does your employer provide resources to learn more about mental health issues and how to seek help?': 'seek_help',
        'is your anonymity protected if you choose to take advantage of mental health or substance abuse treatment resources?': 'anonymity',
        'how easy is it for you to take medical leave for a mental health condition?': 'leave',
        'do you think that discussing a mental health issue with your employer would have negative consequences?': 'mental_health_consequence',
        'do you think that discussing a physical health issue with your employer would have negative consequences?': 'phys_health_consequence',
        'would you be willing to discuss a mental health issue with your coworkers?': 'coworkers',
        'would you be willing to discuss a mental health issue with your supervisors?': 'supervisor',
        'would you bring up a mental health issue with a potential employer in an interview?': 'mental_health_interview',
        'would you bring up a physical health issue with a potential employer in an interview?': 'phys_health_interview',
        'do you feel that your employer takes mental health as seriously as physical health?': 'mental_vs_physical',
        'have you heard of or observed negative consequences for coworkers with mental health conditions in your workplace?': 'obs_consequence',
        'any additional notes or comments?': 'comments'
    }

    # Apply renaming
    df_2025 = df_2025.rename(columns=rename_map)

    # Convert timestamp
    if 'timestamp' in df_2025.columns:
        df_2025['timestamp'] = pd.to_datetime(df_2025['timestamp'], errors='coerce', dayfirst=True)

    # Clean age
    if 'age' in df_2025.columns:
        df_2025['age'] = pd.to_numeric(df_2025['age'], errors='coerce')
        df_2025['age'] = df_2025['age'].apply(lambda x: x if 18 <= x <= 100 else np.nan)
        df_2025['age'] = df_2025['age'].fillna(df_2025['age'].median())
    
    # Clean gender
    if 'gender' in df_2025.columns:
        def clean_gender(g):
            if pd.isna(g):
                return 'other'
                
            g = str(g).strip().lower()
            male_keywords = ['male', 'm', 'man', 'cis male', 'trans male', 
                            'trans man', 'male (cis)', 'cis man', 'make', 'mail', 'malr']
            female_keywords = ['female', 'f', 'woman', 'cis female', 'trans female', 
                             'trans woman', 'female (cis)', 'cis woman', 'female (trans)']

            if any(k in g for k in male_keywords):
                return 'male'
            elif any(k in g for k in female_keywords):
                return 'female'
            return 'other'

        df_2025['gender'] = df_2025['gender'].apply(clean_gender)
    else:
        print("Warning: No gender column found after normalization and renaming")
        print("Available columns:", df_2025.columns.tolist())

    return df_2025

# Step 3: Data Transformation Functions
def transform_surveys(df_2014, df_2016, df_2025):
    """Transform and align survey data from 2014, 2016, and 2025"""

    # --- Standardize Country Names ---
    country_mapping = {
        'United States': 'USA',
        'United States of America': 'USA',
        'US': 'USA',
        'UK': 'UK',
        'United Kingdom': 'UK',
        'CA': 'Canada',
        'DE': 'Germany'
    }

    df_2014['country'] = df_2014['country'].replace(country_mapping)
    df_2016['what_country_do_you_live_in'] = df_2016['what_country_do_you_live_in'].replace(country_mapping)
    df_2025['country'] = df_2025['country'].replace(country_mapping)

    # --- Standardize Age Columns ---
    df_2016 = df_2016.rename(columns={'what_is_your_age': 'age'})

    # --- Standardize Gender Columns ---
    gender_mapping = {
        'female': 'Female',
        'male': 'Male',
        'f': 'Female',
        'm': 'Male',
        'woman': 'Female',
        'man': 'Male',
        'cis female': 'Female',
        'cis male': 'Male',
        'trans female': 'Other',
        'trans male': 'Other'
    }

    df_2014['gender'] = df_2014['gender'].replace(gender_mapping, regex=True).fillna('Other')
    df_2016['what_is_your_gender'] = df_2016['what_is_your_gender'].replace(gender_mapping, regex=True).fillna('Other')
    df_2025['gender'] = df_2025['gender'].replace(gender_mapping, regex=True).fillna('Other')

    # --- Map work_interfere to numeric scale (2014 and 2025 only) ---
    interfere_map = {
        'Never': 0,
        'Rarely': 1,
        'Sometimes': 2,
        'Often': 3,
        'Unknown': 1
    }

    df_2014['mh_impact_score'] = df_2014['work_interfere'].map(interfere_map)
    df_2025['mh_impact_score'] = df_2025['work_interfere'].map(interfere_map)

    # --- Create has_benefits flag for 2016 survey ---
    df_2016['has_benefits'] = df_2016[
        'does_your_employer_provide_mental_health_benefits_as_part_of_healthcare_coverage'
    ].map({
        'Yes': 1,
        'No': 0,
        'I don\'t know': 0,
        'Not eligible for coverage / N/A': 0
    })

    # --- Harmonize column names (optional, if you plan to concatenate) ---
    df_2016.rename(columns={
        'what_is_your_gender': 'gender',
        'what_country_do_you_live_in': 'country'
    }, inplace=True)
    """Normalize all column names in the 2016 survey to lowercase with underscores"""
    
    # Create a comprehensive mapping for all 2016 columns
    column_mapping = {
        'Are you self-employed?': 'self_employed',
        'How many employees does your company or organization have?': 'no_employees',
        'Is your employer primarily a tech company/organization?': 'tech_company',
        'Is your primary role within your company related to tech/IT?': 'tech_role',
        'Does your employer provide mental health benefits as part of healthcare coverage?': 'benefits',
        'Do you know the options for mental health care available under your employer-provided coverage?': 'care_options',
        'Has your employer ever formally discussed mental health (for example, as part of a wellness campaign or other official communication)?': 'wellness_program',
        'Does your employer offer resources to learn more about mental health concerns and options for seeking help?': 'seek_help',
        'Is your anonymity protected if you choose to take advantage of mental health or substance abuse treatment resources provided by your employer?': 'anonymity',
        'If a mental health issue prompted you to request a medical leave from work, asking for that leave would be:': 'leave',
        'Do you think that discussing a mental health disorder with your employer would have negative consequences?': 'mental_health_consequence',
        'Do you think that discussing a physical health issue with your employer would have negative consequences?': 'phys_health_consequence',
        'Would you feel comfortable discussing a mental health disorder with your coworkers?': 'coworkers',
        'Would you feel comfortable discussing a mental health disorder with your direct supervisor(s)?': 'supervisor',
        'Do you feel that your employer takes mental health as seriously as physical health?': 'mental_vs_physical',
        'Have you heard of or observed negative consequences for co-workers who have been open about mental health issues in your workplace?': 'obs_consequence',
        'Do you have medical coverage (private insurance or state-provided) which includes treatment of mental health issues?': 'medical_coverage',
        'Do you know local or online resources to seek help for a mental health disorder?': 'know_resources',
        'If you have been diagnosed or treated for a mental health disorder, do you ever reveal this to clients or business contacts?': 'reveal_to_clients',
        'If you have revealed a mental health issue to a client or business contact, do you believe this has impacted you negatively?': 'client_impact',
        'If you have been diagnosed or treated for a mental health disorder, do you ever reveal this to coworkers or employees?': 'reveal_to_coworkers',
        'If you have revealed a mental health issue to a coworker or employee, do you believe this has impacted you negatively?': 'coworker_impact',
        'Do you believe your productivity is ever affected by a mental health issue?': 'productivity_affected',
        'If yes, what percentage of your work time (time performing primary or secondary job functions) is affected by a mental health issue?': 'productivity_percentage',
        'Do you have previous employers?': 'previous_employers',
        'Have your previous employers provided mental health benefits?': 'prev_benefits',
        'Were you aware of the options for mental health care provided by your previous employers?': 'prev_care_options',
        'Did your previous employers ever formally discuss mental health (as part of a wellness campaign or other official communication)?': 'prev_wellness_program',
        'Did your previous employers provide resources to learn more about mental health issues and how to seek help?': 'prev_seek_help',
        'Was your anonymity protected if you chose to take advantage of mental health or substance abuse treatment resources with previous employers?': 'prev_anonymity',
        'Do you think that discussing a mental health disorder with previous employers would have negative consequences?': 'prev_mental_health_consequence',
        'Do you think that discussing a physical health issue with previous employers would have negative consequences?': 'prev_phys_health_consequence',
        'Would you have been willing to discuss a mental health issue with your previous co-workers?': 'prev_coworkers',
        'Would you have been willing to discuss a mental health issue with your direct supervisor(s)?': 'prev_supervisor',
        'Did you feel that your previous employers took mental health as seriously as physical health?': 'prev_mental_vs_physical',
        'Did you hear of or observe negative consequences for co-workers with mental health issues in your previous workplaces?': 'prev_obs_consequence',
        'Would you be willing to bring up a physical health issue with a potential employer in an interview?': 'phys_health_interview',
        'Why or why not?': 'phys_health_interview_why',
        'Would you bring up a mental health issue with a potential employer in an interview?': 'mental_health_interview',
        'Why or why not?': 'mental_health_interview_why',
        'Do you feel that being identified as a person with a mental health issue would hurt your career?': 'career_impact',
        'Do you think that team members/co-workers would view you more negatively if they knew you suffered from a mental health issue?': 'coworker_perception',
        'How willing would you be to share with friends and family that you have a mental illness?': 'share_with_family',
        'Have you observed or experienced an unsupportive or badly handled response to a mental health issue in your current or previous workplace?': 'bad_response_experience',
        'Have your observations of how another individual who discussed a mental health disorder made you less likely to reveal a mental health issue yourself in your current workplace?': 'observation_impact',
        'Do you have a family history of mental illness?': 'family_history',
        'Have you had a mental health disorder in the past?': 'past_disorder',
        'Do you currently have a mental health disorder?': 'current_disorder',
        'If yes, what condition(s) have you been diagnosed with?': 'diagnosed_condition',
        'If maybe, what condition(s) do you believe you have?': 'suspected_condition',
        'Have you been diagnosed with a mental health condition by a medical professional?': 'professional_diagnosis',
        'If so, what condition(s) were you diagnosed with?': 'professional_diagnosis_details',
        'Have you ever sought treatment for a mental health issue from a mental health professional?': 'treatment',
        'If you have a mental health issue, do you feel that it interferes with your work when being treated effectively?': 'treated_interference',
        'If you have a mental health issue, do you feel that it interferes with your work when NOT being treated effectively?': 'untreated_interference',
        'What is your age?': 'age',
        'What is your gender?': 'gender',
        'What country do you live in?': 'country',
        'What US state or territory do you live in?': 'state',
        'What country do you work in?': 'work_country',
        'What US state or territory do you work in?': 'work_state',
        'Which of the following best describes your work position?': 'position',
        'Do you work remotely?': 'remote_work'
    }
    
    # Apply the column name normalization
    df_2016 = df_2016.rename(columns=column_mapping)

    return df_2014, df_2016, df_2025

# Step 4: Data Integration Function
def merge_all_surveys(df_2014, df_2016, df_2025):
    """
    Merge all three survey datasets while keeping all columns from each survey.
    Non-matching columns will be filled with NaN values.
    
    Args:
        df_2014: 2014 survey DataFrame (reference schema)
        df_2016: 2016 survey DataFrame
        df_2025: 2025 survey DataFrame
        
    Returns:
        Merged DataFrame with all columns preserved
    """
    
    # Create mapping dictionaries for column alignment
    map_2016_to_2014 = {
        'what_is_your_age': 'age',
        'what_is_your_gender': 'gender',
        'what_country_do_you_live_in': 'country',
        'are_you_self_employed': 'self_employed',
        'do_you_have_a_family_history_of_mental_illness': 'family_history',
        'have_you_ever_sought_treatment_for_a_mental_health_issue_from_a_mental_health_professional': 'treatment',
        'if_you_have_a_mental_health_issue_do_you_feel_that_it_interferes_with_your_work_when_being_treated_effectively': 'work_interfere',
        'how_many_employees_does_your_company_or_organization_have': 'no_employees',
        'do_you_work_remotely': 'remote_work',
        'is_your_employer_primarily_a_tech_company_organization': 'tech_company',
        'does_your_employer_provide_mental_health_benefits_as_part_of_healthcare_coverage': 'benefits',
        'do_you_know_the_options_for_mental_health_care_available_under_your_employer_provided_coverage': 'care_options',
        'has_your_employer_ever_formally_discussed_mental_health_for_example_as_part_of_a_wellness_campaign_or_other_official_communication': 'wellness_program',
        'does_your_employer_offer_resources_to_learn_more_about_mental_health_concerns_and_options_for_seeking_help': 'seek_help',
        'is_your_anonymity_protected_if_you_choose_to_take_advantage_of_mental_health_or_substance_abuse_treatment_resources_provided_by_your_employer': 'anonymity',
        'if_a_mental_health_issue_prompted_you_to_request_a_medical_leave_from_work_asking_for_that_leave_would_be': 'leave',
        'do_you_think_that_discussing_a_mental_health_disorder_with_your_employer_would_have_negative_consequences': 'mental_health_consequence',
        'do_you_think_that_discussing_a_physical_health_issue_with_your_employer_would_have_negative_consequences': 'phys_health_consequence',
        'would_you_feel_comfortable_discussing_a_mental_health_disorder_with_your_coworkers': 'coworkers',
        'would_you_feel_comfortable_discussing_a_mental_health_disorder_with_your_direct_supervisor_s': 'supervisor',
        'would_you_bring_up_a_mental_health_issue_with_a_potential_employer_in_an_interview': 'mental_health_interview',
        'would_you_be_willing_to_bring_up_a_physical_health_issue_with_a_potential_employer_in_an_interview': 'phys_health_interview',
        'do_you_feel_that_your_employer_takes_mental_health_as_seriously_as_physical_health': 'mental_vs_physical',
        'have_you_heard_of_or_observed_negative_consequences_for_co_workers_who_have_been_open_about_mental_health_issues_in_your_workplace': 'obs_consequence'
    }

    # Reverse mapping to go from 2014 names to 2016 names
    map_2014_to_2016 = {v: k for k, v in map_2016_to_2014.items()}

    # Add year identifiers
    df_2014['survey_year'] = 2014
    df_2016['survey_year'] = 2016
    df_2025['survey_year'] = 2025

    # Get all unique columns from all surveys
    all_columns = set(df_2014.columns) | set(df_2016.columns) | set(df_2025.columns)
    
    # Create DataFrames with all possible columns for each survey
    def expand_df(df, all_cols):
        missing_cols = [col for col in all_cols if col not in df.columns]
        for col in missing_cols:
            df[col] = np.nan
        return df

    # Expand each DataFrame to include all columns
    df_2014_expanded = expand_df(df_2014, all_columns)
    df_2016_expanded = expand_df(df_2016, all_columns)
    df_2025_expanded = expand_df(df_2025, all_columns)

    # Concatenate all surveys
    merged_df = pd.concat(
        [df_2014_expanded, df_2016_expanded, df_2025_expanded],
        axis=0,
        ignore_index=True
    )

    return merged_df
'''# Step 5: Data Quality Validation
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
'''
# Step 6: Save Outputs
def save_outputs(final_df, df_2025, df_2014, df_2016, prefix=''):
    """Save processed data and metadata"""
    # Create directories if they don't exist
    os.makedirs(DATA_PROCESSED_PATH, exist_ok=True)
    os.makedirs(OUTPUTS_PATH, exist_ok=True)
    
    # Save CSV files
    final_df.to_csv(os.path.join(OUTPUTS_PATH, f'{prefix}integrated.csv'), index=False)
    df_2025.to_csv(os.path.join(DATA_PROCESSED_PATH, f'{prefix}cleaned_survey_2025.csv'), index=False)
    df_2014.to_csv(os.path.join(DATA_PROCESSED_PATH, f'{prefix}cleaned_survey_2014.csv'), index=False)
    df_2016.to_csv(os.path.join(DATA_PROCESSED_PATH, f'{prefix}cleaned_survey_2016.csv'), index=False)

    # Save metadata
    metadata = {
        'created_date': pd.Timestamp.now().isoformat(),
        'data_sources': [
            'Mental Health Survey 2025',
            'Mental Health Survey 2014',
            'Mental Health Survey 2016'
        ],
        'processing_steps': [
            'Column standardization',
            'Missing value imputation',
            'Data type conversion',
            'Feature engineering',
            'Country-level aggregation'
        ]    }

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
    df_survey, df_2014, df_2016 = load_datasets()

    # Step 2: Data Cleaning
    print("Cleaning 2025 survey data...")
    df_2025 = clean_survey_2025(df_survey)

    print("Cleaning 2014 survey data...")
    df_2014 = clean_survey_2014(df_2014)

    print("Cleaning 2016 survey data...")
    df_2016 = clean_survey_2016(df_2016)

    # Step 3: Data Transformation

    print("Transforming survey data...")
    df_2014, df_2016, df_2025 = transform_surveys(df_2014, df_2016, df_2025)

    # Step 4: Data Integration
    print("Merging datasets...")
    final_df = merge_all_surveys(df_2014, df_2016, df_2025)

    '''# Additional cleaning
    final_df = clean_data(final_df)

    # Step 5: Data Validation
    print("Validating data quality...")
    validation_results = validate_data(final_df)
'''
    # Step 6: Save Results
    print("Saving results...")
    save_outputs(
        final_df,
        df_2025,
        df_2014,
        df_2016,
        prefix='final_'
    )

    print("=== ETL Pipeline completed successfully ===")
    return final_df
if __name__ == "__main__":
    final_data = run_etl()

    # Display results
    print("\nFinal data preview:")
    print(final_data.head())
'''
    print("\nValidation results:")
    for check, result in validation.items():
        print(f"{check}: {result}")'''
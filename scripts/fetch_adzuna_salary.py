import os
import requests
import pandas as pd
import numpy as np
import time
from dotenv import load_dotenv
from scipy import stats

# Load API keys from .env
load_dotenv()
APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

# Constants
MIN_REASONABLE_SALARY = 30000
MAX_REASONABLE_SALARY = 500000
INVALID_VALUES = {175, 200, 250, 300}
COMPANY_SCALE_FACTOR = 0.607

SALARY_BENCHMARKS = {
    "Finance": {
        "Associate": (65000, 95000, 130000, 25000),
        "Manager": (140000, 175000, 220000, 35000),
        "Executive": (180000, 240000, 350000, 60000)
    },
    "Marketing": {
        "Associate": (55000, 75000, 100000, 20000),
        "Manager": (100000, 135000, 180000, 30000),
        "Executive": (150000, 200000, 280000, 50000)
    },
    "Operations": {
        "Associate": (60000, 85000, 120000, 25000),
        "Manager": (120000, 160000, 210000, 35000),
        "Executive": (170000, 230000, 320000, 55000)
    },
    "Sales": {
        "Associate": (50000, 70000, 95000, 18000),
        "Manager": (110000, 145000, 190000, 32000),
        "Executive": (160000, 210000, 300000, 50000)
    },
    "Human Resources": {
        "Associate": (55000, 75000, 105000, 22000),
        "Manager": (100000, 130000, 170000, 30000),
        "Executive": (150000, 195000, 280000, 48000)
    }
}

def is_valid_salary(salary):
    if salary in INVALID_VALUES:
        return False
    return MIN_REASONABLE_SALARY <= salary <= MAX_REASONABLE_SALARY

def remove_statistical_outliers(salaries, method='iqr', factor=2.5):
    if len(salaries) < 5:
        return salaries
    salaries_array = np.array(salaries)
    if method == 'iqr':
        Q1 = np.percentile(salaries_array, 25)
        Q3 = np.percentile(salaries_array, 75)
        IQR = Q3 - Q1
        lower = Q1 - factor * IQR
        upper = Q3 + factor * IQR
        return [s for s in salaries if lower <= s <= upper]
    elif method == 'zscore':
        z_scores = np.abs(stats.zscore(salaries_array))
        return [s for i, s in enumerate(salaries) if z_scores[i] < factor]
    return salaries

def generate_synthetic_salaries(dept, role, target_count=50):
    if dept not in SALARY_BENCHMARKS or role not in SALARY_BENCHMARKS[dept]:
        base_salary = 75000
        multiplier = {"Associate": 1.0, "Manager": 1.8, "Executive": 2.5}.get(role, 1.0)
        median = int(base_salary * multiplier)
        std_dev = int(median * 0.3)
        min_sal, max_sal = int(median * 0.7), int(median * 1.6)
    else:
        min_sal, median, max_sal, std_dev = SALARY_BENCHMARKS[dept][role]
    mu = np.log(median)
    sigma = std_dev / median
    synthetic = []
    for _ in range(target_count):
        salary = int(np.random.lognormal(mu, sigma))
        synthetic.append(max(min_sal, min(salary, max_sal)))
    return synthetic

def fetch_salary_data(dept, role, max_pages=5):
    query = f"{dept} {role}"
    print(f"🔍 Fetching: {query}")
    salaries = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for page in range(1, max_pages + 1):
        url = f"https://api.adzuna.com/v1/api/jobs/au/search/{page}"
        params = {
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "what": query,
            "where": "Australia",
            "results_per_page": 50,
            "content-type": "application/json",
            "sort_by": "salary"
        }
        try:
            res = requests.get(url, params=params, headers=headers, timeout=10)
            if res.status_code != 200:
                print(f"❌ Error {res.status_code} on page {page}")
                if res.status_code == 429:
                    time.sleep(5)
                continue
            for job in res.json().get("results", []):
                loc = job.get("location", {}).get("display_name", "").lower()
                if not any(x in loc for x in ["australia", "nsw", "vic", "qld", "wa", "sa", "act", "nt", "tas"]):
                    continue
                sal_min = job.get("salary_min")
                sal_max = job.get("salary_max")
                if sal_min and sal_max:
                    avg = (sal_min + sal_max) / 2
                    if is_valid_salary(avg):
                        salaries.append(avg)
                elif sal_min and is_valid_salary(sal_min):
                    salaries.append(sal_min)
                elif sal_max and is_valid_salary(sal_max):
                    salaries.append(sal_max)
            time.sleep(1.5)
        except Exception as e:
            print(f"❌ Exception: {e}")
            continue
    if len(salaries) >= 5:
        salaries = remove_statistical_outliers(salaries, 'iqr', 2.0)
    print(f"✅ Found {len(salaries)} valid salaries")
    return salaries

def calculate_salary_stats(salaries, dept, role, min_required=30):
    original = len(salaries)
    if original < min_required:
        synth_needed = min_required - original
        print(f"   📊 Generating {synth_needed} synthetic salaries")
        synthetic = generate_synthetic_salaries(dept, role, synth_needed)
        if original > 0:
            factor = np.median(salaries) / np.median(synthetic)
            synthetic = [int(s * factor) for s in synthetic]
        salaries.extend(synthetic)
    return {
        "Department": dept,
        "Role": role,
        "Count": len(salaries),
        "Real_Data_Count": original,
        "Synthetic_Data_Count": len(salaries) - original,
        "Min_Salary": int(np.min(salaries)),
        "P10": int(np.percentile(salaries, 10)),
        "P25": int(np.percentile(salaries, 25)),
        "Median": int(np.median(salaries)),
        "P75": int(np.percentile(salaries, 75)),
        "P90": int(np.percentile(salaries, 90)),
        "Max_Salary": int(np.max(salaries)),
        "Mean": int(np.mean(salaries)),
        "Std_Dev": int(np.std(salaries)),
    }

roles = [
    ("Finance", "Associate"), ("Marketing", "Associate"),
    ("Operations", "Executive"), ("Human Resources", "Associate"),
    ("Operations", "Associate"), ("Finance", "Manager"),
    ("Operations", "Manager"), ("Finance", "Executive"),
    ("Marketing", "Executive"), ("Marketing", "Manager"),
    ("Sales", "Executive"), ("Human Resources", "Manager"),
    ("Sales", "Associate"), ("Sales", "Manager"),
    ("Human Resources", "Executive")
]

results = []
for dept, role in roles:
    salaries = fetch_salary_data(dept, role, max_pages=4)
    stats = calculate_salary_stats(salaries, dept, role)
    results.append(stats)

df = pd.DataFrame(results)
df.to_csv("australian_salary_data_complete.csv", index=False)

# Prepare Tableau columns
tableau_df = df.copy()
for col in ["Min_Salary", "P25", "Median", "P75", "Max_Salary", "Mean"]:
    tableau_df[f"Company_Scaled_{col.split('_')[0]}"] = (tableau_df[col] * COMPANY_SCALE_FACTOR).astype(int)

# Adjustment rules
adjustments = [
    ("Associate", "Finance", "Reduce", (4, 8)),
    ("Associate", "Human Resources", "Reduce", (4, 8)),
    ("Associate", "Marketing", "Increase", (3, 8)),
    ("Associate", "Operations", "Reduce", (4, 8)),
    ("Associate", "Sales", "Increase", (3, 8)),
    ("Executive", "Finance", "Increase", (3, 8)),
    ("Executive", "Human Resources", "Increase", (3, 8)),
    ("Executive", "Marketing", "Increase", (3, 8)),
    ("Executive", "Operations", "Increase", (3, 8)),
    ("Executive", "Sales", "Increase", (3, 8)),
    ("Manager", "Finance", "Reduce", (4, 8)),
    ("Manager", "Human Resources", "Increase", (3, 8)),
    ("Manager", "Marketing", "Increase", (3, 8)),
    ("Manager", "Operations", "Reduce", (4, 8)),
    ("Manager", "Sales", "Reduce", (4, 8)),
]

adjust_cols = [
    "Company_Scaled_Min", "Company_Scaled_P25", "Company_Scaled_Median",
    "Company_Scaled_P75", "Company_Scaled_Max", "Company_Scaled_Mean"
]

# Apply the adjustment to all key columns
for role, dept, direction, (low, high) in adjustments:
    idx = (tableau_df['Role'] == role) & (tableau_df['Department'] == dept)
    if idx.any():
        for col in adjust_cols:
            base = tableau_df.loc[idx, col]
            pct = np.random.uniform(low, high)
            if direction == "Reduce":
                adjusted = (base * (1 - pct / 100)).astype(int)
            else:
                adjusted = (base * (1 + pct / 100)).astype(int)
            tableau_df.loc[idx, col] = adjusted

# Save final CSV
tableau_df.to_csv("australian_salary_tableau_ready.csv", index=False)
print("✅ Exported with full adjustments: australian_salary_tableau_ready.csv")

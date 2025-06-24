import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv
import os

# 1. CONFIGURATION
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

# 2. CREATE CONNECTION ENGINE
print("🔌 Connecting to database...")
engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        print("✅ Connected to PostgreSQL:", result.fetchone()[0])
except OperationalError as e:
    print("❌ Failed to connect to database.")
    print(e)
    exit(1)

# 3. LOAD CSV DATA
print("📂 Loading data from CSVs...")
employees_df = pd.read_csv('notebooks/cleaned_employees.csv')
performance_df = pd.read_csv('data/performance_metrics.csv')
salary_df = pd.read_csv('australian_salary_tableau_ready.csv')

# 4. PREVIEW SHAPES
print(f"👥 Employees: {employees_df.shape}")
print(f"📈 Performance: {performance_df.shape}")
print(f"💰 Salary Reference: {salary_df.shape}")

# 5. UPLOAD TO DATABASE
print("📤 Uploading data to PostgreSQL...")
employees_df.to_sql('employees', engine, if_exists='replace', index=False)
performance_df.to_sql('performance_metrics', engine, if_exists='replace', index=False)
salary_df.to_sql('australian_salary_reference', engine, if_exists='replace', index=False)

print("✅ All datasets uploaded successfully to AWS RDS PostgreSQL.")

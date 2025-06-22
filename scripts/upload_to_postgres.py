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
print("Connecting to database...")
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

# 4. PREVIEW SHAPES
print(f"👥 Employees rows: {employees_df.shape[0]}, columns: {employees_df.shape[1]}")
print(f"📈 Performance rows: {performance_df.shape[0]}, columns: {performance_df.shape[1]}")

# 5. UPLOAD TO DATABASE
print("📤 Uploading data to PostgreSQL...")
employees_df.to_sql('employees', engine, if_exists='replace', index=False)
performance_df.to_sql('performance_metrics', engine, if_exists='replace', index=False)

print("✅ Data uploaded successfully to AWS RDS PostgreSQL.")
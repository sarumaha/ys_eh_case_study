-- Fetch top 10 highest paid employees along with their performance data
-- Filters out deleted records using IsDeleted
-- Make sure only one performance record per employee (highest score retained if duplicates)
-- Sorts by salary in descending order

WITH cleaned_performance AS (
    -- 📌 Select the best (non-deleted) performance record per employee
    SELECT DISTINCT ON ("EmployeeID") *
    FROM public.performance_metrics
    WHERE COALESCE("IsDeleted", FALSE) = FALSE
    ORDER BY "EmployeeID", "PerformanceScore" DESC
)

SELECT 
    e."EmployeeID",
    e."DepartmentName",
    e."RoleName",
    e."AnnualSalary",
    e."HireDate",
    p."SatisfactionRating",
    p."PerformanceScore"

FROM public.employees e

-- Join with cleaned performance data
JOIN cleaned_performance p 
    ON e."EmployeeID" = p."EmployeeID"

-- Filter out invalid or missing salaries
WHERE e."AnnualSalary" IS NOT NULL

-- Sort by highest salary first
ORDER BY e."AnnualSalary" DESC

-- Limit to top 10 results
LIMIT 10;











--  Goal: Show average and median salaries for each unique role
SELECT 
    "RoleName",
    
    -- Calculate average salary
    ROUND(AVG("AnnualSalary")::numeric, 2) AS avg_salary,
    
    -- Use percentile_cont to get median (50th percentile)
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY "AnnualSalary") AS median_salary

FROM public.employees

-- Group results by role
GROUP BY "RoleName"

-- Sort alphabetically for easy viewing
ORDER BY "RoleName";


SELECT DISTINCT e."DepartmentName" || '-' || e."RoleName" AS dept_role
FROM public.employees e;


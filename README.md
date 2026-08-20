# Python Coursework Solutions

This repository contains the prepared Python solutions and beginner-friendly explanations from the coursework tasks.

## Contents

| Directory | Contents |
|---|---|
| `solutions/pharmacy_reconciliation/` | Two detailed explanations of pharmacy and SBIS CSV reconciliation scripts |
| `solutions/student_debt/` | Pure Python solution for calculating student debts from Google Sheets data |
| `solutions/activity_metrics/` | Pure Python solution for retention, rolling retention, lifetime, churn, MAU, WAU, and DAU |

The repository is private and contains no credentials or downloaded source datasets.

## Running the activity metrics solution

Place `registrations.csv` and `entries.csv` next to the script and run:

```bash
python3 solutions/activity_metrics/activity_metrics_solution.py
```

## Student debt solution

Import the function and pass it the three lists obtained from Google Sheets:

```python
from solutions.student_debt.student_debt_solution import generate_report

generate_report(sheet1_data, sheet2_data, sheet3_data)
```

The report is saved as `student_debt_report.txt`.

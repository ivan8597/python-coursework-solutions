from datetime import date, timedelta


REFERENCE_DATE = date(2021, 12, 31)
JANUARY_COHORT_MONTH = 1
RETENTION_DAY = 15
ROLLING_RETENTION_DAY = 30
CHURN_DAY = 29


def read_semicolon_csv(filename):
    """Read a two-column semicolon-separated CSV without pandas."""
    rows = []
    with open(filename, encoding="utf-8") as file:
        headers = file.readline().strip().split(";")
        for line in file:
            values = line.strip().split(";")
            rows.append(dict(zip(headers, values)))
    return rows


def to_date(value):
    return date.fromisoformat(value.strip())


def monday_of_week(day):
    """Return the Monday belonging to the calendar week of day."""
    return day - timedelta(days=day.weekday())


registrations = read_semicolon_csv("registrations.csv")
entries = read_semicolon_csv("entries.csv")

registration_date = {
    int(row["user_id"]): to_date(row["registration_date"])
    for row in registrations
}

# Deduplicate repeated entries made by one user on one calendar day.
activity = {}
for row in entries:
    user_id = int(row["user_id"])
    entry_day = to_date(row["entry_date"])
    activity.setdefault(user_id, set()).add(entry_day)

all_users = set(registration_date)
user_count = len(all_users)

jan_users = {
    user_id
    for user_id, registered_on in registration_date.items()
    if registered_on.year == 2021 and registered_on.month == JANUARY_COHORT_MONTH
}

# Retention means an entry exactly N days after registration.
retention_15_users = sum(
    registration_date[user_id] + timedelta(days=RETENTION_DAY)
    in activity.get(user_id, set())
    for user_id in jan_users
)
retention_15_day = round(100 * retention_15_users / len(jan_users), 5)

# Rolling retention means at least one entry on day N or any later day.
rolling_30_users = sum(
    any(
        entry_day >= registration_date[user_id] + timedelta(days=ROLLING_RETENTION_DAY)
        for entry_day in activity.get(user_id, set())
    )
    for user_id in jan_users
)
rolling_retention = round(100 * rolling_30_users / len(jan_users), 5)

# The last observed user lifetime in the data determines the integration range.
max_lifetime_day = max(
    (max(activity[user_id]) - registration_date[user_id]).days
    for user_id in all_users
    if activity.get(user_id)
)

# n-day retention is calculated over the full population (1000 users),
# as required by the case. The discrete integral is the sum of daily rates.
retention_curve = []
for age in range(max_lifetime_day + 1):
    active_on_age_day = sum(
        registration_date[user_id] + timedelta(days=age)
        in activity.get(user_id, set())
        for user_id in all_users
    )
    retention_curve.append(active_on_age_day / user_count)

lifetime = round(sum(retention_curve), 5)

# Churn on day 29 is the complement of rolling retention on day 29.
rolling_29_users = sum(
    any(
        entry_day >= registration_date[user_id] + timedelta(days=CHURN_DAY)
        for entry_day in activity.get(user_id, set())
    )
    for user_id in all_users
)
churn_29 = round(1 - rolling_29_users / user_count, 5)

# Group active users by calendar day.
users_by_day = {}
for row in entries:
    entry_day = to_date(row["entry_date"])
    users_by_day.setdefault(entry_day, set()).add(int(row["user_id"]))

# December metrics.
december_days = {
    day for day in users_by_day
    if day.year == REFERENCE_DATE.year and day.month == 12
}
dec_mau = len(set().union(*(users_by_day[day] for day in december_days)))

december_week_days = {
    day for day in users_by_day
    if date(2021, 12, 25) <= day <= date(2021, 12, 31)
}
dec_wau = len(set().union(*(users_by_day[day] for day in december_week_days)))

dec_dau = len(users_by_day[REFERENCE_DATE])

# Average MAU: one value for each calendar month with activity.
users_by_month = {}
for day, users in users_by_day.items():
    month = (day.year, day.month)
    users_by_month.setdefault(month, set()).update(users)
avg_mau = round(
    sum(len(users) for users in users_by_month.values()) / len(users_by_month),
    5,
)

# Average WAU: one value for each Monday-Sunday calendar week with activity.
users_by_week = {}
for day, users in users_by_day.items():
    week_start = monday_of_week(day)
    users_by_week.setdefault(week_start, set()).update(users)
avg_wau = round(
    sum(len(users) for users in users_by_week.values()) / len(users_by_week),
    5,
)

# Average DAU: one value for every calendar day with activity.
avg_dau = round(
    sum(len(users) for users in users_by_day.values()) / len(users_by_day),
    5,
)

# Optional display for checking the values.
print("retention_15_day =", retention_15_day)
print("rolling_retention =", rolling_retention)
print("lifetime =", lifetime)
print("churn_29 =", churn_29)
print("dec_mau =", dec_mau)
print("dec_wau =", dec_wau)
print("dec_dau =", dec_dau)
print("avg_mau =", avg_mau)
print("avg_wau =", avg_wau)
print("avg_dau =", avg_dau)

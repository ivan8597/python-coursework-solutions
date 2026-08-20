from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_DOWN


AS_OF_DATE = date(2023, 3, 1)
PAYMENT_PERIOD_DAYS = 183
INSTALLMENT_PERIODS = 6


def _to_number(value):
    """Convert a Google Sheets value to Decimal."""
    if value is None or str(value).strip() == "":
        return Decimal("0")

    text = str(value).strip().replace(" ", "").replace(" ", "")
    text = text.replace(",", ".")

    try:
        return Decimal(text)
    except InvalidOperation as error:
        raise ValueError(f"Не удалось преобразовать число: {value!r}") from error


def _to_date(value):
    """Convert a date from Google Sheets to datetime.date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    text = str(value).strip()
    if not text:
        return None

    formats = (
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%d.%m.%y",
        "%Y/%m/%d",
        "%d/%m/%Y",
    )

    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass

    raise ValueError(f"Не удалось распознать дату: {value!r}")


def _overdue_payments(expected_date, as_of=AS_OF_DATE):
    """Return the number of payments overdue by the reference date."""
    expected_date = _to_date(expected_date)
    if expected_date is None or expected_date > as_of:
        return 0

    days_late = (as_of - expected_date).days
    return days_late // PAYMENT_PERIOD_DAYS + 1


def generate_report(sheet1, sheet2, sheet3):
    """Create student_debt_report.txt from three Google Sheets record lists.

    sheet1: student_id, student_name, installment (Y/N)
    sheet2: student_id, last_payment_date, expected_payment_date
    sheet3: student_id, already_payed_amount, left_to_pay,
            one-time_payment, installment_amount
    """
    payments_by_id = {str(row["student_id"]): row for row in sheet2}
    amounts_by_id = {str(row["student_id"]): row for row in sheet3}

    report_lines = []

    for student in sheet1:
        student_id = str(student["student_id"])
        payment_data = payments_by_id.get(student_id)
        amount_data = amounts_by_id.get(student_id)

        # If one of the auxiliary sheets has no record for the student,
        # there is not enough information to calculate the debt.
        if payment_data is None or amount_data is None:
            continue

        overdue_count = _overdue_payments(
            payment_data["expected_payment_date"],
            AS_OF_DATE,
        )

        if overdue_count == 0:
            continue

        if str(student.get("installment (Y/N)", "")).strip().upper() == "Y":
            installment_amount = _to_number(amount_data["installment_amount"])
            left_to_pay = _to_number(amount_data["left_to_pay"])

            # Six equal payments make up the installment plan.
            one_payment = installment_amount / INSTALLMENT_PERIODS
            debt = min(one_payment * overdue_count, left_to_pay)
        else:
            debt = _to_number(amount_data["one-time_payment"])

        # The reference answer uses whole rubles and truncates kopecks.
        debt = debt.quantize(Decimal("1"), rounding=ROUND_DOWN)

        if debt <= 0:
            continue

        report_lines.append(
            f"Студент {student['student_name']} - долг {debt} рублей"
        )

    with open("student_debt_report.txt", "w", encoding="utf-8") as report_file:
        report_file.write("\n".join(report_lines))
        if report_lines:
            report_file.write("\n")


# Example of obtaining the three lists with gspread:
# sheet1_data = client.open("название_таблицы").worksheet("Лист1").get_all_records()
# sheet2_data = client.open("название_таблицы").worksheet("Лист2").get_all_records()
# sheet3_data = client.open("название_таблицы").worksheet("Лист3").get_all_records()
# generate_report(sheet1_data, sheet2_data, sheet3_data)

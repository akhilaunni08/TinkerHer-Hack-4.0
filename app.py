from flask import Flask, render_template, request, redirect, url_for
import csv
import os
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from datetime import datetime

app = Flask(__name__)
EXPENSE_FILE = "data.csv"
INCOME_FILE = "income.csv"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

def init_files():
    if not os.path.exists(EXPENSE_FILE):
        with open(EXPENSE_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Amount", "Category", "Date", "Notes"])
    if not os.path.exists(INCOME_FILE):
        with open(INCOME_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Amount", "Source", "Date"])

init_files()

@app.route("/")
def home():
    total_spent = 0
    total_earned = 0
    if os.path.exists(EXPENSE_FILE):
        with open(EXPENSE_FILE, "r") as f:
            reader = csv.DictReader(f)
            total_spent = sum(float(row["Amount"]) for row in reader)
    if os.path.exists(INCOME_FILE):
        with open(INCOME_FILE, "r") as f:
            reader = csv.DictReader(f)
            total_earned = sum(float(row["Amount"]) for row in reader)
    
    return render_template("index.html", total_spent=total_spent, total_earned=total_earned, balance=total_earned - total_spent)

@app.route("/add", methods=["GET", "POST"])
def add_expense():
    if request.method == "POST":
        amount = request.form["amount"]
        category = request.form["category"]
        date = request.form.get("date", datetime.now().strftime("%Y-%m-2d"))
        notes = request.form.get("notes", "")

        with open(EXPENSE_FILE, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([amount, category, date, notes])

        return redirect(url_for("view_expenses"))

    return render_template("add_expense.html", today=datetime.now().strftime("%Y-%m-%d"))

@app.route("/expenses")
def view_expenses():
    expenses = []
    if os.path.exists(EXPENSE_FILE):
        with open(EXPENSE_FILE, "r") as file:
            reader = csv.DictReader(file)
            for index, row in enumerate(reader):
                expenses.append({
                    "id": index,
                    "amount": row["Amount"],
                    "category": row["Category"],
                    "date": row.get("Date", "N/A"),
                    "notes": row.get("Notes", "")
                })
    return render_template("expenses.html", expenses=expenses)

@app.route("/delete/<int:expense_id>")
def delete_expense(expense_id):
    if not os.path.exists(EXPENSE_FILE):
        return redirect(url_for("view_expenses"))

    with open(EXPENSE_FILE, "r") as file:
        reader = list(csv.reader(file))
        header = reader[0]
        data = reader[1:]

    if 0 <= expense_id < len(data):
        data.pop(expense_id)

    with open(EXPENSE_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(data)

    return redirect(url_for("view_expenses"))

@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
    if not os.path.exists(EXPENSE_FILE):
        return redirect(url_for("view_expenses"))

    with open(EXPENSE_FILE, "r") as file:
        reader = list(csv.reader(file))
        header = reader[0]
        data = reader[1:]

    if expense_id >= len(data):
        return redirect(url_for("view_expenses"))

    if request.method == "POST":
        data[expense_id] = [
            request.form["amount"],
            request.form["category"],
            request.form["date"],
            request.form["notes"]
        ]
        with open(EXPENSE_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(header)
            writer.writerows(data)
        return redirect(url_for("view_expenses"))

    expense = {
        "amount": data[expense_id][0],
        "category": data[expense_id][1],
        "date": data[expense_id][2] if len(data[expense_id]) > 2 else "",
        "notes": data[expense_id][3] if len(data[expense_id]) > 3 else ""
    }
    return render_template("edit_expense.html", expense=expense, expense_id=expense_id)

@app.route("/income", methods=["GET", "POST"])
def income():
    if request.method == "POST":
        amount = request.form["amount"]
        source = request.form["source"]
        date = request.form.get("date", datetime.now().strftime("%Y-%m-%d"))
        with open(INCOME_FILE, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([amount, source, date])
        return redirect(url_for("income"))

    incomes = []
    if os.path.exists(INCOME_FILE):
        with open(INCOME_FILE, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                incomes.append(row)
    return render_template("income.html", incomes=incomes)

@app.route("/dashboard")
def dashboard():
    categories = {}
    total = 0
    if os.path.exists(EXPENSE_FILE):
        with open(EXPENSE_FILE, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                amount = float(row["Amount"])
                category = row["Category"]
                total += amount
                categories[category] = categories.get(category, 0) + amount

    if categories:
        plt.figure(facecolor='#141414')
        plt.pie(categories.values(), labels=categories.keys(), autopct="%1.1f%%", 
                textprops={'color':"w"}, colors=['#10B981', '#34D399', '#059669', '#6EE7B7'])
        plt.title("Spending Breakdown", color='w')
        plt.axis('equal')
        plt.savefig(os.path.join(STATIC_DIR, "chart.png"), transparent=True)
        plt.close()

    return render_template("dashboard.html", total=total)

@app.route("/report")
def report():
    summary = {}
    if os.path.exists(EXPENSE_FILE):
        with open(EXPENSE_FILE, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                cat = row["Category"]
                amt = float(row["Amount"])
                summary[cat] = summary.get(cat, 0) + amt
    
    report_data = [{"category": k, "amount": v} for k, v in summary.items()]
    return render_template("report.html", report_data=report_data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)

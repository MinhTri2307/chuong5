import math
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

OPS = ["+", "-", "*", "/"]

SCORE_FIELDS = [
    {"key": "cc", "label": "Chuyên cần (10%)", "weight": Decimal("0.1")},
    {"key": "gk", "label": "Giữa kỳ (30%)", "weight": Decimal("0.3")},
    {"key": "ck", "label": "Cuối kỳ (60%)", "weight": Decimal("0.6")},
]


def parse_number(text):
    text = (text or "").strip().replace(",", ".")
    try:
        value = float(text)
    except ValueError:
        return None
    if not math.isfinite(value):
        return None
    return value


def fmt(x):
    if not math.isfinite(x):
        return "∞"
    x = round(x, 10)
    if x == int(x):
        return str(int(x))
    return str(x)


def check_score(text):
    text = (text or "").strip().replace(",", ".")
    try:
        value = Decimal(text)
    except InvalidOperation:
        return None, "Vui lòng nhập một số."
    if not value.is_finite():
        return None, "Vui lòng nhập một số."
    if value < 0 or value > 10:
        return None, "Điểm phải từ 0 đến 10."
    return value, None


def letter_grade(score):
    if score >= Decimal("8.5"):
        return "A"
    if score >= Decimal("7.0"):
        return "B"
    if score >= Decimal("5.5"):
        return "C"
    if score >= Decimal("4.0"):
        return "D"
    return "F"


def check_range(text, low, high):
    value = parse_number(text)
    if value is None:
        return None, "Vui lòng nhập một số."
    if value < low or value > high:
        return None, f"Giá trị phải từ {fmt(low)} đến {fmt(high)}."
    return value, None


def bmi_class(bmi):
    # chuẩn người châu Á
    if bmi < 18.5:
        return "Thiếu cân", "vang"
    if bmi < 23:
        return "Bình thường", "xanh"
    if bmi < 25:
        return "Thừa cân", "vang"
    return "Béo phì", "do"


@app.route("/")
def index():
    return redirect(url_for("calc"))


@app.route("/calc", methods=["GET", "POST"])
def calc():
    a_text = ""
    b_text = ""
    op = "+"
    errors = {}
    result = None

    if request.method == "POST":
        a_text = request.form.get("a", "")
        b_text = request.form.get("b", "")
        op = request.form.get("op", "")

        a = parse_number(a_text)
        b = parse_number(b_text)

        if a is None:
            errors["a"] = "Vui lòng nhập một số."
        if b is None:
            errors["b"] = "Vui lòng nhập một số."
        if op not in OPS:
            errors["op"] = "Phép toán không hợp lệ."
        if not errors and op == "/" and b == 0:
            errors["b"] = "Không thể chia cho 0."

        if not errors:
            if op == "+":
                value = a + b
            elif op == "-":
                value = a - b
            elif op == "*":
                value = a * b
            else:
                value = a / b
            result = f"{fmt(a)} {op} {fmt(b)} = {fmt(value)}"

    return render_template(
        "calc.html",
        a=a_text,
        b=b_text,
        op=op,
        ops=OPS,
        errors=errors,
        result=result,
    )


@app.route("/diem", methods=["GET", "POST"])
def diem():
    values = {f["key"]: "" for f in SCORE_FIELDS}
    errors = {}
    result = None

    if request.method == "POST":
        scores = {}
        for f in SCORE_FIELDS:
            key = f["key"]
            values[key] = request.form.get(key, "")
            value, error = check_score(values[key])
            if error:
                errors[key] = error
            else:
                scores[key] = value

        if not errors:
            total = sum(scores[f["key"]] * f["weight"] for f in SCORE_FIELDS)
            total = total.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
            if scores["ck"] < 1:
                result = f"{total} · F (điểm thi dưới 1)"
            else:
                result = f"{total} · {letter_grade(total)}"

    return render_template(
        "diem.html",
        fields=SCORE_FIELDS,
        values=values,
        errors=errors,
        result=result,
    )


@app.route("/bmi", methods=["GET", "POST"])
def bmi():
    values = {"h": "", "w": ""}
    errors = {}
    result = None

    if request.method == "POST":
        values["h"] = request.form.get("h", "")
        values["w"] = request.form.get("w", "")

        h, err = check_range(values["h"], 50, 250)
        if err:
            errors["h"] = err
        w, err = check_range(values["w"], 10, 300)
        if err:
            errors["w"] = err

        if not errors:
            m = h / 100
            value = w / (m * m)
            label, color = bmi_class(value)
            result = {
                "text": f"{round(value, 1)} · {label}",
                "color": color,
                "range": f"{18.5 * m * m:.1f} – {22.9 * m * m:.1f} kg",
            }

    return render_template("bmi.html", values=values, errors=errors, result=result)


if __name__ == "__main__":
    app.run(debug=True)
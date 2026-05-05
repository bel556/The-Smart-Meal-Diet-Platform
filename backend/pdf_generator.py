from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

styles = getSampleStyleSheet()



def compute_totals(problem, state):
    total_cost = problem.get_total_cost(state)
    total_cal = problem.get_total_cal(state)

    protein = 0
    carbs = 0
    fat = 0

    for day in state:
        protein += (
            problem.transitionmodel["Breakfast"][day[0]][3] +
            problem.transitionmodel["Lunch"][day[1]][3] +
            problem.transitionmodel["Dinner"][day[2]][3]
        )
        carbs += (
            problem.transitionmodel["Breakfast"][day[0]][4] +
            problem.transitionmodel["Lunch"][day[1]][4] +
            problem.transitionmodel["Dinner"][day[2]][4]
        )
        fat += (
            problem.transitionmodel["Breakfast"][day[0]][5] +
            problem.transitionmodel["Lunch"][day[1]][5] +
            problem.transitionmodel["Dinner"][day[2]][5]
        )

    return total_cost, total_cal, protein, carbs, fat


def format_cell(meal_name):
    return Paragraph(f"<b>{meal_name}</b>", styles["BodyText"])



def create_week_table(problem, week_state, week_number):

    days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    header = [""] + days
    table_data = [header]

    meal_types = ["Breakfast", "Lunch", "Dinner"]

    for i, meal_type in enumerate(meal_types):
        row = [Paragraph(f"<b>{meal_type}</b>", styles["BodyText"])]

        for day in week_state:
            row.append(format_cell(day[i]))

        table_data.append(row)

    col_widths = [70] + [60] * 7

    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F81BD")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#D9E1F2")),
        ("BACKGROUND", (1, 1), (-1, -1), colors.white),

        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),

        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    title = Paragraph(f"<b>Week {week_number}</b>", styles["Heading2"])

    return [title, Spacer(1, 10), table, Spacer(1, 15)]



def create_pdf_in_memory(problem, state):

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)

    elements = []


    title = Paragraph(
        "<b><font size=20>4-Week Meal Plan</font></b>",
        styles["Title"]
    )
    elements.append(title)
    elements.append(Spacer(1, 15))

    
    cost, cal, protein, carbs, fat = compute_totals(problem, state)

    summary = Paragraph(
        f"""
        <b>Summary</b><br/>
        Cost: {round(cost, 2)} DA<br/>
        Calories: {round(cal, 2)} Kcal<br/>
        Protein: {round(protein, 2)} g &nbsp;&nbsp;
        Carbs: {round(carbs, 2)} g &nbsp;&nbsp;
        Fat: {round(fat, 2)} g
        """,
        styles["Normal"]
    )

    elements.append(summary)
    elements.append(Spacer(1, 20))

   
    weeks = [state[i:i + 7] for i in range(0, 28, 7)]

 
    elements.extend(create_week_table(problem, weeks[0], 1))
    elements.append(Spacer(1, 30))
    elements.extend(create_week_table(problem, weeks[1], 2))

    elements.append(PageBreak())


    elements.extend(create_week_table(problem, weeks[2], 3))
    elements.append(Spacer(1, 30))
    elements.extend(create_week_table(problem, weeks[3], 4))

    doc.build(elements)

    buffer.seek(0)
    return buffer
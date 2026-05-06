from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, HRFlowable
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch

styles = getSampleStyleSheet()

# Modern custom styles
styles.add(ParagraphStyle(
    name='ModernTitle',
    parent=styles['Title'],
    fontName='Helvetica-Bold',
    fontSize=24,
    textColor=colors.HexColor("#2C3E50"),
    spaceAfter=20
))

styles.add(ParagraphStyle(
    name='ModernSubTitle',
    parent=styles['Heading2'],
    fontName='Helvetica-Bold',
    fontSize=16,
    textColor=colors.HexColor("#34495E"),
    spaceBefore=15,
    spaceAfter=10
))

styles.add(ParagraphStyle(
    name='StatsLabel',
    parent=styles['Normal'],
    fontSize=9,
    textColor=colors.HexColor("#7F8C8D"),
    alignment=1
))


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


def format_cell(meal_name, meal_stats):
    return Paragraph(
        f"<b>{meal_name}</b><br/><font size=7 color='#7F8C8D'>{meal_stats['cal']} kcal • {meal_stats['price']} DA</font>",
        styles["BodyText"]
    )


def create_week_table(problem, week_state, week_number):

    days_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    meal_types = ["Breakfast", "Lunch", "Dinner"]
    
    # Pre-cache meal data to avoid repeated dict lookups in the loop
    cache = problem.transitionmodel

    header = [""] + [Paragraph(f"<b>{d}</b>", styles["StatsLabel"]) for d in days_names]
    table_data = [header]

    # Transpose state to process by meal type
    meal_rows = []
    daily_stats = [{"cal": 0, "price": 0} for _ in range(7)]

    for i, meal_type in enumerate(meal_types):
        row = [Paragraph(f"<b>{meal_type}</b>", styles["BodyText"])]
        type_cache = cache[meal_type]

        for day_idx, day in enumerate(week_state):
            meal_name = day[i]
            meal_info = type_cache[meal_name]
            
            price = meal_info[1]
            cal = meal_info[2]
            
            daily_stats[day_idx]["price"] += price
            daily_stats[day_idx]["cal"] += cal
            
            row.append(format_cell(meal_name, {"price": round(price, 1), "cal": int(cal)}))

        table_data.append(row)

    # ADDING DAILY TOTALS ROW (using computed stats)
    totals_row = [Paragraph("<b>Daily<br/>Total</b>", styles["BodyText"])]
    for stats in daily_stats:
        totals_row.append(Paragraph(
            f"<b>{int(stats['cal'])} kcal</b><br/><font size=8 color='#2980B9'>{round(stats['price'], 1)} DA</font>",
            styles["StatsLabel"]
        ))
    table_data.append(totals_row)

    col_widths = [75] + [100] * 7

    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    table.setStyle(TableStyle([
        # Headers
        ("BACKGROUND", (1, 0), (-1, 0), colors.HexColor("#ECF0F1")),
        ("TEXTCOLOR", (1, 0), (-1, 0), colors.HexColor("#2C3E50")),
        
        # Meal Labels Column
        ("BACKGROUND", (0, 1), (0, -2), colors.HexColor("#F9F9F9")),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        
        # Totals Row
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EBF5FB")),
        ("TOPPADDING", (0, -1), (-1, -1), 8),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 8),

        # Grid and General
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D5DBDB")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 1), (-1, -2), 10),
        ("BOTTOMPADDING", (0, 1), (-1, -2), 10),
    ]))

    title = Paragraph(f"Week {week_number}", styles["ModernSubTitle"])

    return [title, Spacer(1, 5), table, Spacer(1, 20)]


def create_pdf_in_memory(problem, state):

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=landscape(A4),
        rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
    )

    elements = []

    # Title Section
    elements.append(Paragraph("Personalized 4-Week Meal Plan", styles["ModernTitle"]))
    
    cost, cal, protein, carbs, fat = compute_totals(problem, state)

    # Summary Card-like Section
    summary_data = [
        [
            Paragraph(f"<b>Total Budget</b><br/><font size=14>{round(cost, 2)} DA</font>", styles["StatsLabel"]),
            Paragraph(f"<b>Total Energy</b><br/><font size=14>{int(cal)} kcal</font>", styles["StatsLabel"]),
            Paragraph(f"<b>Protein</b><br/><font size=14>{int(protein)}g</font>", styles["StatsLabel"]),
            Paragraph(f"<b>Carbs</b><br/><font size=14>{int(carbs)}g</font>", styles["StatsLabel"]),
            Paragraph(f"<b>Fats</b><br/><font size=14>{int(fat)}g</font>", styles["StatsLabel"]),
        ]
    ]
    summary_table = Table(summary_data, colWidths=[120]*5)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FDFEFE")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#BDC3C7")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 25))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#D5DBDB"), spaceAfter=20))

    weeks = [state[i:i + 7] for i in range(0, 28, 7)]

    # We can fit 1 week per page for better readability in landscape
    for i, week_state in enumerate(weeks):
        elements.extend(create_week_table(problem, week_state, i + 1))
        if i < 3: # Page break after each week except last
            elements.append(PageBreak())

    doc.build(elements)

    buffer.seek(0)
    return buffer
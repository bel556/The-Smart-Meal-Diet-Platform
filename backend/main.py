from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd

from schemas import MealRequest
from GA import GAProblem, GASearch
from pdf_generator import create_pdf_in_memory

app = FastAPI(title="Meal Plan Generator API")


# Load dataset once (IMPORTANT: not inside endpoint)
recipes_df = pd.read_csv("recipes.csv")


@app.post("/generate-meal-plan")
def generate_meal_plan(request: MealRequest):
    try:
        # 1️⃣ Create GA problem
        problem = GAProblem(
            recipes_df=recipes_df,
            total_price=request.budget,
            tdee=request.calories,
            nutri_preference_str=request.goal
        )

        # 2️⃣ Run Genetic Algorithm
        best_state, fitness = GASearch(problem)

        if not best_state:
            raise HTTPException(status_code=500, detail="Failed to generate meal plan")

        # 3️⃣ Generate PDF in memory
        pdf_buffer = create_pdf_in_memory(problem, best_state)

        # 4️⃣ Return PDF
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=meal_plan.pdf"
            }
        )

    except ValueError as e:
        # for invalid goal like "bulkkk"
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
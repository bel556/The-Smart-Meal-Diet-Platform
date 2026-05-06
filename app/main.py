from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd

try:
    from app.schemas import MealRequest
    from app.GA import GAProblem, GASearch
    from app.pdf_generator import create_pdf_in_memory
except ImportError:
    from schemas import MealRequest
    from GA import GAProblem, GASearch
    from pdf_generator import create_pdf_in_memory

from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
                title="Meal Plan Generator API",
                docs_url=None,
                redoc_url=None,
                openapi_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://nutri-mlih.vercel.app"],  # Allows your Next.js app
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (POST, GET, etc.)
    allow_headers=["*"],  # Allows all headers
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
recipes_df = pd.read_csv(os.path.join(BASE_DIR, "recipes.csv"))


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
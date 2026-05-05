from pydantic import BaseModel

class MealRequest(BaseModel):
    budget: float
    calories: int
    goal: str   # "maintain", "gain", "loss"
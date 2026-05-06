import random

NUTRI_PREFERENCE_MAP = {
    "maintain":       {"protein": 0.30, "fat": 0.25, "carbs": 0.45},
    "gain":   {"protein": 0.40, "fat": 0.25, "carbs": 0.35},
    "loss":       {"protein": 0.25, "fat": 0.35, "carbs": 0.40},
}

def Gettransitionmodel(recipes_df):
    result = {}

    for _, row in recipes_df.iterrows():
        meal_type = row["type"]
        meal_name = row["Name"]

        meal_info = (
            row["Category"],
            row["total_price"],
            row["provided_calories"],
            row["provided_protein"],
            row["provided_carbs"],
            row["provided_fat"]
        )
        if meal_type not in result:
           result[meal_type] = {}

        result[meal_type][meal_name] = meal_info

    return result

def resolve_nutri_preference(preference_str):
    key = preference_str.strip().lower()
    if key not in NUTRI_PREFERENCE_MAP:
        valid = ", ".join(NUTRI_PREFERENCE_MAP.keys())
        raise ValueError(f"Unknown preference '{preference_str}'. Valid options: {valid}")
    return NUTRI_PREFERENCE_MAP[key]

def diversity_penalty_per_week(state):
    penalty = 0
    days_per_week = 7
    meals_per_day = 3

    for start in range(0, len(state), days_per_week):
        week = state[start:start + days_per_week]

        week_meals = [meal for day in week for meal in day]

        counts = {}
        for meal in week_meals:
            counts[meal] = counts.get(meal, 0) + 1

        for meal, count in counts.items():
            if count > 2:
                penalty += (count - 2)
    return penalty / (len(state) * meals_per_day)


class GAProblem:
    def __init__(self, recipes_df, total_price, tdee, nutri_preference_str="maintain"):
        self.size = 90
        self.total_price = total_price
        self.tdee = tdee
        self.transitionmodel = Gettransitionmodel(recipes_df)
        prefs = resolve_nutri_preference(nutri_preference_str)
        self.target_protein_g = tdee * prefs["protein"]
        self.target_fat_g     = tdee * prefs["fat"]
        self.target_carbs_g   = tdee * prefs["carbs"]
     
     
    def get_total_cost(self, state):
        total_cost = 0
        model = self.transitionmodel
        for day in state:
           total_cost += (
               model["Breakfast"][day[0]][1] +
               model["Lunch"][day[1]][1] +
               model["Dinner"][day[2]][1]
           )
        return total_cost
    
    
    def get_total_cal(self,state):
        total_cal = 0
        model = self.transitionmodel
        for day in state:
            total_cal += (
                model["Breakfast"][day[0]][2] +
                model["Lunch"][day[1]][2] +
                model["Dinner"][day[2]][2]
            )
        return total_cal
    

    def _macro_penalty_for_day(self, day):
        actual_protein =  self.transitionmodel["Breakfast"][day[0]][3] +  self.transitionmodel["Dinner"][day[2]][3] +  self.transitionmodel["Lunch"][day[1]][3]
        actual_carbs   = self.transitionmodel["Breakfast"][day[0]][4] +  self.transitionmodel["Dinner"][day[2]][4] +  self.transitionmodel["Lunch"][day[1]][4]
        actual_fat   = self.transitionmodel["Breakfast"][day[0]][5] +  self.transitionmodel["Dinner"][day[2]][5] +  self.transitionmodel["Lunch"][day[1]][5]  
        protein_dev = abs(actual_protein - self.target_protein_g) / self.target_protein_g
        fat_dev     = abs(actual_fat     - self.target_fat_g)     / self.target_fat_g
        carbs_dev   = abs(actual_carbs   - self.target_carbs_g)   / self.target_carbs_g
        return (protein_dev + fat_dev + carbs_dev) / 3
    

    def fitness_function(self, state):
        total_cost = self.get_total_cost(state)
        cost_penalty = 1 if (self.total_price - total_cost) / (self.total_price) < 0 else (self.total_price - total_cost) / (self.total_price)
        lower_bound = 0.9 * self.tdee
        upper_bound = 1.1 * self.tdee

        bad_days = 0
        total_macro_dev=0
        for day in state:
            day_calories = (
                self.transitionmodel["Breakfast"][day[0]][2] +
                self.transitionmodel["Lunch"][day[1]][2] +
                self.transitionmodel["Dinner"][day[2]][2]
            )
            if day_calories != self.tdee:
                bad_days += 0.001
            if day_calories < lower_bound or day_calories > upper_bound:
                bad_days += 1
            total_macro_dev += self._macro_penalty_for_day(day)
        nutrition_penalty = bad_days / len(state)
        macro_penalty     = total_macro_dev / len(state)
        diversity_penalty = diversity_penalty_per_week(state)
        fitness = -(
            0.3 * cost_penalty +
            0.2* nutrition_penalty +
            0.15 * diversity_penalty +
            0.35* macro_penalty
        )
        return fitness
    
    
    def generate_random_state(self):
         breakfast_list = list(self.transitionmodel['Breakfast'].keys())
         lunch_list = list(self.transitionmodel['Lunch'].keys())
         dinner_list = list(self.transitionmodel['Dinner'].keys())
         return [(random.choice(breakfast_list),
                  random.choice(lunch_list),
                  random.choice(dinner_list))
                    for _ in range(30)]
def crossover_and_mutation(population,problem):
       childs = []
     
       for i in range(len(population)):
         for j in range(i+1,len(population)):
            cutoff = random.randrange(1,29)
            parent_a = population[i][0]
            parent_b = population[j][0]
            child_a = parent_a[:cutoff] + parent_b[cutoff:]
            child_b = parent_b[:cutoff] + parent_a[cutoff:]
            random_lunch_a = random.choice(list(problem.transitionmodel['Lunch'].keys()))
            random_lunch_b = random.choice(list(problem.transitionmodel['Lunch'].keys()))
            random_pos_a  = random.randrange(30)
            random_pos_b  = random.randrange(30)
            t1 =   [child_a[random_pos_a][0],random_lunch_a, child_a[random_pos_a][2]]
            t2 =  [child_b[random_pos_b][0],random_lunch_b, child_b[random_pos_b][2]]
            child_a[random_pos_a] = tuple(t1) 
            child_b[random_pos_b] = tuple(t2) 
            childs.append((child_a,problem.fitness_function(child_a)))
            childs.append((child_b,problem.fitness_function(child_b)))
       return childs

def GASearch(problem):
    # step 1 Selection:
    list_of_states = []
    for _ in range(100):
        state = problem.generate_random_state()
        fitness = problem.fitness_function(state)
        list_of_states.append((state,fitness))
    population = sorted(list_of_states, key=lambda x: x[1], reverse=True)[:25]
    # step 2 and 3 crossover and mutation
    for _ in range(250):
        population = sorted(population, key=lambda x: x[1], reverse=True)[:25]
        for state, fitness in population:
            if fitness == 0:
                return (state, fitness)
        population =  crossover_and_mutation(population,problem)
    best_candidate = sorted(population, key=lambda x: x[1], reverse=True)[:1]
    return best_candidate[0]

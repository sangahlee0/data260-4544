from mcp.server.fastmcp import FastMCP
import requests

mcp = FastMCP("meals")

BASE_URL = "https://www.themealdb.com/api/json/v1/1"

@mcp.tool()
def search_meals_by_name(query: str, limit: int=5):
    """
    Search for meals by name using TheMealDB API.

    Input:
        query (str): The search query for meal names.
        limit (int): The maximum number of results to return.

    Output:
        list objects with {id, name, area, category, thumb}

    """
    if limit < 1 or limit > 25:
        return {"error": "Limit must be between 1 and 25."}
    try:
        response = requests.get(f"{BASE_URL}/search.php?s={query}")
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch data from API: {e}")
    except ValueError as e:
        raise RuntimeError(f"Failed to parse JSON response: {e}")

    meals = data.get("meals", [])
    if not meals:
        return {"message": "No matches found."}
    results = []
    for meal in meals[:limit]:
        # Return only the required fields: id, name, area, category, and thumb
        results.append({
            "id": meal.get("idMeal"),
            "name": meal.get("strMeal"),
            "area": meal.get("strArea"),
            "category": meal.get("strCategory"),
            "thumb": meal.get("strMealThumb")
        })
    return results


@mcp.tool()
def meals_by_ingredient(ingredient: str, limit: int=12):
    """
    Input:
        ingredient (str): The ingredient to search for.
        limit (int): The maximum number of results to return.

    Output:
        list objects with {id, name, thumb}

    """
    try:
        response = requests.get(f"{BASE_URL}/filter.php?i={ingredient}")
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch data from API: {e}")
    except ValueError as e:
        raise RuntimeError(f"Failed to parse JSON response: {e}")

    meals = data.get("meals", [])
    if not meals:
        return {"message": "No matches found."}
    results = []
    for meal in meals[:limit]:
        results.append({
            "id": meal.get("idMeal"),
            "name": meal.get("strMeal"),
            "thumb": meal.get("strMealThumb")
        })
    return results

@mcp.tool()
def random_meal():
    """
    Output:
        dict with {id, name, category, area, instructions, image, source, youtube, ingredients: [{name, measure}]}

    """
    try:
        response = requests.get(f"{BASE_URL}/random.php")
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch data from API: {e}")
    except ValueError as e:
        raise RuntimeError(f"Failed to parse JSON response: {e}")

    meal = data.get("meals")

    if not meal:
        return {"message": "No matches found."}

    meal = meal[0]  # Get the first meal from the list

    # Ingredients is a list of dicts with name and measure
    ingredients = []
    for i in range(1, 21):  # db ingredient field is 1-20
        ingredient = meal.get(f"strIngredient{i}")
        measure = meal.get(f"strMeasure{i}")
        if ingredient and ingredient.strip():
            ingredients.append({"name": ingredient.strip(), "measure": measure.strip() if measure else ""})
    return {"id": meal.get("idMeal"), 
            "name": meal.get("strMeal"), 
            "category": meal.get("strCategory"), 
            "area": meal.get("strArea"), 
            "instructions": meal.get("strInstructions"), 
            "image": meal.get("strMealThumb"), 
            "source": meal.get("strSource"), 
            "youtube": meal.get("strYoutube"), 
            "ingredients": ingredients}


@mcp.tool()
def meal_details(id: str):
    """
    Get meal details by ID using TheMealDB API.

    Input:
        id (str): The ID of the meal.

    Output:
        dict with {id, name, category, area, instructions, image, source, youtube, ingredients: [{name, measure}]}

    """
    try:
        response = requests.get(f"{BASE_URL}/lookup.php?i={id}")
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch data from API: {e}")
    except ValueError as e:
        raise RuntimeError(f"Failed to parse JSON response: {e}")

    meal = data.get("meals")
    if not meal:
        return {"message": "No matches found."}
    meal = meal[0]  # Get the first meal from the list
    # Ingredients is a list of dicts with name and measure
    ingredients = []
    for i in range(1, 21):  # db ingredient field is 1-20
        ingredient = meal.get(f"strIngredient{i}")
        measure = meal.get(f"strMeasure{i}")
        if ingredient and ingredient.strip():
            ingredients.append({"name": ingredient.strip(), "measure": measure.strip() if measure else ""})
    return {"id": meal.get("idMeal"), 
            "name": meal.get("strMeal"), 
            "category": meal.get("strCategory"), 
            "area": meal.get("strArea"), 
            "instructions": meal.get("strInstructions"), 
            "image": meal.get("strMealThumb"), 
            "source": meal.get("strSource"), 
            "youtube": meal.get("strYoutube"), 
            "ingredients": ingredients}


if __name__ == "__main__":
    mcp.run()
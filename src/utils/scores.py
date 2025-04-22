import os
import json
import datetime

# Define file paths as constants for better maintainability
HIGHSCORE_FILE = "data/stats/highscores.json"

# Enhanced high score functions
def load_high_scores():
    """Load high scores with history from file or create default if it doesn't exist"""
    try:
        if os.path.exists(HIGHSCORE_FILE):
            with open(HIGHSCORE_FILE, 'r') as f:
                high_scores = json.load(f)
                
            # Ensure the file has the expected structure
            if not isinstance(high_scores, dict):
                print("Warning: High scores file has invalid format. Creating new file.")
                high_scores = create_default_high_scores()
        else:
            high_scores = create_default_high_scores()
            
        # Ensure all required categories exist
        required_categories = ["classic", "ai", "fibonacci", "fibonacci_ai", "vs_mode"]
        for category in required_categories:
            if category not in high_scores:
                high_scores[category] = {"scores": [], "dates": []}
                
                # Add special fields for specific categories
                if category == "fibonacci" or category == "fibonacci_ai":
                    high_scores[category]["fib_values"] = []
                    
        return high_scores
    except Exception as e:
        print(f"Error loading high scores: {e}")
        return create_default_high_scores()

def create_default_high_scores():
    """Create a default high scores structure"""
    high_scores = {
        "classic": {"scores": [], "dates": []},
        "ai": {"scores": [], "dates": []},
        "fibonacci": {"scores": [], "fib_values": [], "dates": []},
        "fibonacci_ai": {"scores": [], "fib_values": [], "dates": []},
        "vs_mode": {
            "player": {"scores": [], "dates": []},
            "ai": {"scores": [], "dates": []},
            "matches": []
        }
    }
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(HIGHSCORE_FILE), exist_ok=True)
    
    # Save the default structure
    with open(HIGHSCORE_FILE, 'w') as f:
        json.dump(high_scores, f, indent=4)
        
    return high_scores

def save_high_score(mode, score):
    """Save high score with date to the high scores file"""
    try:
        high_scores = load_high_scores()
        
        # Format today's date
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Check if this category exists
        if mode not in high_scores:
            high_scores[mode] = {"scores": [], "dates": []}
            
        # Add the score and date
        high_scores[mode]["scores"].append(score)
        high_scores[mode]["dates"].append(today)
        
        # Sort scores (highest first) and keep only top 10
        if len(high_scores[mode]["scores"]) > 10:
            combined = list(zip(high_scores[mode]["scores"], high_scores[mode]["dates"]))
            combined.sort(key=lambda x: x[0], reverse=True)  # Sort by score
            combined = combined[:10]  # Keep top 10
            
            high_scores[mode]["scores"] = [item[0] for item in combined]
            high_scores[mode]["dates"] = [item[1] for item in combined]
        
        # Save the updated high scores
        with open(HIGHSCORE_FILE, 'w') as f:
            json.dump(high_scores, f, indent=4)
        
        # Check if this is a new high score
        return score == max(high_scores[mode]["scores"])
    except Exception as e:
        print(f"Error saving high score: {e}")
        return False

def save_fibonacci_high_score(food_score, fib_value):
    """Save Fibonacci high score with both food count and Fibonacci value"""
    try:
        high_scores = load_high_scores()
        
        # Format today's date
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Check if category exists
        if "fibonacci" not in high_scores:
            high_scores["fibonacci"] = {
                "scores": [],
                "fib_values": [],
                "dates": []
            }
            
        # Add the scores and date
        high_scores["fibonacci"]["scores"].append(food_score)
        high_scores["fibonacci"]["fib_values"].append(fib_value)
        high_scores["fibonacci"]["dates"].append(today)
        
        # Sort by food score (highest first) and keep top 10
        if len(high_scores["fibonacci"]["scores"]) > 10:
            combined = list(zip(
                high_scores["fibonacci"]["scores"],
                high_scores["fibonacci"]["fib_values"],
                high_scores["fibonacci"]["dates"]
            ))
            combined.sort(key=lambda x: x[0], reverse=True)  # Sort by food score
            combined = combined[:10]  # Keep top 10
            
            high_scores["fibonacci"]["scores"] = [item[0] for item in combined]
            high_scores["fibonacci"]["fib_values"] = [item[1] for item in combined]
            high_scores["fibonacci"]["dates"] = [item[2] for item in combined]
        
        # Save the updated high scores
        with open(HIGHSCORE_FILE, 'w') as f:
            json.dump(high_scores, f, indent=4)
        
        # Check if this is a new high score
        return food_score == max(high_scores["fibonacci"]["scores"])
    except Exception as e:
        print(f"Error saving Fibonacci high score: {e}")
        return False

def save_vs_high_score(player_type, score):
    """Save player vs AI high scores"""
    try:
        high_scores = load_high_scores()
        
        # Format today's date
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Check if category exists
        if "vs_mode" not in high_scores:
            high_scores["vs_mode"] = {
                "player": {"scores": [], "dates": []},
                "ai": {"scores": [], "dates": []},
                "matches": []
            }
            
        # Make sure the player type exists
        if player_type not in ["player", "ai"]:
            print(f"Invalid player type: {player_type}")
            return False
            
        # Add the score and date
        high_scores["vs_mode"][player_type]["scores"].append(score)
        high_scores["vs_mode"][player_type]["dates"].append(today)
        
        # Sort scores (highest first) and keep only top 10
        if len(high_scores["vs_mode"][player_type]["scores"]) > 10:
            combined = list(zip(
                high_scores["vs_mode"][player_type]["scores"], 
                high_scores["vs_mode"][player_type]["dates"]
            ))
            combined.sort(key=lambda x: x[0], reverse=True)  # Sort by score
            combined = combined[:10]  # Keep top 10
            
            high_scores["vs_mode"][player_type]["scores"] = [item[0] for item in combined]
            high_scores["vs_mode"][player_type]["dates"] = [item[1] for item in combined]
        
        # Save the updated high scores
        with open(HIGHSCORE_FILE, 'w') as f:
            json.dump(high_scores, f, indent=4)
        
        # Check if this is a new high score
        return score == max(high_scores["vs_mode"][player_type]["scores"])
    except Exception as e:
        print(f"Error saving VS mode high score: {e}")
        return False
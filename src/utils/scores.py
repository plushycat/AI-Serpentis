import os
import json
import datetime

# Add at the top of the file
_high_scores_cache = None
_last_updated = 0

# Define file paths as constants for better maintainability
HIGHSCORE_FILE = "data/stats/highscores.json"

# Enhanced high score functions
def load_high_scores():
    """Load high scores with caching for better performance"""
    global _high_scores_cache, _last_updated
    current_time = datetime.datetime.now().timestamp()
    
    # Use cache if available and recent (less than 5 seconds old)
    if _high_scores_cache and current_time - _last_updated < 5:
        return _high_scores_cache
        
    # Otherwise load from file
    try:
        print(f"Attempting to load high scores from {HIGHSCORE_FILE}")
        if os.path.exists(HIGHSCORE_FILE):
            with open(HIGHSCORE_FILE, 'r') as f:
                high_scores = json.load(f)
                print(f"Successfully loaded high scores: {list(high_scores.keys())}")
                
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
                    
        # Update cache
        _high_scores_cache = high_scores
        _last_updated = current_time
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

# Fix for save_high_score
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
        
        # ALWAYS sort scores (highest first) regardless of count
        combined = list(zip(high_scores[mode]["scores"], high_scores[mode]["dates"]))
        combined.sort(key=lambda x: x[0], reverse=True)  # Sort by score
        combined = combined[:10] if len(combined) > 10 else combined  # Keep top 10 if needed
        
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

# Fix for save_fibonacci_high_score
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
        
        # ALWAYS sort by food score (highest first)
        combined = list(zip(
            high_scores["fibonacci"]["scores"],
            high_scores["fibonacci"]["fib_values"],
            high_scores["fibonacci"]["dates"]
        ))
        combined.sort(key=lambda x: x[0], reverse=True)  # Sort by food score
        combined = combined[:10] if len(combined) > 10 else combined  # Keep top 10 if needed
        
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
        
        # ALWAYS sort scores (highest first) regardless of count
        combined = list(zip(
            high_scores["vs_mode"][player_type]["scores"], 
            high_scores["vs_mode"][player_type]["dates"]
        ))
        combined.sort(key=lambda x: x[0], reverse=True)  # Sort by score
        combined = combined[:10] if len(combined) > 10 else combined  # Keep top 10 if needed
        
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

def resort_all_high_scores():
    """Resort all high scores and correct legacy data structures"""
    try:
        high_scores = load_high_scores()
        modified = False
        
        # Add a flag to check if data has already been resorted
        if high_scores.get("_resorted"):
            return high_scores
            
        # Mark as resorted
        high_scores["_resorted"] = True
        modified = True
        
        # Resort classic mode and AI mode scores
        for mode in ["classic", "ai"]:
            if mode in high_scores:
                # Ensure scores are in the new format
                if isinstance(high_scores[mode], dict) and "scores" in high_scores[mode]:
                    scores = high_scores[mode]["scores"]
                    dates = high_scores[mode].get("dates", [])
                    
                    # If dates are missing, create placeholder dates
                    while len(dates) < len(scores):
                        dates.append(datetime.datetime.now().strftime("%Y-%m-%d"))
                    
                    # Sort scores
                    combined = list(zip(scores, dates))
                    combined.sort(key=lambda x: x[0], reverse=True)  # Sort by score (highest first)
                    
                    # Keep only top 10
                    combined = combined[:10] if len(combined) > 10 else combined
                    
                    # Update high scores
                    high_scores[mode]["scores"] = [item[0] for item in combined]
                    high_scores[mode]["dates"] = [item[1] for item in combined]
                    modified = True
                    
                # Handle legacy format (direct integer)
                elif isinstance(high_scores[mode], (int, float)):
                    # Convert to new format
                    score = high_scores[mode]
                    high_scores[mode] = {
                        "scores": [score],
                        "dates": [datetime.datetime.now().strftime("%Y-%m-%d")]
                    }
                    modified = True
        
        # Resort fibonacci modes
        for mode in ["fibonacci", "fibonacci_ai"]:
            if mode in high_scores:
                # Ensure we have all required fields
                if isinstance(high_scores[mode], dict) and "scores" in high_scores[mode]:
                    scores = high_scores[mode]["scores"]
                    fib_values = high_scores[mode].get("fib_values", [0] * len(scores))
                    dates = high_scores[mode].get("dates", [])
                    
                    # If dates are missing, create placeholder dates
                    while len(dates) < len(scores):
                        dates.append(datetime.datetime.now().strftime("%Y-%m-%d"))
                        
                    # If fib_values are missing, create placeholder values
                    while len(fib_values) < len(scores):
                        fib_values.append(0)
                    
                    # Sort scores
                    combined = list(zip(scores, fib_values, dates))
                    combined.sort(key=lambda x: x[0], reverse=True)  # Sort by score (highest first)
                    
                    # Keep only top 10
                    combined = combined[:10] if len(combined) > 10 else combined
                    
                    # Update high scores
                    high_scores[mode]["scores"] = [item[0] for item in combined]
                    high_scores[mode]["fib_values"] = [item[1] for item in combined]
                    high_scores[mode]["dates"] = [item[2] for item in combined]
                    modified = True
        
        # Handle VS mode - both old and new formats
        # First, sort the current vs_mode format
        if "vs_mode" in high_scores:
            for player_type in ["player", "ai"]:
                if player_type in high_scores["vs_mode"] and "scores" in high_scores["vs_mode"][player_type]:
                    scores = high_scores["vs_mode"][player_type]["scores"]
                    dates = high_scores["vs_mode"][player_type].get("dates", [])
                    
                    # If dates are missing, create placeholder dates
                    while len(dates) < len(scores):
                        dates.append(datetime.datetime.now().strftime("%Y-%m-%d"))
                    
                    # Sort scores
                    combined = list(zip(scores, dates))
                    combined.sort(key=lambda x: x[0], reverse=True)  # Sort by score (highest first)
                    
                    # Keep only top 10
                    combined = combined[:10] if len(combined) > 10 else combined
                    
                    # Update high scores
                    high_scores["vs_mode"][player_type]["scores"] = [item[0] for item in combined]
                    high_scores["vs_mode"][player_type]["dates"] = [item[1] for item in combined]
                    modified = True
        
        # Then handle the legacy "vs" format and merge with vs_mode
        if "vs" in high_scores:
            # Create vs_mode if it doesn't exist
            if "vs_mode" not in high_scores:
                high_scores["vs_mode"] = {
                    "player": {"scores": [], "dates": []},
                    "ai": {"scores": [], "dates": []},
                    "matches": []
                }
            
            # Ensure all player types exist in vs_mode
            for player_type in ["player", "ai"]:
                if player_type not in high_scores["vs_mode"]:
                    high_scores["vs_mode"][player_type] = {"scores": [], "dates": []}
                
                # Also ensure the scores and dates keys exist
                if "scores" not in high_scores["vs_mode"][player_type]:
                    high_scores["vs_mode"][player_type]["scores"] = []
                if "dates" not in high_scores["vs_mode"][player_type]:
                    high_scores["vs_mode"][player_type]["dates"] = []
                
                # Now proceed with the migration
                if player_type in high_scores["vs"] and "scores" in high_scores["vs"][player_type]:
                    vs_scores = high_scores["vs"][player_type]["scores"]
                    vs_dates = high_scores["vs"][player_type].get("dates", [])
                    
                    # If dates are missing, create placeholder dates
                    while len(vs_dates) < len(vs_scores):
                        vs_dates.append(datetime.datetime.now().strftime("%Y-%m-%d"))
                    
                    # Merge with vs_mode scores
                    new_scores = high_scores["vs_mode"][player_type]["scores"] + vs_scores
                    new_dates = high_scores["vs_mode"][player_type]["dates"] + vs_dates
                    
                    # Sort combined scores
                    combined = list(zip(new_scores, new_dates))
                    combined.sort(key=lambda x: x[0], reverse=True)  # Sort by score
                    
                    # Keep only top 10
                    combined = combined[:10] if len(combined) > 10 else combined
                    
                    # Update vs_mode
                    high_scores["vs_mode"][player_type]["scores"] = [item[0] for item in combined]
                    high_scores["vs_mode"][player_type]["dates"] = [item[1] for item in combined]
                    modified = True
            
            # Remove the legacy "vs" key after migration
            del high_scores["vs"]
            modified = True
        
        # Create backward compatibility by copying vs_mode back to vs
        # Fix VS mode duplication - only copy if destination is empty
        if "vs_mode" in high_scores and "vs" not in high_scores:
            high_scores["vs"] = {
                "player": {"scores": [], "dates": []},
                "ai": {"scores": [], "dates": []}
            }
            
            for player_type in ["player", "ai"]:
                if player_type in high_scores["vs_mode"] and not high_scores["vs"][player_type].get("scores", []):
                    high_scores["vs"][player_type]["scores"] = high_scores["vs_mode"][player_type].get("scores", [])
                    high_scores["vs"][player_type]["dates"] = high_scores["vs_mode"][player_type].get("dates", [])
            
            modified = True
        
        # Save the updated high scores
        if modified:
            with open(HIGHSCORE_FILE, 'w') as f:
                json.dump(high_scores, f, indent=4)
            print("Successfully resorted all high scores")
        
        return high_scores
    except Exception as e:
        print(f"Error resorting high scores: {e}")
        import traceback
        traceback.print_exc()
        return load_high_scores()  # Return original if error
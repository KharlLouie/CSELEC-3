def convert_grade_to_gpa(grade):
    """Convert grade to GPA using Philippine scale"""       
    if grade >= 96: return 1.00
    elif grade >= 93: return 1.25
    elif grade >= 90: return 1.50
    elif grade >= 87: return 1.75
    elif grade >= 84: return 2.00
    elif grade >= 80: return 2.25
    elif grade >= 78: return 2.50
    elif grade >= 76: return 2.75
    elif grade == 75: return 3.00
    else: return 5.00

def calculate_weighted_average(grades_list, units_list):
    """Calculate raw weighted average"""
    if not grades_list or len(grades_list) != len(units_list):
        return 0.0
    
    valid_units = [u if isinstance(u, (int, float)) and u > 0 else 0 
                  for u in units_list]
    
    weighted_sum = sum(g * u for g, u in zip(grades_list, valid_units))
    total_units = sum(valid_units)
    return weighted_sum / total_units if total_units > 0 else 0.0
# length in minutes
break_15_minutes = 15
meal_30_minutes = 30

# break requirements based on shift length (in hours)
break_rules = {
    # key is minumum shift duration in hours
    4: {'15': 1, '30': 0},
    6: {'15': 1, '30': 1},
    8: {'15': 2, '30': 1}
}
#temporary fake database (will become db.py later)

def get_query1():
    # fake data – later this will come from SQLite
    return [
        ("value1", "value2", "value3"),
        ("other1", "other2", "other3"),
        ("more1", "more2", "more3"),
    ]

def get_query2():
    return [
        (1, "Alice", 10.5),
        (2, "Bruno", 20.0),
        (3, "Carla", 30.75),
    ]

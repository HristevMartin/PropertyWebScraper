import os

db_config = {
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "pass"),
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "estate_buildings_uk"),
}

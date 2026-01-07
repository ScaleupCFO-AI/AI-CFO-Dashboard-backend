import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
ENV = os.getenv("ENV")

print("ENV:", ENV)
print("DATABASE_URL loaded:", DATABASE_URL is not None)

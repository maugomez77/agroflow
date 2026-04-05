"""Vercel serverless entry point for AgroFlow FastAPI backend."""

from agroflow.api import app
from agroflow.demo import generate_demo_data
from agroflow.store import Store

# Auto-load demo data if store is empty
store = Store()
data = store.load()
if not data.get("farms"):
    generate_demo_data()

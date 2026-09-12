"""API local do Cypher.

Execute com: uvicorn main:app --reload --port 8000
"""

try:
    from .app.factory import create_app, startup
except ImportError:
    from app.factory import create_app, startup


app = create_app()

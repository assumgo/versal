import os

# Only tests receive this non-production key; normal startup requires configuration.
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-with-at-least-32-characters")

import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lanchonete.db")
TOKEN_SECRET = os.getenv("TOKEN_SECRET", "dev-only-change-this-secret-before-deploy")
TOKEN_TTL_SECONDS = int(os.getenv("TOKEN_TTL_SECONDS", "3600"))
SEED_ADMIN_EMAIL = os.getenv("SEED_ADMIN_EMAIL", "admin@example.com").lower()
SEED_ADMIN_NAME = os.getenv("SEED_ADMIN_NAME", "Administrador Demo")
SEED_ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "TroqueEstaSenha123!")

if len(TOKEN_SECRET) < 32:
    raise RuntimeError("TOKEN_SECRET precisa ter pelo menos 32 caracteres.")


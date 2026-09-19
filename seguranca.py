import secrets
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash


BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"

DATABASE_DIR.mkdir(exist_ok=True)

SECRET_KEY_FILE = DATABASE_DIR / "system.key"


def carregar_secret_key():
    if SECRET_KEY_FILE.exists():
        chave = SECRET_KEY_FILE.read_text(
            encoding="utf-8"
        ).strip()

        if chave:
            return chave

    chave = secrets.token_hex(64)

    SECRET_KEY_FILE.write_text(
        chave,
        encoding="utf-8"
    )

    return chave


# ============================================================
# CHAVE MASTER
# ============================================================

# python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('SUA_CHAVE_AQUI'))"

MASTER_ACTIVATION_HASH = "scrypt:32768:8:1$Z1VHL7Ys59Gtif9E$23c88748b9dd9b9ba186c07cf4b8a2776a03fb41b64c3999044e78b260a26a4b9a9a484cb371768604a4b6c11e40cd98cea712ac2e7f5b6447b09847ba7d9457"


def validar_chave_master(chave):
    if not MASTER_ACTIVATION_HASH:
        return False

    if MASTER_ACTIVATION_HASH.startswith("COLE_AQUI"):
        return False

    return check_password_hash(
        MASTER_ACTIVATION_HASH,
        chave
    )


def criar_hash_senha(senha):
    return generate_password_hash(senha)
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


MASTER_ACTIVATION_HASH = "scrypt:32768:8:1$iVXFsSXPTNNB9EUs$a113790115594f32608057d7be1c849eeb246a8d0a9850f62a580fe1eb6877132798e3589d1bf7d81b007d92a04d236128439536f44ae2b6f60bae185993cca3"


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
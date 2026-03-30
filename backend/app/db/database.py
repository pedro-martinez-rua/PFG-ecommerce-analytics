from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# create_engine crea la conexión con PostgreSQL.
# El pool_pre_ping=True verifica que la conexión sigue viva antes de usarla.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# SessionLocal es la fábrica de sesiones. Cada request abre una sesión,
# hace sus operaciones, y la cierra. Equivale al EntityManager de Java.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base es la clase de la que heredan todos los modelos.
# Equivale a @Entity en Java — registra las tablas en SQLAlchemy.
Base = declarative_base()

def get_db():
    """
    Generador que abre una sesión por request y la cierra al terminar.
    Se usa como dependencia en los endpoints (equivale a @Autowired en Spring).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
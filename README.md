python -c "from app.database import Base; import app.models; print('MODEL TABLES:',sorted(Base.metadata.tables.keys()))"

python -m alembic revision --autogenerate -m "add sites guards attendance and system settings"

python -m alembic upgrade head

python -c "from sqlalchemy import inspect; from app.database import get_engine; i=inspect(get_engine()); print('TABLES:'); [print('-',x) for x in i.get_table_names()]"

python -c "from app.main import app; [print(','.join(sorted(r.methods or [])), r.path) for r in app.routes if hasattr(r,'methods')]"

# python -m uvicorn app.main:app --host 0.0.0.0 --port 8200 --reload

# node .\node_modules\next\dist\bin\next build

# node .\node_modules\next\dist\bin\next dev --hostname 0.0.0.0 --port 3300
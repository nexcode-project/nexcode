import os
from sqlalchemy import create_engine, text

# 从环境变量或配置文件获取数据库 URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/nexcode")

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        conn.commit()
    print("Successfully deleted alembic_version table")
except Exception as e:
    print(f"Error: {e}") 
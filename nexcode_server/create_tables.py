from sqlalchemy import create_engine
from app.models.database import Base

# 创建引擎
engine = create_engine("postgresql://postgres@localhost/nexcode")

# 创建所有表
Base.metadata.create_all(engine)
print("Tables created successfully")

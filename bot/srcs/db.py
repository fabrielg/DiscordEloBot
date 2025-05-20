from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base
import os
# Create the engine — replace `user`, `password`, `localhost`, `dbname`

user = os.getenv('POSTGRES_USER')
password = os.getenv('POSTGRES_PASSWORD')
host = "postgres"
dbname = os.getenv('POSTGRES_DB')

engine = create_engine(f'postgresql+psycopg2://{user}:{password}@{host}/{dbname}', echo=True)

# Session and Base setup
session_factory = sessionmaker(bind=engine)
db = scoped_session(session_factory)
Base = declarative_base()
Base.query = db.query_property()
Base.metadata.create_all(engine)
print("salut")
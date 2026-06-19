import os
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Boolean, event
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./unified_transit.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Enable foreign keys for SQLite
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String, nullable=False)

    journeys = relationship("Journey", back_populates="user", cascade="all, delete-orphan")
    vehicles = relationship("Vehicle", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")

class Journey(Base):
    __tablename__ = "journeys"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    from_stop = Column(String, nullable=False)
    to_stop = Column(String, nullable=False)
    mode = Column(String, nullable=False)
    cost = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    distance = Column(Float, nullable=False)
    date = Column(String, nullable=False)
    is_saved = Column(Boolean, default=False, nullable=False)
    custom_name = Column(String, nullable=True)

    user = relationship("User", back_populates="journeys")

class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    fuel_type = Column(String, nullable=False)  # Petrol, Diesel, EV, CNG
    efficiency = Column(Float, nullable=False)  # mileage

    user = relationship("User", back_populates="vehicles")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    doc_type = Column(String, nullable=False)  # licence, rc, insurance, puc
    doc_number = Column(String, nullable=False)
    expiry_date = Column(String, nullable=False)  # YYYY-MM-DD
    file_path = Column(String, nullable=False)

    user = relationship("User", back_populates="documents")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

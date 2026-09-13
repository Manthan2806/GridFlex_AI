from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


DATABASE_URL = "sqlite:///./gridflex.db"

# SQLite needs this option because FastAPI can handle requests in different threads.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class EVResource(Base):
    __tablename__ = "ev_resources"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    rated_power_kw: Mapped[float] = mapped_column(Float, nullable=False)
    required_kwh: Mapped[float] = mapped_column(Float, nullable=False)
    availability_rate: Mapped[float] = mapped_column(Float, nullable=False)
    override_rate: Mapped[float] = mapped_column(Float, nullable=False)


class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    run_id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    total_dispatched_kw: Mapped[float] = mapped_column(Float, nullable=False)
    total_delivered_kw: Mapped[float] = mapped_column(Float, nullable=False)
    results_json: Mapped[str] = mapped_column(Text, nullable=False)

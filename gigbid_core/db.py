import json
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, Float, Integer, String, Text, create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from gigbid_core.config import ROOT, settings

(ROOT / "data/runtime").mkdir(parents=True, exist_ok=True)
Base = declarative_base()
url = settings().database_url
if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
    url = "sqlite:///" + str(ROOT / url.removeprefix("sqlite:///"))
engine = create_engine(
    url,
    connect_args={"check_same_thread": False, "timeout": 30} if url.startswith("sqlite") else {},
    pool_pre_ping=True,
)
if url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def configure_sqlite(connection, _):
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")


Session = sessionmaker(engine, expire_on_commit=False)


def now():
    return datetime.now(timezone.utc).isoformat()


def uid():
    return str(uuid4())


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=uid)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    profile = Column(Text, default="{}")


class Record(Base):
    __tablename__ = "records"
    key = Column(String, primary_key=True)
    tenant = Column(String, index=True, nullable=False)
    kind = Column(String, index=True, nullable=False)
    record_id = Column(String, nullable=False)
    payload = Column(Text, nullable=False)
    updated = Column(String, default=now)


class Run(Base):
    __tablename__ = "runs"
    id = Column(String, primary_key=True, default=uid)
    tenant = Column(String, index=True, nullable=False)
    job_id = Column(String, nullable=False)
    kind = Column(String, default="bid")
    status = Column(String, default="queued")
    state = Column(Text, default="{}")
    error = Column(Text, default="")
    created = Column(String, default=now)
    updated = Column(String, default=now)


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant = Column(String, index=True, nullable=False)
    run_id = Column(String, index=True, nullable=False)
    node = Column(String, nullable=False)
    payload = Column(Text, nullable=False)
    created = Column(String, default=now)


class Effect(Base):
    __tablename__ = "effects"
    key = Column(String, primary_key=True)
    tenant = Column(String, nullable=False)
    request_hash = Column(String, nullable=False)
    result = Column(Text, nullable=False)
    cost = Column(Float, default=0)
    created = Column(String, default=now)


class Audit(Base):
    __tablename__ = "audit"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant = Column(String, nullable=False)
    trace_id = Column(String, nullable=False)
    tool = Column(String, nullable=False)
    payload = Column(Text, nullable=False)
    created = Column(String, default=now)


@contextmanager
def db():
    with Session.begin() as session:
        yield session


def init_db():
    Base.metadata.create_all(engine)


def put(session, tenant, kind, record_id, payload):
    key = f"{tenant}:{kind}:{record_id}"
    item = session.get(Record, key)
    if item:
        item.payload, item.updated = json.dumps(payload), now()
    else:
        session.add(
            Record(key=key, tenant=tenant, kind=kind, record_id=record_id, payload=json.dumps(payload))
        )


def get(session, tenant, kind, record_id):
    item = session.get(Record, f"{tenant}:{kind}:{record_id}")
    return json.loads(item.payload) if item else None


def records(session, tenant, kind):
    return [json.loads(x.payload) for x in session.query(Record).filter_by(tenant=tenant, kind=kind).all()]

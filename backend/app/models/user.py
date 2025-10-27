import os
from datetime import datetime
from fastapi_users_db_sqlalchemy import (
    SQLAlchemyBaseUserTable,
    SQLAlchemyBaseUserTableUUID,
    SQLAlchemyUserDatabase,
)
from sqlalchemy import Boolean, Column, DateTime, Integer, String, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from fastapi_users import schemas
from fastapi import Depends
from collections.abc import AsyncGenerator

Base = declarative_base()


class User(SQLAlchemyBaseUserTable[int], Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    custom_discount: Mapped[float] = mapped_column(Float, nullable=True, default=None)

    credit = relationship("UserCredit", back_populates="user", uselist=False)
    transactions = relationship("Transaction", back_populates="user")


class UserCredit(Base):
    __tablename__ = "user_credit"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), primary_key=True, index=True
    )
    credits: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user = relationship("User", back_populates="credit")


class Transaction(Base):
    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False, index=True
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    data_id: Mapped[str] = mapped_column(String, nullable=True)

    user = relationship("User", back_populates="transactions")


class UserToken(Base):
    __tablename__ = "user_token"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), primary_key=True, index=True
    )
    token: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class DataPool(Base):
    __tablename__ = "data_pool"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    data: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    sold_record = relationship(
        "DataPoolSold", back_populates="pool_item", uselist=False
    )


class DataPoolSold(Base):
    __tablename__ = "data_pool_sold"

    pool_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("data_pool.id"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False, index=True
    )
    sold_at = Column(DateTime, server_default=func.now(), nullable=False)

    pool_item = relationship("DataPool", back_populates="sold_record")
    user = relationship("User")


class UserRead(schemas.BaseUser[int]):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


engine = create_async_engine(os.getenv("DATABASE_URL"))
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)

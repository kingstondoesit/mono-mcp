"""
Simple database layer for storing webhook events and account data.
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import create_engine, func, inspect


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(primary_key=True)
    customer_id: Mapped[str]
    account_number: Mapped[str]
    account_name: Mapped[str]
    bank_name: Mapped[str]
    bank_code: Mapped[str]
    account_type: Mapped[str]
    currency: Mapped[str]
    bvn: Mapped[Optional[str]]
    status: Mapped[str] = mapped_column(default="active")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_type: Mapped[str]
    account_id: Mapped[Optional[str]]
    data: Mapped[str]
    processed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(primary_key=True)
    account_id: Mapped[str]
    amount: Mapped[int]
    type: Mapped[str]
    description: Mapped[Optional[str]]
    reference: Mapped[Optional[str]]
    date: Mapped[str]
    balance: Mapped[int]
    category: Mapped[Optional[str]]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class MonoBankingDB:
    """lightweight database for mono banking data"""

    def __init__(self, db_url: str, **kwargs: Any):
        try:
            db_engine = create_engine(db_url, **kwargs)
        except Exception as e:
            raise ValueError(
                f"Failed to create database engine for URL '{db_url}'"
            ) from e
        self.db_engine = db_engine
        self.database = sessionmaker(bind=self.db_engine)
        inspector = inspect(self.db_engine)
        existing_tables = inspector.get_table_names()

        if "accounts" not in existing_tables:
            Base.metadata.create_all(self.db_engine)
        if "webhook_events" not in existing_tables:
            Base.metadata.create_all(self.db_engine)
        if "transactions" not in existing_tables:
            Base.metadata.create_all(self.db_engine)

    def store_account(self, account_data: Dict[str, Any]) -> bool:
        """store or update account information"""
        try:
            with self.database() as db:
                account = db.get(Account, account_data.get("id"))
                if not account:
                    account = Account(**account_data)
                    db.add(account)
                else:
                    for key, value in account_data.items():
                        setattr(account, key, value)
                db.commit()
            return True
        except Exception as e:
            print(f"error storing account: {e}")
            return False
          
    def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """retrieve account by id"""
        try:
            with self.database() as db:
                account = db.get(Account, account_id)
                if account:
                    return {
                        "id": account.id,
                        "customer_id": account.customer_id,
                        "account_number": account.account_number,
                        "account_name": account.account_name,
                        "bank_name": account.bank_name,
                        "bank_code": account.bank_code,
                        "account_type": account.account_type,
                        "currency": account.currency,
                        "bvn": account.bvn,
                        "status": account.status,
                        "created_at": account.created_at,
                        "updated_at": account.updated_at,
                    }
                return None
        except Exception as e:
            print(f"error getting account: {e}")
            return None
          
    def store_webhook_event(
        self, event_type: str, account_id: str, data: Dict[str, Any]
    ) -> bool:
        """store webhook event for processing"""
        try:

            with self.database() as db:
                webhook_event = WebhookEvent(
                    event_type=event_type, account_id=account_id, data=json.dumps(data) 
                )
                db.add(webhook_event)
                db.commit()
            return True
        except Exception as e:
            print(f"error storing webhook event: {e}")
            return False
          
    def store_transactions(
        self, account_id: str, transactions: List[Dict[str, Any]]
    ) -> bool:
        """store transaction history"""
        try:
            with self.database() as db:
                for txn in transactions:
                    existing_txn = db.get(Transaction, txn.get("_id"))
                    if existing_txn:
                        existing_txn.account_id = account_id
                        existing_txn.amount = txn.get("amount")
                        existing_txn.type = txn.get("type")
                        existing_txn.description = txn.get("narration")
                        existing_txn.reference = txn.get("reference")
                        existing_txn.date = txn.get("date")
                        existing_txn.balance = txn.get("balance")
                        existing_txn.category = txn.get("category")
                    else:
                        transaction = Transaction(
                            id=txn.get("_id"),
                            account_id=account_id,
                            amount=txn.get("amount"),
                            type=txn.get("type"),
                            description=txn.get("narration"),
                            reference=txn.get("reference"),
                            date=txn.get("date"),
                            balance=txn.get("balance"),
                            category=txn.get("category"),
                        )
                        db.add(transaction)
                db.commit()
            return True
        except Exception as e:
            print(f"error storing transactions: {e}")
            return False
          
    def get_recent_transactions(
        self, account_id: str, limit: int = 10 
    ) -> List[Dict[str, Any]]:
        """get recent transactions from database"""
        try:
            with self.database() as db:
                transactions = (
                    db.query(Transaction)
                    .filter(Transaction.account_id == account_id)
                    .order_by(Transaction.date.desc())
                    .limit(limit)
                    .all()
                )

                return [
                    {
                        "id": txn.id,
                        "account_id": txn.account_id,
                        "amount": txn.amount,
                        "type": txn.type,
                        "description": txn.description,
                        "reference": txn.reference,
                        "date": txn.date,
                        "balance": txn.balance,
                        "category": txn.category,
                        "created_at": txn.created_at,
                    }
                    for txn in transactions
                ]
        except Exception as e:
            print(f"error getting transactions: {e}")
            return []

    def remove_account(self, account_id: str) -> bool:
        """remove account and related data"""
        try:
            with self.database() as db:
                account = db.get(Account, account_id)
                if account:
                    db.delete(account)

                transactions = (
                    db.query(Transaction)
                    .filter(Transaction.account_id == account_id)
                    .all()
                )
                for txn in transactions:
                    db.delete(txn)

                db.commit()
            return True
        except Exception as e:
            print(f"error removing account: {e}")
            return False

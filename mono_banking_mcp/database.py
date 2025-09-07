"""
Simple database layer for storing webhook events and account data.
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class MonoBankingDB:
    """lightweight database for mono banking data"""

    def __init__(self, db_path: str = "mono_banking.db"):
        self.db_path = Path(db_path)
        self.init_database()

    def init_database(self):
        """create tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    customer_id TEXT,
                    account_number TEXT,
                    account_name TEXT,
                    bank_name TEXT,
                    bank_code TEXT,
                    account_type TEXT,
                    currency TEXT,
                    bvn TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS webhook_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    account_id TEXT,
                    data TEXT NOT NULL,
                    processed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS transactions (
                    id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    amount INTEGER,
                    type TEXT,
                    description TEXT,
                    reference TEXT,
                    date TEXT,
                    balance INTEGER,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_webhook_events_type ON webhook_events(event_type);
                CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id);
            """
            )

    def store_account(self, account_data: Dict[str, Any]) -> bool:
        """store or update account information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO accounts 
                    (id, customer_id, account_number, account_name, bank_name, 
                     bank_code, account_type, currency, bvn, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        account_data.get("id"),
                        account_data.get("customer_id"),
                        account_data.get("account_number"),
                        account_data.get("account_name"),
                        account_data.get("bank_name"),
                        account_data.get("bank_code"),
                        account_data.get("account_type"),
                        account_data.get("currency"),
                        account_data.get("bvn"),
                        datetime.now().isoformat(),
                    ),
                )
            return True
        except Exception as e:
            print(f"error storing account: {e}")
            return False

    def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """retrieve account by id"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM accounts WHERE id = ?", (account_id,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"error getting account: {e}")
            return None

    def store_webhook_event(
        self, event_type: str, account_id: str, data: Dict[str, Any]
    ) -> bool:
        """store webhook event for processing"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO webhook_events (event_type, account_id, data)
                    VALUES (?, ?, ?)
                """,
                    (event_type, account_id, json.dumps(data)),
                )
            return True
        except Exception as e:
            print(f"error storing webhook event: {e}")
            return False

    def store_transactions(
        self, account_id: str, transactions: List[Dict[str, Any]]
    ) -> bool:
        """store transaction history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for txn in transactions:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO transactions 
                        (id, account_id, amount, type, description, reference, date, balance, category)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            txn.get("_id"),
                            account_id,
                            txn.get("amount"),
                            txn.get("type"),
                            txn.get("narration"),
                            txn.get("reference"),
                            txn.get("date"),
                            txn.get("balance"),
                            txn.get("category"),
                        ),
                    )
            return True
        except Exception as e:
            print(f"error storing transactions: {e}")
            return False

    def get_recent_transactions(
        self, account_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """get recent transactions from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT * FROM transactions 
                    WHERE account_id = ? 
                    ORDER BY date DESC 
                    LIMIT ?
                """,
                    (account_id, limit),
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"error getting transactions: {e}")
            return []

    def remove_account(self, account_id: str) -> bool:
        """remove account and related data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
                conn.execute(
                    "DELETE FROM transactions WHERE account_id = ?", (account_id,)
                )
            return True
        except Exception as e:
            print(f"error removing account: {e}")
            return False

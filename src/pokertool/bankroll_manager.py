#!/usr/bin/env python3
"""
Bankroll Manager
===============

Manages player bankroll tracking and limits.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Transaction:
    """Bankroll transaction record"""
    timestamp: datetime
    transaction_type: str  # deposit, withdrawal, win, loss
    amount: float
    balance_after: float
    description: str
    transaction_id: int


class BankrollManager:
    """Manages player bankroll."""

    def __init__(self, initial_balance: float = 0.0):
        """Initialize bankroll manager."""
        self.balance = initial_balance
        self.transactions: List[Transaction] = []
        self.transaction_count = 0
        self.buy_in_limit: Optional[float] = None

    def deposit(self, amount: float, description: str = "") -> Transaction:
        """Record a deposit."""
        self.balance += amount
        return self._record_transaction("deposit", amount, description)

    def withdraw(self, amount: float, description: str = "") -> Optional[Transaction]:
        """Record a withdrawal."""
        if amount > self.balance:
            logger.warning(f"Insufficient funds: {self.balance} < {amount}")
            return None
        self.balance -= amount
        return self._record_transaction("withdrawal", amount, description)

    def record_win(self, amount: float, description: str = "") -> Transaction:
        """Record winnings."""
        self.balance += amount
        return self._record_transaction("win", amount, description)

    def record_loss(self, amount: float, description: str = "") -> Transaction:
        """Record losses."""
        self.balance -= amount
        return self._record_transaction("loss", amount, description)

    def get_balance(self) -> float:
        """Get current balance."""
        return round(self.balance, 2)

    def set_buy_in_limit(self, limit: float):
        """Set maximum buy-in limit."""
        self.buy_in_limit = limit

    def can_buy_in(self, amount: float) -> bool:
        """Check if buy-in is allowed."""
        if amount > self.balance:
            return False
        if self.buy_in_limit and amount > self.buy_in_limit:
            return False
        return True

    def get_total_deposits(self) -> float:
        """Get total deposits."""
        total = sum(t.amount for t in self.transactions if t.transaction_type == "deposit")
        return round(total, 2)

    def get_total_withdrawals(self) -> float:
        """Get total withdrawals."""
        total = sum(t.amount for t in self.transactions if t.transaction_type == "withdrawal")
        return round(total, 2)

    def get_total_wins(self) -> float:
        """Get total winnings."""
        total = sum(t.amount for t in self.transactions if t.transaction_type == "win")
        return round(total, 2)

    def get_total_losses(self) -> float:
        """Get total losses."""
        total = sum(t.amount for t in self.transactions if t.transaction_type == "loss")
        return round(total, 2)

    def get_net_profit(self) -> float:
        """Calculate net profit/loss."""
        wins = self.get_total_wins()
        losses = self.get_total_losses()
        return round(wins - losses, 2)

    def get_roi(self) -> float:
        """Calculate ROI percentage."""
        deposits = self.get_total_deposits()
        if deposits == 0:
            return 0.0
        net_profit = self.get_net_profit()
        return round((net_profit / deposits) * 100, 2)

    def get_statistics(self) -> Dict[str, any]:
        """Get comprehensive bankroll statistics."""
        return {
            "current_balance": self.get_balance(),
            "total_transactions": len(self.transactions),
            "total_deposits": self.get_total_deposits(),
            "total_withdrawals": self.get_total_withdrawals(),
            "total_wins": self.get_total_wins(),
            "total_losses": self.get_total_losses(),
            "net_profit": self.get_net_profit(),
            "roi_percent": self.get_roi(),
            "buy_in_limit": self.buy_in_limit
        }

    def get_recent_transactions(self, limit: int = 10) -> List[Transaction]:
        """Get recent transactions."""
        return self.transactions[-limit:]

    def reset(self, keep_balance: bool = False):
        """Reset transaction history."""
        if not keep_balance:
            self.balance = 0.0
        self.transactions.clear()
        self.transaction_count = 0

    def _record_transaction(
        self,
        transaction_type: str,
        amount: float,
        description: str
    ) -> Transaction:
        """Internal method to record transaction."""
        self.transaction_count += 1
        transaction = Transaction(
            timestamp=datetime.now(),
            transaction_type=transaction_type,
            amount=amount,
            balance_after=self.balance,
            description=description,
            transaction_id=self.transaction_count
        )
        self.transactions.append(transaction)
        logger.debug(f"Recorded {transaction_type}: ${amount}, balance: ${self.balance}")
        return transaction


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    manager = BankrollManager(1000.0)

    manager.deposit(500.0, "Initial deposit")
    manager.record_win(150.0, "Tournament win")
    manager.record_loss(75.0, "Cash game loss")

    stats = manager.get_statistics()
    print(f"\nBankroll Statistics:")
    print(f"  Balance: ${stats['current_balance']}")
    print(f"  Net profit: ${stats['net_profit']}")
    print(f"  ROI: {stats['roi_percent']}%")

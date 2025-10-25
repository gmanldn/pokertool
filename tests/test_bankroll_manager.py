#!/usr/bin/env python3
"""Tests for Bankroll Manager"""

import pytest
from src.pokertool.bankroll_manager import BankrollManager


class TestBankrollManager:
    """Test suite for BankrollManager"""

    def test_initialization(self):
        """Test manager initialization"""
        manager = BankrollManager(1000.0)
        assert manager.balance == 1000.0
        assert len(manager.transactions) == 0

    def test_deposit(self):
        """Test deposit"""
        manager = BankrollManager(100.0)
        transaction = manager.deposit(50.0, "Test deposit")

        assert manager.get_balance() == 150.0
        assert transaction.amount == 50.0
        assert transaction.transaction_type == "deposit"

    def test_withdraw(self):
        """Test withdrawal"""
        manager = BankrollManager(100.0)
        transaction = manager.withdraw(30.0, "Test withdrawal")

        assert manager.get_balance() == 70.0
        assert transaction.amount == 30.0

    def test_withdraw_insufficient_funds(self):
        """Test withdrawal with insufficient funds"""
        manager = BankrollManager(50.0)
        transaction = manager.withdraw(100.0)

        assert transaction is None
        assert manager.get_balance() == 50.0

    def test_record_win(self):
        """Test recording win"""
        manager = BankrollManager(100.0)
        manager.record_win(75.0, "Tournament win")

        assert manager.get_balance() == 175.0

    def test_record_loss(self):
        """Test recording loss"""
        manager = BankrollManager(100.0)
        manager.record_loss(25.0, "Cash game loss")

        assert manager.get_balance() == 75.0

    def test_set_buy_in_limit(self):
        """Test setting buy-in limit"""
        manager = BankrollManager(1000.0)
        manager.set_buy_in_limit(100.0)

        assert manager.buy_in_limit == 100.0

    def test_can_buy_in_success(self):
        """Test can buy-in when allowed"""
        manager = BankrollManager(1000.0)
        manager.set_buy_in_limit(200.0)

        assert manager.can_buy_in(150.0) is True

    def test_can_buy_in_exceeds_limit(self):
        """Test can buy-in when exceeds limit"""
        manager = BankrollManager(1000.0)
        manager.set_buy_in_limit(100.0)

        assert manager.can_buy_in(150.0) is False

    def test_can_buy_in_insufficient_balance(self):
        """Test can buy-in with insufficient balance"""
        manager = BankrollManager(50.0)

        assert manager.can_buy_in(100.0) is False

    def test_total_deposits(self):
        """Test total deposits calculation"""
        manager = BankrollManager()
        manager.deposit(100.0)
        manager.deposit(200.0)
        manager.deposit(150.0)

        assert manager.get_total_deposits() == 450.0

    def test_total_withdrawals(self):
        """Test total withdrawals calculation"""
        manager = BankrollManager(1000.0)
        manager.withdraw(100.0)
        manager.withdraw(50.0)

        assert manager.get_total_withdrawals() == 150.0

    def test_total_wins(self):
        """Test total wins calculation"""
        manager = BankrollManager()
        manager.record_win(100.0)
        manager.record_win(150.0)

        assert manager.get_total_wins() == 250.0

    def test_total_losses(self):
        """Test total losses calculation"""
        manager = BankrollManager(1000.0)
        manager.record_loss(50.0)
        manager.record_loss(75.0)

        assert manager.get_total_losses() == 125.0

    def test_net_profit_positive(self):
        """Test net profit calculation (profit)"""
        manager = BankrollManager()
        manager.record_win(200.0)
        manager.record_loss(75.0)

        assert manager.get_net_profit() == 125.0

    def test_net_profit_negative(self):
        """Test net profit calculation (loss)"""
        manager = BankrollManager(1000.0)
        manager.record_win(50.0)
        manager.record_loss(100.0)

        assert manager.get_net_profit() == -50.0

    def test_roi_calculation(self):
        """Test ROI calculation"""
        manager = BankrollManager()
        manager.deposit(100.0)
        manager.record_win(50.0)
        manager.record_loss(20.0)

        # Net profit: 30, ROI: 30/100 = 30%
        assert manager.get_roi() == 30.0

    def test_roi_no_deposits(self):
        """Test ROI with no deposits"""
        manager = BankrollManager()
        assert manager.get_roi() == 0.0

    def test_statistics(self):
        """Test comprehensive statistics"""
        manager = BankrollManager(100.0)
        manager.deposit(500.0)
        manager.record_win(150.0)
        manager.record_loss(50.0)
        manager.withdraw(100.0)

        stats = manager.get_statistics()

        assert stats["current_balance"] == 600.0
        assert stats["total_deposits"] == 500.0
        assert stats["net_profit"] == 100.0

    def test_recent_transactions(self):
        """Test getting recent transactions"""
        manager = BankrollManager()
        for i in range(15):
            manager.deposit(10.0)

        recent = manager.get_recent_transactions(limit=5)
        assert len(recent) == 5

    def test_reset_with_balance(self):
        """Test reset keeping balance"""
        manager = BankrollManager(1000.0)
        manager.deposit(500.0)

        manager.reset(keep_balance=True)

        assert manager.get_balance() == 1500.0
        assert len(manager.transactions) == 0

    def test_reset_clear_all(self):
        """Test reset clearing everything"""
        manager = BankrollManager(1000.0)
        manager.deposit(500.0)

        manager.reset(keep_balance=False)

        assert manager.get_balance() == 0.0
        assert len(manager.transactions) == 0

    def test_transaction_id_increment(self):
        """Test transaction IDs increment"""
        manager = BankrollManager()
        t1 = manager.deposit(100.0)
        t2 = manager.record_win(50.0)
        t3 = manager.record_loss(25.0)

        assert t1.transaction_id == 1
        assert t2.transaction_id == 2
        assert t3.transaction_id == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

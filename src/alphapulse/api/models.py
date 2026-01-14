"""
SQLAlchemy database models for AlphaPulse.

Critical: All monetary values use DECIMAL/NUMERIC types, not FLOAT,
to ensure exact decimal precision for financial calculations.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DECIMAL, Column, DateTime, Enum, Index, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Price(Base):
    """
    Price data model with DECIMAL precision for financial calculations.

    Uses DECIMAL(20, 8) for price and volume to support:
    - Up to 999,999,999.99999999 (12 integer digits, 8 decimal places)
    - Exact decimal representation (no floating-point errors)
    """

    __tablename__ = "prices"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    price = Column(DECIMAL(20, 8), nullable=False)  # DECIMAL precision for price
    volume = Column(DECIMAL(20, 8), nullable=False)  # DECIMAL precision for volume
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Composite index for efficient time-series queries
    __table_args__ = (Index("idx_prices_symbol_timestamp", "symbol", "timestamp"),)

    def __repr__(self):
        return f"<Price(symbol='{self.symbol}', price={self.price}, timestamp={self.timestamp})>"

    def to_dict(self):
        """Convert model to dictionary with Decimal serialization."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "price": str(self.price) if self.price is not None else None,
            "volume": str(self.volume) if self.volume is not None else None,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TradingSignal(Base):
    """
    Trading signal model with DECIMAL precision for confidence scores.

    Uses DECIMAL(5, 4) for confidence to support:
    - Range: 0.0000 to 1.0000
    - 4 decimal places precision for confidence scores
    """

    __tablename__ = "trading_signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    signal_type = Column(
        Enum("BUY", "SELL", "HOLD", name="signal_type_enum"), nullable=False
    )
    confidence = Column(DECIMAL(5, 4), nullable=False)  # 0.0000 to 1.0000
    price_at_signal = Column(
        DECIMAL(20, 8), nullable=True
    )  # Optional price at signal time
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Composite index for efficient signal queries
    __table_args__ = (
        Index("idx_signals_symbol_timestamp", "symbol", "timestamp"),
        Index("idx_signals_type_timestamp", "signal_type", "timestamp"),
    )

    def __repr__(self):
        return f"<TradingSignal(symbol='{self.symbol}', type='{self.signal_type}', confidence={self.confidence})>"

    def to_dict(self):
        """Convert model to dictionary with Decimal serialization."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "signal_type": self.signal_type,
            "confidence": str(self.confidence) if self.confidence is not None else None,
            "price_at_signal": (
                str(self.price_at_signal) if self.price_at_signal is not None else None
            ),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TechnicalIndicator(Base):
    """
    Technical indicator model with DECIMAL precision for all values.

    Uses appropriate DECIMAL precision for different indicator types:
    - Price-based: DECIMAL(20, 8)
    - Percentage-based: DECIMAL(10, 6)
    - Ratio-based: DECIMAL(10, 4)
    """

    __tablename__ = "technical_indicators"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)

    # Trend indicators
    sma_20 = Column(DECIMAL(20, 8), nullable=True)
    ema_12 = Column(DECIMAL(20, 8), nullable=True)

    # Momentum indicators
    rsi_14 = Column(DECIMAL(10, 4), nullable=True)  # 0.0000 to 100.0000
    macd = Column(DECIMAL(20, 8), nullable=True)
    macd_signal = Column(DECIMAL(20, 8), nullable=True)
    macd_histogram = Column(DECIMAL(20, 8), nullable=True)

    # Volatility indicators
    bb_upper = Column(DECIMAL(20, 8), nullable=True)
    bb_middle = Column(DECIMAL(20, 8), nullable=True)
    bb_lower = Column(DECIMAL(20, 8), nullable=True)
    atr_14 = Column(DECIMAL(20, 8), nullable=True)

    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Composite index
    __table_args__ = (Index("idx_indicators_symbol_timestamp", "symbol", "timestamp"),)

    def __repr__(self):
        return (
            f"<TechnicalIndicator(symbol='{self.symbol}', timestamp={self.timestamp})>"
        )

    def to_dict(self):
        """Convert model to dictionary with Decimal serialization."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "sma_20": str(self.sma_20) if self.sma_20 is not None else None,
            "ema_12": str(self.ema_12) if self.ema_12 is not None else None,
            "rsi_14": str(self.rsi_14) if self.rsi_14 is not None else None,
            "macd": str(self.macd) if self.macd is not None else None,
            "macd_signal": (
                str(self.macd_signal) if self.macd_signal is not None else None
            ),
            "macd_histogram": (
                str(self.macd_histogram) if self.macd_histogram is not None else None
            ),
            "bb_upper": str(self.bb_upper) if self.bb_upper is not None else None,
            "bb_middle": str(self.bb_middle) if self.bb_middle is not None else None,
            "bb_lower": str(self.bb_lower) if self.bb_lower is not None else None,
            "atr_14": str(self.atr_14) if self.atr_14 is not None else None,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

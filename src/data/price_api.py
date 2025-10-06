from __future__ import annotations
from datetime import datetime
from typing import  Dict, Optional,  Any

import numpy as np
import pandas as pd

from vnstock import Quote

import talib

class PriceAPI:
    """
    Enhanced VN Stock API
    """

    def __init__(self, symbol: str, source: str = "VCI") -> None:
        self.symbol = symbol
        self.source = source
        # Khởi tạo Quote, phòng thủ nếu lỗi
        try:
            self._quote = Quote(symbol=symbol, source=source)
        except Exception:
            self._quote = None

    # ================= Price & Index =================
    def get_price_history(
        self,
        start: str = "2022-01-01",
        end: Optional[str] = None,
        interval: str = "1D",
        add_tech: bool = False,
    ) -> pd.DataFrame:
        # Phòng thủ nếu _quote chưa có
        if self._quote is None:
            try:
                self._quote = Quote(symbol=self.symbol, source=self.source)
            except Exception as e:
                raise RuntimeError(f"Không khởi tạo được Quote cho {self.symbol}: {e}")

        df = self._quote.history(start=start, end=end, interval=interval)
        if df is None or df.empty:
            return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])

        # Chuẩn hóa cột
        rename_map = {
            "time": "time",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}).copy()
        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"])
            df = df.sort_values("time").reset_index(drop=True)

        if add_tech:
            try:
                close = df["close"].astype(float).values
                high = df["high"].astype(float).values
                low = df["low"].astype(float).values
                vol = df["volume"].astype(float).values

                df["MA20"] = pd.Series(talib.SMA(close, timeperiod=20))
                df["RSI14"] = pd.Series(talib.RSI(close, timeperiod=14))
                macd, macds, macdh = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
                df["MACD"] = macd
                df["MACD_signal"] = macds
                df["ATR14"] = pd.Series(talib.ATR(high, low, close, timeperiod=14))
            except Exception:
                pass

        return df

    def get_enhanced_price_history(
        self,
        start: str = "2021-01-01",
        end: Optional[str] = None,
        interval: str = "1D",
    ) -> pd.DataFrame:
        df = self.get_price_history(start=start, end=end, interval=interval, add_tech=True).round(2)
        df['time'] = df['time'].dt.strftime('%Y-%m-%d')
        return df

    # ============ Gói dữ liệu cho AI ============
    def get_index_history(self,
                          index_symbol: str = "VNINDEX",
                          start: str = "2024-06-01",
                          end: Optional[str] = None,
                          interval: str = "1D") -> pd.DataFrame:
        
        from vnstock import Quote as _Quote
        idx_quote = _Quote(symbol=index_symbol)
        if end is None:
            end = datetime.now().strftime("%Y-%m-%d")
        df = idx_quote.history(start=start, end=end, interval=interval)

        return df.sort_values("time", ascending=False)
    def get_comprehensive_analysis(
        self,
        start: str = "2022-06-01",
        end: Optional[str] = None,
        interval: str = "1D",
    ) -> Dict[str, Any]:
        df = self.get_enhanced_price_history(start=start, end=end, interval=interval)
        ts = datetime.now().strftime("%Y-%m-%d")

        if df.empty:
            return {
                "timestamp": ts,
                "technical_summary": {"latest_close": 0},
                "moving_averages": {},
                "volume_analysis": {},
                "support_resistance": {},
                "fibonacci": {},
                "patterns": {},
                "divergences": {},
                "data_quality": {"price_data_points": 0, "completeness_score": 0.0},
            }

        close = df["close"].astype(float)
        high = df["high"].astype(float)
        low = df["low"].astype(float)
        volume = df["volume"].astype(float)

        # Indicators
        rsi = (talib.RSI(close.values, timeperiod=14)).round(2)
        macd, macds, macdh = talib.MACD(close.values, fastperiod=12, slowperiod=26, signalperiod=9)
        atr = (talib.ATR(high.values, low.values, close.values, timeperiod=14)).round(2)
        try:
            adx = (talib.ADX(high.values, low.values, close.values, timeperiod=14)).round(2)
            adx_latest = float(adx[-1]) if not np.isnan(adx[-1]) else None
        except Exception:
            adx_latest = None

        latest_close = float(close.iloc[-1])
        latest_volume = int(volume.iloc[-1])

        # Moving averages
        def ma(series, n):
            return float(pd.Series(series).rolling(n).mean().iloc[-1])

        ma5 = ma(close, 5)
        ma20 = ma(close, 20)
        ma50 = ma(close, 50)
        ma100 = ma(close, 100)
        ma200 = ma(close, 200)
        p_vs_ma20 = round((latest_close / ma20 - 1) * 100, 2) if ma20 else None
        p_vs_ma50 = round((latest_close / ma50 - 1) * 100, 2) if ma50 else None

        # Volume analysis
        vol_ma20 = float(pd.Series(volume).rolling(20).mean().iloc[-1])
        vol_ratio = round(latest_volume / vol_ma20, 2) if vol_ma20 else None
        obv = pd.Series(np.sign(close.diff().fillna(0)) * volume).cumsum()
        obv_latest = float(obv.iloc[-1])
        obv_trend = "Up" if obv.diff().tail(5).mean() > 0 else "Down"
        ad_trend = obv_trend
        mfi = None

        # Support/Resistance
        h = float(high.iloc[-1]); l = float(low.iloc[-1]); c = latest_close
        pivot = round((2*h + l + c) / 4, 2)
        r1 = round(2 * pivot - l, 2); s1 = round(2 * pivot - h, 2)
        r2 = round(pivot + (h - l), 2); s2 = round(pivot - (h - l), 2)
        dyn_support = float(low.rolling(20).min().iloc[-1])
        dyn_resistance = float(high.rolling(20).max().iloc[-1])

        # Fibonacci (50 phiên)
        sw = close.tail(50)
        swing_high = float(sw.max()); swing_low = float(sw.min())
        def fib(level): return round(swing_low + (swing_high - swing_low) * level, 2)
        fibs = {
            "swing_high": swing_high, "swing_low": swing_low,
            "23.6": fib(0.236), "38.2": fib(0.382), "50.0": fib(0.5), "61.8": fib(0.618), "78.6": fib(0.786),
            "127.2_ext": round(swing_high + (swing_high - swing_low) * 0.272, 2),
            "161.8_ext": round(swing_high + (swing_high - swing_low) * 0.618, 2),
            "261.8_ext": round(swing_high + (swing_high - swing_low) * 1.618, 2),
        }

        # Patterns & Divergences placeholders
        completeness = 1.0 if len(df) >= 200 else round(len(df) / 200, 2)

        return {
            "timestamp": ts,
            "technical_summary": {
                "latest_close": latest_close,
                "RSI14": float(rsi[-1]) if not np.isnan(rsi[-1]) else None,
                "MACD": float(macd[-1]) if not np.isnan(macd[-1]) else None,
                "SignalMACD": float(macds[-1]) if not np.isnan(macds[-1]) else None,
                "BB_position": None,
                "ATR14": float(atr[-1]) if not np.isnan(atr[-1]) else None,
                "ADX": adx_latest,
            },
            "moving_averages": {
                "MA5": ma5, "MA20": ma20, "MA50": ma50, "MA100": ma100, "MA200": ma200,
                "price_vs_MA20_pct": p_vs_ma20, "price_vs_MA50_pct": p_vs_ma50
            },
            "volume_analysis": {
                "latest_volume": latest_volume, "volume_ratio": vol_ratio, "volume_ma20": vol_ma20,
                "OBV_latest": obv_latest,
                "OBV_trend":  obv_trend,
                "AD":  ad_trend, "MFI14": mfi
            
            },
            "support_resistance": {
                "pivot": pivot, "S1": s1, "S2": s2, "R1": r1, "R2": r2,
                "dynamic_support": dyn_support, "dynamic_resistance": dyn_resistance
            },
            "fibonacci": fibs,
            "data_quality": {"price_data_points": int(len(df)), "completeness_score": completeness}
        }

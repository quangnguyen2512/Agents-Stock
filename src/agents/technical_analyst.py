"""
technical_analyst.py
--------------------
AI Technical Analyst for HOSE stocks, using raw data tables from PriceAPI to build analysis prompts and generate recommendations in a structured JSON format. Mirrors PEValuationAnalyst but focuses on technical indicators (RSI, MACD, MA, ATR, ADX, volume, support/resistance, Fibonacci).

Dependencies:
- vnstock
- talib
- google-generativeai

Core Components:
- MarketContext: Analysis context (symbol, current price, market data).
- AnalysisResponse: Standardized result object with recommendation, confidence, and JSON payload.
- TechnicalAnalyst: Agent for Gemini calls (async), prompt creation, and JSON parsing.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import asyncio
import json
import math

import pandas as pd

try:
    import google.generativeai as genai
except ImportError:
    genai = None


@dataclass
class MarketContext:
    """Market context used as input for AI analysis."""
    symbol: str
    current_price: Optional[float] = None
    market_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        self.symbol = self.symbol.upper().strip()


@dataclass
class AnalysisResponse:
    """Standardized analysis result for UI consumption."""
    recommendation: Optional[str] = None
    confidence_level: Optional[float] = None
    data_quality: Optional[float] = None
    key_points: Optional[List[str]] = None
    concerns: Optional[List[str]] = None
    content: Optional[Dict[str, Any]] = None


def make_json_serializable(obj: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
    """Recursively convert non-serializable types (e.g., Timestamp) in dict/list to JSON-friendly formats."""
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, pd.Timestamp) or isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def json_serializable_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert DataFrame to list of dicts with Timestamp converted to ISO string."""
    def convert_value(v: Any) -> Any:
        if isinstance(v, pd.Timestamp) or isinstance(v, datetime):
            return v.isoformat()
        return v

    records = df.to_dict(orient='records')
    for r in records:
        for k, v in r.items():
            r[k] = convert_value(v)
    return records


class TechnicalAnalyst:
    """
    AI Agent specialized in technical analysis.

    Responsibilities:
    - Compact raw data tables for prompts.
    - Generate structured prompts with bull/neutral/bear scenarios.
    - Call Gemini asynchronously and parse JSON responses into AnalysisResponse.
    """
    def __init__(self, apikey: str, model: str = "gemini-2.0-flash") -> None:
        if not genai:
            raise ImportError(
                "google-generativeai not installed. Install with: "
                "pip install google-generativeai"
            )
        self.apikey = apikey
        self.model = model
        genai.configure(api_key=apikey)
        self.client = genai.GenerativeModel(model)

    async def analyze(self, context: MarketContext) -> AnalysisResponse:
        """
        Perform technical analysis based on context's market_data.

        Steps:
        - Compact data.
        - Create prompt.
        - Call AI asynchronously.
        - Parse response.
        """
        data_for_ai = self._compact_market_data(context)
        prompt = self._create_prompt(data_for_ai)
        ai_text = await self._call_ai_async(prompt)
        return self._parse_response(ai_text)

    def _compact_market_data(self, context: MarketContext) -> Dict[str, Any]:
        """Compress raw data tables for prompt embedding, ensuring brevity and JSON serializability."""
        md = context.market_data or {}
        ts = md.get("timestamp", datetime.now().strftime("%Y-%m-%d"))

        # Raw data tables (compact to tail(100) and make JSON serializable)
        price_history = md.get("price_history")
        price_history_compact = (
            json_serializable_records(price_history.tail(200))
            if isinstance(price_history, pd.DataFrame) and not price_history.empty
            else []
        )

        comprehensive_analysis = make_json_serializable(md.get("comprehensive_analysis", {}))  # Recursive convert for safety

        index_history = md.get("index_history")
        index_history_compact = (
            json_serializable_records(index_history.tail(200))
            if isinstance(index_history, pd.DataFrame) and not index_history.empty
            else []
        )

        return {
            "symbol": context.symbol,
            "latest_price": context.current_price,
            "timestamp": ts,
            "price_history": price_history_compact,  # Raw enhanced price history (tail 100, serialized)
            "comprehensive_analysis": comprehensive_analysis,  # Raw comprehensive dict (serialized)
            "index_history": index_history_compact,  # Raw index history (tail 100, serialized)
        }

    def _create_prompt(self, data: Dict) -> str:
        """Tạo prompt phân tích chuyên sâu theo VSA và SEBA để đưa ra hành động tối ưu."""
        symbol = data.get("symbol", "N/A")
        latest_price = data.get("latest_price", "N/A")
        data_json = json.dumps(data, ensure_ascii=False, indent=2)

        prompt_template = f"""
        Bạn là một chuyên gia phân tích kỹ thuật cấp cao tại quỹ đầu tư lớn nhất Việt Nam, với hơn 20 năm kinh nghiệm phân tích cổ phiếu HOSE. Bạn chuyên sâu về VSA (Volume Spread Analysis) và phương pháp SEBA (Supply, Effort, Background, Action), tập trung vào việc phân tích sự mất cân bằng cung-cầu qua volume, spread, closing price, và price action để xác định hành động tối ưu.

        **Dữ liệu đầu vào:**
        - Mã cổ phiếu: {symbol}
        - Giá hiện tại: {latest_price} (nghìn VND)
        **Dữ liệu bảng lịch sử (compact và serialized):**
        {data_json}

        **Yêu cầu phân tích:**
        Thực hiện phân tích chuyên sâu và đưa ra kết luận theo VSA và SEBA. 
        Tập trung vào: 
        - Các điểm giá quan trọng (support/resistance, Fibonacci levels) và khối lượng (volume climaxes, spikes) kết hợp với hành động giá (price action như mô hình nến, spread rộng/hẹp).
        - Phân tích theo SEBA: Supply (cung cấp), Effort (nỗ lực mua/bán), Background (bối cảnh thị trường), Action (hành động tối ưu).
        - Đưa ra nhận định chuyên môn cao, kết luận về hành động tối ưu nhất (BUY/HOLD/SELL) với lý do chặt chẽ dựa trên dữ liệu.
        - Phân tích 3 kịch bản bull/neutral/bear với target price, probability, drivers, invalidations.
        - Xác định các mẫu hình đang hình thành tiềm năng (ví dụ: tam giác, cờ, cốc tay cầm, mô hình nến) và điều kiện xác nhận hoàn thiện mẫu hình.
        - Nhận định khả năng tăng giá trong 1 tháng tới, kèm điều kiện xác nhận và chấm điểm dựa trên khả năng tăng giá + mức độ hoàn thiện mẫu hình.
        - Chỉ dùng dữ liệu cung cấp, không bịa đặt. Đúng cấu trúc JSON chuẩn sau (KHÔNG ĐƯỢC THÊM/BỚT bất kỳ trường nào!).

        **Cấu trúc JSON cần trả về:**
        {{
        "quick_conclusion": "Kết luận ngắn gọn về phân tích VSA/SEBA và hành động tối ưu (tối đa 30 từ)",
        "vsa_seba_analysis": {{
            "supply_demand_imbalance": "Phân tích mất cân bằng cung-cầu theo VSA (volume, spread, closing price)",
            "effort_background": "Phân tích nỗ lực (effort) và bối cảnh (background) theo SEBA",
            "key_price_points": ["Các điểm giá quan trọng (support/resistance, fibo) với price action"],
            "volume_insights": ["Các điểm khối lượng quan trọng (spikes, climaxes) và ý nghĩa"],
            "pattern_potential": ["Các mẫu hình đang hình thành tiềm năng (ví dụ: tam giác, cờ, cốc tay cầm)"],
            "pattern_confirmation_conditions": ["Điều kiện xác nhận hoàn thiện mẫu hình (ví dụ: breakout với volume cao)"],
            "professional_insight": "Nhận định chuyên môn cao về hành động giá tổng thể"
        }},
        "price_increase_1m": {{
            "expectation": "Có/Không (nhận định có tăng giá trong 1 tháng tới hay không)",
            "conditions": ["Điều kiện để tăng giá xảy ra (ví dụ: breakout xác nhận với volume tăng)"],
            "probability_score": number (0-100, chấm điểm dựa trên khả năng tăng giá và hoàn thiện mẫu hình)
        }},
        "tech_overview": {{
            "trend": "Up/Sideways/Down",
            "momentum": "Strong/Moderate/Weak",
            "volatility": "High/Medium/Low",
            "breadth": "string (từ volume/OBV)",
            "notes": ["array of strings (luận điểm ngắn gọn theo VSA/SEBA)"]
        }},
        "scenarios": {{
            "bull": {{"target_price": number, "probability": "<%>", "drivers": ["array of strings"], "invalidations": "string (điều kiện)"}},
            "neutral": {{"target_price": number, "probability": "<%>", "drivers": ["array of strings"], "invalidations": "string (điều kiện)"}},
            "bear": {{"target_price": number, "probability": "<%>", "drivers": ["array of strings"], "invalidations": "string (điều kiện)"}}
        }},
        "strategy_recommendation": {{
            "action": "BUY/HOLD/SELL",
            "reasoning": "Lý do chi tiết dựa trên VSA/SEBA và phân tích chuyên sâu",
            "time_horizon": "Ngắn/Trung/Dài hạn",
            "entry": "Điểm vào lệnh phù hợp (dựa trên price action và volume)",
            "stop_loss": "Giá cắt lỗ (dựa trên support/resistance)",
            "take_profit": "Giá chốt lời (dựa trên fibo/target)",
            "position_sizing": "Tỷ trọng gợi ý dựa trên rủi ro (tối đa 1-2% vốn)",
            "risk_management": "Nguyên tắc ngắn gọn (dựa trên volume và effort)"
        }},
        "investment_scores": {{
            "setup_quality": number (0-100),
            "risk_reward": number (0-100),
            "trend_alignment": number (0-100),
            "momentum_strength": number (0-100),
            "reliability_score": number (0-100),
            "summary_score": number (0-100)
        }},
        "key_highlights": [
            "Điểm nhấn 1 từ VSA/SEBA",
            "Điểm nhấn 2 từ price action và volume"
        ],
        "risk_factors": [
            "Các yếu tố rủi ro cụ thể (ví dụ: volume thấp, invalidation)"
        ],
        "data_quality": {{
            "sample_size": number,
            "completeness": "<%>",
            "confidence_level": "Cao/Trung bình/Thấp"
        }}
        }}

        **Hướng dẫn tính toán và phân tích:**
        - Sử dụng VSA để phân tích: Volume cao với spread rộng (climactic action), low volume với narrow spread (no demand/supply), stopping volume.
        - Áp dụng SEBA: Supply (xác định cung cấp từ volume), Effort (nỗ lực mua/bán qua spread và close), Background (bối cảnh thị trường từ index_history), Action (hành động tối ưu dựa trên price action).
        - Xác định mẫu hình đang hình thành (dựa trên price action và volume) và điều kiện xác nhận (ví dụ: breakout với volume tăng, mô hình hoàn thiện với confirmation bar).
        - Nhận định khả năng tăng giá trong 1 tháng tới: Dựa trên hoàn thiện mẫu hình, volume support, và drivers; chấm điểm probability_score kết hợp yếu tố này.
        - Target price dựa trên fibo, support/resistance; probability từ drivers (ví dụ bull nếu volume absorption mạnh).
        - Đưa ra nhận định chuyên môn cao: Tập trung vào hành động giá kết hợp khối lượng để dự đoán xu hướng ngắn hạn (1-3 tháng).
        - JSON phải hợp lệ, đầy đủ, và chỉ dựa trên dữ liệu cung cấp (giá ở nghìn VND).
        """
        return prompt_template



    async def _call_ai_async(self, prompt: str) -> str:
        """Asynchronous call to Gemini API, expecting JSON text."""
        try:
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(
                None, lambda: self.client.generate_content(prompt, generation_config={"temperature": 0.7})
            )
            return resp.text
        except Exception as e:
            raise RuntimeError(f"AI API call failed: {e}") from e

    def _parse_response(self, response_text: str) -> AnalysisResponse:
        """Safely extract and parse JSON from AI response."""
        try:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start == -1 or end <= start:
                raise ValueError("No JSON found in response.")
            data = json.loads(response_text[start:end])
            strat = data.get("strategy_recommendation", {})
            action = strat.get("action", "NA")
            reliability = data.get("investment_scores", {}).get("reliability_score", 50)
            conf = float(reliability) 
            dq = data.get("data_quality", {})
            completeness = dq.get("completeness", 50)
            dq_score = float(completeness) 
            return AnalysisResponse(
                recommendation=action,
                confidence_level=conf,
                data_quality=dq_score,
                key_points=data.get("key_highlights", []),
                concerns=data.get("risk_factors", []),
                content=data,
            )
        except Exception as e:
            return AnalysisResponse(
                recommendation="PARSE_ERROR",
                confidence_level=0.0,
                data_quality=0.0,
                key_points=[f"Parse error: {str(e)}"],
                concerns=["Invalid AI response"],
                content={"raw": response_text},
            )

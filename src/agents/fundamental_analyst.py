# fundamental_analyst.py
# -------------------- 
# AI Fundamental Analyst for HOSE stocks, using raw data from fundamental_api.py to build analysis prompts 
# and generate DuPont-based recommendations in a structured JSON format.
# Focuses on DuPont analysis: ROE decomposition into Profit Margin, Asset Turnover, Equity Multiplier.
# Updated: Use rolling 4 quarters (TTM) for calculations, with correct column names from API.
# Dependencies: vnstock (via fundamental_api), pandas, google-generativeai

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import asyncio
import json
import pandas as pd

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Import from fundamental_api.py (assuming it's in the same directory)
from src.data.fundamental_api import FundamentalAPI  # Adjust import if needed

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

class FundamentalAnalyst:
    """AI Agent specialized in fundamental analysis using DuPont method."""
    
    def __init__(self, api_key: str, model: str = 'gemini-2.0-flash') -> None:
        if not genai:
            raise ImportError("google-generativeai not installed. Install with: pip install google-generativeai")
        self.api_key = api_key
        self.model = model
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)

    async def analyze(self, context: MarketContext) -> AnalysisResponse:
        """Perform DuPont-based fundamental analysis based on context's market_data."""
        # Steps: Compact data, Create prompt, Call AI asynchronously, Parse response
        data_for_ai = self.compact_market_data(context)
        prompt = self.create_prompt(data_for_ai)
        ai_text = await self.call_ai_async(prompt)
        return self.parse_response(ai_text)

    def compact_market_data(self, context: MarketContext) -> Dict[str, Any]:
        """Compress raw data tables for prompt embedding, ensuring brevity and JSON serializability."""
        md = context.market_data or {}
        ts = md.get('timestamp', datetime.now().strftime('%Y-%m-%d'))

        # Use fundamental_api to fetch data
        api = FundamentalAPI(context.symbol)
        income = api.get_income_statement()
        balance = api.get_balance_sheet()
        ratios = api.get_ratio()

        # Compute DuPont components with rolling 4 quarters (TTM) and correct column names
        dupont_data = self.compute_rolling_dupont(income, balance)

        income_compact = json_serializable_records(income.tail(8))  # Last 8 quarters/years
        balance_compact = json_serializable_records(balance.tail(8))
        ratios_compact = json_serializable_records(ratios.tail(8))
        dupont_compact = json_serializable_records(dupont_data)  # Already a DataFrame

        return {
            'symbol': context.symbol,
            'latest_price': context.current_price,
            'timestamp': ts,
            'income_statement': income_compact,
            'balance_sheet': balance_compact,
            'ratios': ratios_compact,
            'dupont_components': dupont_compact  # Pre-computed rolling DuPont for AI to analyze
        }

    def compute_rolling_dupont(self, income: pd.DataFrame, balance: pd.DataFrame) -> pd.DataFrame:
        """Compute rolling 4-quarter (TTM) DuPont components with correct column names."""
        # Merge income and balance on Năm, Kỳ
        df = pd.merge(income, balance, on=['CP', 'Năm', 'Kỳ'], how='inner')
        
        # Sort by Năm, Kỳ ascending for rolling calculations
        df = df.sort_values(['Năm', 'Kỳ'])
        
        # Ensure numeric types
        income_cols = ['Doanh thu thuần', 'Lợi nhuận sau thuế của Cổ đông công ty mẹ (đồng)']
        balance_cols = ['TỔNG CỘNG TÀI SẢN (đồng)', 'VỐN CHỦ SỞ HỮU (đồng)']
        for col in income_cols + balance_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Calculate TTM sums for income items
        df['revenue_ttm'] = df['Doanh thu thuần'].rolling(window=4, min_periods=1).sum()
        df['net_income_ttm'] = df['Lợi nhuận sau thuế của Cổ đông công ty mẹ (đồng)'].rolling(window=4, min_periods=1).sum()
        
        # For assets and equity, use average over the period (simple end-of-quarter average for rolling)
        df['avg_assets_ttm'] = df['TỔNG CỘNG TÀI SẢN (đồng)'].rolling(window=4, min_periods=1).mean()
        df['avg_equity_ttm'] = df['VỐN CHỦ SỞ HỮU (đồng)'].rolling(window=4, min_periods=1).mean()
        
        # DuPont components (TTM)
        df['profit_margin'] = (df['net_income_ttm'] / df['revenue_ttm']) * 100  # %
        df['asset_turnover'] = df['revenue_ttm'] / df['avg_assets_ttm']
        df['equity_multiplier'] = df['avg_assets_ttm'] / df['avg_equity_ttm']
        df['roe'] = (df['profit_margin'] / 100) * df['asset_turnover'] * df['equity_multiplier'] * 100  # %
        
        # Round and handle NaN
        for col in ['profit_margin', 'asset_turnover', 'equity_multiplier', 'roe']:
            df[col] = df[col].round(2).fillna(0)
        
        # Return relevant columns, sorted descending for recent first
        result = df[['Năm', 'Kỳ', 'profit_margin', 'asset_turnover', 'equity_multiplier', 'roe']]
        return result.sort_values(['Năm', 'Kỳ'], ascending=[False, False])

    def create_prompt(self, data: Dict) -> str:
        """Create a structured prompt for DuPont analysis."""
        symbol = data.get('symbol', 'N/A')
        latest_price = data.get('latest_price', 'N/A')
        data_json = json.dumps(data, ensure_ascii=False, indent=2)

        prompt_template = f"""
Bạn là một chuyên gia phân tích cơ bản cấp cao tại quỹ đầu tư lớn nhất Việt Nam, với hơn 20 năm kinh nghiệm phân tích cổ phiếu HOSE. 
Bạn chuyên sâu về phương pháp DuPont để phân tích ROE, tập trung vào việc phân tích xu hướng, rủi ro và khuyến nghị đầu tư.

Dữ liệu đầu vào:
- Mã cổ phiếu: {symbol}
- Giá hiện tại: {latest_price} nghìn VND
- Dữ liệu bảng (compact và serialized): {data_json}

Yêu cầu phân tích:
Thực hiện phân tích chuyên sâu theo phương pháp DuPont với dữ liệu rolling 4 quý (TTM). Tập trung vào:
- Phân tích ROE = Lợi nhuận biên (Net Income TTM / Revenue TTM) x Hiệu quả sử dụng tài sản (Revenue TTM / Avg Assets TTM) x Đòn bẩy tài chính (Avg Assets TTM / Avg Equity TTM).
- Xu hướng thời gian của từng thành phần (tăng/giảm, lý do từ dữ liệu thu nhập, cân đối).

- Đưa ra nhận định chuyên môn cao, kết luận hành động tối ưu (BUY/HOLD/SELL) với lý do chặt chẽ dựa trên dữ liệu.
- Phân tích 3 kịch bản (bull/neutral/bear) với target price, probability, drivers, invalidations kết hợp dựa vào EV/EBITDA và Số CP lưu hành (Triệu CP)
- Chỉ dùng dữ liệu cung cấp, không bịa đặt.

Định cấu trúc JSON chuẩn sau (KHÔNG THÊM/BỚT bất kỳ trường nào!):
{{
  "quick_conclusion": "Kết luận ngắn gọn về phân tích DuPont và hành động tối ưu (tối đa 30 từ)",
  "dupont_analysis": {{
    "profit_margin_trend": "Phân tích xu hướng lợi nhuận biên",
    "asset_turnover_trend": "Phân tích xu hướng hiệu quả sử dụng tài sản",
    "equity_multiplier_trend": "Phân tích xu hướng đòn bẩy tài chính",
    "roe_overall": "Phân tích tổng thể ROE và ý nghĩa"
  }},
  "professional_insight": "Nhận định chuyên môn cao về sức khỏe tài chính",
  "scenarios": {{
    "bull": {{ "target_price": number, "probability": number, "drivers": array of strings, "invalidations": string }},
    "neutral": {{ "target_price": number, "probability": number, "drivers": array of strings, "invalidations": string }},
    "bear": {{ "target_price": number, "probability": number, "drivers": array of strings, "invalidations": string }}
  }},
  "strategy_recommendation": {{
    "action": "BUY/HOLD/SELL",
    "reasoning": "Lý do chi tiết dựa trên DuPont",
    "time_horizon": "Ngắn/Trung/Dài hạn"
  }},
  "investment_scores": {{
    "roe_quality": number (0-100),
    "risk_level": number (0-100),
    "summary_score": number (0-100)
  }},
  "key_highlights": ["Điểm nhấn 1", "Điểm nhấn 2"],
  "risk_factors": ["Yếu tố rủi ro 1", "Yếu tố rủi ro 2"],
  "data_quality": {{ "completeness": number (0-100), "confidence_level": "Cao/Trung bình/Thấp" }}
}}

Hướng dẫn tính toán và phân tích:
- Sử dụng dữ liệu dupont_components (rolling 4 quý) để phân tích xu hướng.
- Target price dựa trên ROE dự báo và định giá cơ bản và dựa vào EV/EBITDA và Số CP lưu hành (Triệu CP)
- JSON phải hợp lệ, đầy đủ, và chỉ dựa trên dữ liệu cung cấp (giá nghìn VND).
"""
        return prompt_template

    async def call_ai_async(self, prompt: str) -> str:
        """Asynchronous call to Gemini API, expecting JSON text."""
        try:
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(None, lambda: self.client.generate_content(prompt, generation_config={'temperature': 0.3}))
            return resp.text
        except Exception as e:
            raise RuntimeError(f"AI API call failed: {e}") from e

    def parse_response(self, response_text: str) -> AnalysisResponse:
        """Safely extract and parse JSON from AI response."""
        try:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start == -1 or end <= start:
                raise ValueError("No JSON found in response.")
            data = json.loads(response_text[start:end])
            strat = data.get('strategy_recommendation', {})
            action = strat.get('action', 'N/A')
            conf = data.get('data_quality', {}).get('confidence_level', 'Trung bình')
            conf_score = 80 if conf == 'Cao' else 50 if conf == 'Trung bình' else 20
            dq = data.get('data_quality', {}).get('completeness', 50)
            return AnalysisResponse(
                recommendation=action,
                confidence_level=conf_score,
                data_quality=float(dq),
                key_points=data.get('key_highlights', []),
                concerns=data.get('risk_factors', []),
                content=data
            )
        except Exception as e:
            return AnalysisResponse(
                recommendation="PARSE_ERROR",
                confidence_level=0.0,
                data_quality=0.0,
                key_points=[f"Parse error: {str(e)}"],
                concerns=["Invalid AI response"],
                content={"raw": response_text}
            )

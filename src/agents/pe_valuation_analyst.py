from datetime import datetime
import asyncio
from typing import Dict, List, Optional, Any
import json
import pandas as pd

try:
    import google.generativeai as genai
except ImportError:
    print("Warning: google-generativeai not installed. Please install it with: pip install google-generativeai")
    genai = None

from src.data.pe_api import PEAPI

class MarketContext:
    """Context chứa thông tin thị trường cần thiết cho phân tích"""
    def __init__(self, symbol: str, current_price: Optional[float] = None, market_data: Optional[Dict] = None):
        self.symbol = symbol.upper()
        self.current_price = current_price
        self.market_data = market_data or {}
        self.timestamp = datetime.now()

class AnalysisResponse:
    """Response object chứa kết quả phân tích"""
    def __init__(self,
                 recommendation: Optional[str] = None,
                 confidence_level: Optional[float] = None,
                 data_quality: Optional[float] = None,
                 key_points: Optional[List[str]] = None,
                 concerns: Optional[List[str]] = None,
                 content: Optional[Dict] = None):
        self.recommendation = recommendation
        self.confidence_level = confidence_level
        self.data_quality = data_quality
        self.key_points = key_points or []
        self.concerns = concerns or []
        self.content = content or {}

class PEValuationAnalyst:
    """Agent chuyên về phân tích định giá PE"""
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        if not genai:
            raise ImportError("google-generativeai not installed. Please install it with: pip install google-generativeai")
        self.api_key = api_key
        self.model = model
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)

    async def analyze(self, context: MarketContext) -> AnalysisResponse:
        """Thực hiện phân tích định giá PE cho cổ phiếu"""
        pe_api = PEAPI(context.symbol)
        petrailing_df = pe_api.compute_pe_trailing()
        distribution_stats = pe_api.calculate_pe_distribution_stats(petrailing_df)

        analysis_data = {
            "symbol": context.symbol,
            "data_analyst": self._safe_convert_to_dict(petrailing_df, limit=1200),
            "distribution_stats": distribution_stats,
            "latest_price": self._safe_get_latest_price(petrailing_df),
            "latest_pe": self._safe_calculate_pe_stats(petrailing_df)
        }

        prompt = self._create_analysis_prompt(analysis_data)
        response = await self._call_ai_async(prompt)
        result = self._parse_response(response)
        return result

    def _safe_calculate_pe_stats(self, df: pd.DataFrame) -> float:
        """Lấy PE hiện tại an toàn"""
        try:
            return float(df.iloc[0]["PE_trailing"])
        except Exception:
            return float('nan')

    def _safe_get_latest_price(self, df: pd.DataFrame) -> Optional[float]:
        """Lấy giá mới nhất an toàn"""
        try:
            return float(df.iloc[0]["close"])
        except Exception:
            return None

    def _safe_convert_to_dict(self, df: pd.DataFrame, limit: int = 1000) -> List[Dict[str, Any]]:
        """Chuyển DataFrame thành dict an toàn"""
        try:
            cols_to_include = ["time", "close", "PE_trailing"]
            df_limit = df[cols_to_include].head(limit)
            return df_limit.to_dict(orient="records")
        except Exception:
            return []

    def _create_analysis_prompt(self, data: Dict) -> str:
        """Tạo prompt phân tích với kịch bản do AI tự đưa ra"""
        symbol = data.get("symbol", "N/A")
        latest_price = data.get("latest_price", "N/A")
        latest_pe = data.get("latest_pe", "null")
        dist_stats = json.dumps(data.get("distribution_stats", {}), ensure_ascii=False, indent=2)
        data_analyst = json.dumps(data.get("data_analyst", []), ensure_ascii=False, indent=2)

        prompt_template = f"""
            Bạn là một chuyên gia phân tích tài chính cấp cao tại quỹ đầu tư lớn nhất Việt Nam, với hơn 15 năm kinh nghiệm phân tích cổ phiếu HOSE.

            **Dữ liệu đầu vào:**
            - Mã cổ phiếu: {symbol}
            - Giá hiện tại: {latest_price} (nghìn VND)
            - PE hiện tại: {latest_pe}

            **Thống kê phân phối PE Trailing (sẵn có):**
            {dist_stats}

            **Dữ liệu bảng lịch sử PE:**
            {data_analyst}

            **Yêu cầu phân tích:**
            Thực hiện phân tích định giá chuyên sâu dựa trên dữ liệu, đúng cấu trúc JSON chuẩn sau (KHÔNG ĐƯỢC THÊM/BỚT bất kỳ trường nào!).
            Các kịch bản "bull", "neutral", "bear" sẽ là các giá trị gần nhất trong {dist_stats}

            **Cấu trúc JSON cần trả về:**
            {{
            "quick_conclusion": "Kết luận ngắn gọn về định giá và khuyến nghị",
            "pe_valuation": {{
                "current_pe": {latest_pe},
                "historical_pe_stats": {{"mean": , "median": , "percentile_current": }},
                "fair_value_pe": <giá trị gần nhất>,
                "fair_price": ,
                "current_vs_fair": "<±X%>",
                "z_score": ,
                "scenarios": {{
                "bull": {{"pe": <giá trị trên cách 1 bậc trong {dist_stats}>, "target_price": , "probability": "<%>", "rationale": "Lý do kịch bản tích cực"}},
                "neutral": {{"pe" <giá trị trên gần nhất trong {dist_stats}>: , "target_price": , "probability": "<%>", "rationale": "Lý do kịch bản trung tính"}},
                "bear": {{"pe": , "<giá trị pe liền dưới trong {dist_stats}>": , "probability": "<%>", "rationale": "Lý do kịch bản tiêu cực"}}
                }}
            }},
            "growth_analysis": {{
                "required_next_quarter_eps_growth": "<%>",
                "suitable_next_quarter_growth": "<%>",
                "growth_sustainability": <0-100>
            }},
            "strategy_recommendation": {{
                "action": "BUY/HOLD/SELL",
                "reasoning": "Lý do chi tiết dựa trên analysis",
                "time_horizon": "Ngắn/Trung/Dài hạn",
                "entry_strategy": "Cách vào lệnh, điểm mua phù hợp"
            }},
            "investment_score": {{
                "overall": <0-100>,
                "growth_potential": <0-100>,
                "value_attractiveness": <0-100>,
                "risk_adjusted": <0-100>
            }},
            "reliability_score": <0-100>,
            "key_highlights": [
                "PE hiện tại ở percentile , đánh giá ",
                "Giá hợp lý: nghìn VND",
                "Z-score: , status "
            ],
            "risk_factors": [
                "Các yếu tố rủi ro/ngành/vĩ mô cụ thể"
            ],
            "data_quality": {{
                "sample_size": ,
                "data_completeness": "<%>",
                "confidence_level": "Cao/Trung bình/Thấp"
            }}
            }}

            **Hướng dẫn tính toán:**
            - Sử dụng distribution_stats (mean, median, percentile_current, z_score) cho pe_valuation.
            - Fair value PE dựa trên median hoặc xu hướng lịch sử.
            - Target price = PE × EPS gần nhất (từ dữ liệu lịch sử).
            - Các kịch bản: Tự phân tích dựa trên dữ liệu, ví dụ bull nếu z-score thấp và xu hướng tăng.
            - Chỉ dùng dữ liệu cung cấp, giá ở nghìn VND, JSON phải hợp lệ và đầy đủ.
            """
        return prompt_template

    async def _call_ai_async(self, prompt: str) -> str:
        """Gọi AI API bất đồng bộ"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: self.client.generate_content(prompt))
            return response.text
        except Exception as e:
            raise Exception(f"AI API call failed: {str(e)}")

    def _parse_response(self, response_text: str) -> AnalysisResponse:
        """Parse response từ AI thành AnalysisResponse object"""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            json_text = response_text[start_idx:end_idx]
            data = json.loads(json_text)
            recommendation = data.get("strategy_recommendation", {}).get("reasoning", "N/A")
            reliability = data.get("reliability_score", 50)
            confidence = float(reliability) if isinstance(reliability, (int, float)) else 50.0
            key_points = data.get("key_highlights", [])
            concerns = data.get("risk_factors", [])
            return AnalysisResponse(
                recommendation=recommendation,
                confidence_level=confidence,
                data_quality=50.0,  # Giản hóa, có thể tính động nếu cần
                key_points=key_points,
                concerns=concerns,
                content=data
            )
        except Exception as e:
            return AnalysisResponse(
                recommendation="PARSE_ERROR",
                confidence_level=0.0,
                data_quality=0.0,
                key_points=[f"Lỗi parse response: {str(e)}"],
                concerns=["AI response không hợp lệ"],
                content={"error": str(e), "raw_response": response_text}
            )

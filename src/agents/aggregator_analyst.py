# src/agents/aggregator_analyst.py
import json
from dataclasses import dataclass, field
from typing import Dict, Any

try:
    import google.generativeai as genai
except ImportError:
    genai = None

@dataclass
class AggregationResult:
    overall_rating: str = "HOLD"
    target_price: float = 0.0
    confidence_level: float = 0.5
    time_horizon: str = "N/A"
    rationale: str = "Không có đủ thông tin."
    risk_factors: list = field(default_factory=list)
    key_highlights: list = field(default_factory=list)
    investment_score: float = 50.0
    raw_content: dict = field(default_factory=dict)

class AggregatorAnalyst:
    """AI Agent tổng hợp, đóng vai trò CIO (đồng bộ)."""
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)
    
    def analyze(self, fundamental_result, technical_result, pe_valuation_result, symbol) -> AggregationResult:
        prompt = self._create_aggregation_prompt(symbol, fundamental_result, technical_result, pe_valuation_result)
        ai_text = self._call_ai(prompt)
        return self._parse_response(ai_text)
    
    def _create_aggregation_prompt(self, symbol, fundamental, technical, pe_valuation) -> str:
        fundamental_json = json.dumps(fundamental, ensure_ascii=False, indent=2)
        technical_json = json.dumps(technical, ensure_ascii=False, indent=2)
        pe_valuation_json = json.dumps(pe_valuation, ensure_ascii=False, indent=2)
        
        # Sửa lỗi SyntaxError: Nhân đôi các dấu ngoặc nhọn {{ }} để chúng không bị f-string xử lý
        return f"""
Bạn là Giám đốc Đầu tư (CIO) của một quỹ đầu tư hàng đầu. Nhiệm vụ của bạn là tổng hợp báo cáo từ ba bộ phận phân tích để đưa ra quyết định đầu tư cuối cùng cho mã cổ phiếu {symbol}.

**Nguyên tắc chỉ đạo:**
1.  **Cơ bản cho 'MUA GÌ', Kỹ thuật cho 'MUA KHI NÀO'**: Dùng cơ bản cho tầm nhìn dài hạn, kỹ thuật cho thời điểm vào/ra lệnh.
2.  **Đồng thuận là chìa khóa**: Khi cả ba báo cáo đồng thuận, mức độ tự tin sẽ rất cao.
3.  **Xử lý mâu thuẫn**: Nếu có mâu thuẫn, hãy thận trọng, có thể là "HOLD" hoặc giảm tỷ trọng.
4.  **Rủi ro là trên hết**: Luôn xác định rủi ro chính và đề xuất chiến lược quản trị.

**BÁO CÁO ĐẦU VÀO:**
1. Phân tích Cơ bản (Fundamental): {fundamental_json}
2. Phân tích Kỹ thuật (Technical): {technical_json}
3. Phân tích Định giá P/E (PE Valuation): {pe_valuation_json}

**YÊU CẦU:**
Tổng hợp thông tin và điền vào cấu trúc JSON sau (KHÔNG thay đổi cấu trúc):
```json
{{
  "overall_rating": "BUY/HOLD/SELL",
  "target_price": "number (giá mục tiêu cuối cùng, tính toán có trọng số)",
  "confidence_level": "number (0.0-1.0, dựa trên mức độ đồng thuận)",
  "time_horizon": "1M/3M/6M/12M",
  "rationale": "Lý do chi tiết cho quyết định cuối cùng, giải thích cách xử lý các tín hiệu đồng thuận/mâu thuẫn.",
  "risk_factors": ["Rủi ro chính 1 (tổng hợp)", "Rủi ro chính 2"],
  "key_highlights": ["Điểm nhấn chính 1 (tổng hợp)", "Điểm nhấn chính 2"],
  "investment_score": "number (0-100, trọng số: Cơ bản 40%, Kỹ thuật 30%, Định giá 30%)",
  "consensus_analysis": {{
    "agreement_level": "HIGH/MEDIUM/LOW",
    "conflicting_signals": "Mô tả ngắn gọn các tín hiệu mâu thuẫn nếu có."
  }},
  "entry_strategy": {{
    "optimal_entry": "number (vùng giá vào lệnh)",
    "stop_loss": "number (ngưỡng cắt lỗ)",
    "position_sizing": "Khuyến nghị tỷ trọng vốn (Thấp, Trung bình, Cao)"
  }}
}}
```"""
    
    def _call_ai(self, prompt: str) -> str:
        try:
            response = self.client.generate_content(prompt, generation_config={"temperature": 0.2})
            return response.text
        except Exception as e:
            return json.dumps({"error": f"Lỗi gọi API của AI: {e}"})

    def _parse_response(self, text: str) -> AggregationResult:
        try:
            start, end = text.find('{'), text.rfind('}') + 1
            if start == -1: raise ValueError("Không tìm thấy JSON.")
            data = json.loads(text[start:end])
            
            if "error" in data:
                return AggregationResult(overall_rating="ERROR", rationale=data["error"], raw_content=data)
            
            return AggregationResult(
                overall_rating=data.get("overall_rating", "HOLD"),
                target_price=float(data.get("target_price", 0.0)),
                confidence_level=float(data.get("confidence_level", 0.5)),
                time_horizon=data.get("time_horizon", "6M"),
                rationale=data.get("rationale", ""),
                risk_factors=data.get("risk_factors", []),
                key_highlights=data.get("key_highlights", []),
                investment_score=float(data.get("investment_score", 50.0)),
                raw_content=data
            )
        except Exception as e:
            return AggregationResult(
                overall_rating="PARSE_ERROR", 
                rationale=f"Lỗi phân tích JSON: {e}", 
                raw_content={"raw": text}
            )
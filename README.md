# GoldenKey AI Trading Analysis

Hệ thống phân tích cổ phiếu Việt Nam sử dụng AI với đội ngũ chuyên gia ảo chuyên biệt.

## 🌟 Tính năng chính

### 🤖 Đội ngũ AI Agent chuyên biệt
- **Technical Analyst (Minh Anh)**: Chuyên gia phân tích kỹ thuật với 8 năm kinh nghiệm
- **Fundamental Analyst (Thảo Linh)**: Chuyên gia phân tích cơ bản với 10 năm kinh nghiệm
- **Portfolio Manager (Hoàng Nam)**: Chuyên gia quản lý danh mục với 12 năm kinh nghiệm  
- **Risk Manager (Minh Đức)**: Chuyên gia quản lý rủi ro với 9 năm kinh nghiệm

### 📊 Chức năng phân tích
- **Phân tích đơn lẻ**: Phân tích toàn diện một cổ phiếu
- **Phân tích danh mục**: Tối ưu hóa và đánh giá rủi ro danh mục
- **Quick Overview**: Phân tích nhanh nhiều cổ phiếu (không dùng AI)
- **Phân tích rủi ro**: Đánh giá rủi ro chuyên sâu

### 🔧 Công nghệ
- **Backend**: Python, VNStock API, Google Gemini AI
- **Frontend**: Streamlit Dashboard
- **Data**: 21 ngành công nghiệp với 1000+ mã cổ phiếu
- **Cache**: Hệ thống cache thông minh tiết kiệm API cost

## 📁 Cấu trúc dự án

```
Agent-to-agent-ai-trading-vietnam/
├── app.py                      # Entry point chính
├── requirements.txt            # Dependencies
├── config.json                 # Configuration file
├── README.md                  # Documentation
├── src/
│   ├── agents/                # AI Agents
│   │   ├── base_agent.py      # Base class cho agents
│   │   ├── technical_analyst.py
│   │   ├── fundamental_analyst.py
│   │   ├── portfolio_manager.py
│   │   └── risk_manager.py
│   ├── core/
│   │   └── analysis_pipeline.py # Điều phối agents
│   ├── data/
│   │   └── vn_stock_api.py     # VN Stock API wrapper ✅
│   ├── ui/
│   │   ├── components.py       # UI components
│   │   ├── main_dashboard.py   # Dashboard chính
│   │   └── styles.py          # Custom styles
│   └── utils/
│       ├── config.py          # Configuration management
│       └── helpers.py         # Utility functions
├── data/
│   └── cache/                 # Cache directory
└── logs/                      # Log files
```

## 🚀 Hướng dẫn cài đặt

### 1. Clone repository
```bash
git clone <repository-url>
cd Agent-to-agent-ai-trading-vietnam
```

### 2. Tạo virtual environment
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# hoặc
.venv\Scripts\activate     # Windows
```

### 3. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 4. Cấu hình API Key
Tạo file `config.json` trong thư mục gốc:

```json
{
    "api": {
        "api_keys": {
            "gemini": "YOUR_GEMINI_API_KEY_HERE"
        }
    },
    "agents": {
        "model_name": "gemini-1.5-flash",
        "max_tokens": 2048,
        "temperature": 0.7
    },
    "ui": {
        "theme": "light",
        "page_title": "GoldenKey AI Analysis"
    },
    "cache_duration": 30,
    "enable_caching": true,
    "debug_mode": false
}
```

Hoặc set environment variable:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### 5. Chạy ứng dụng
```bash
streamlit run app.py
```

## 💡 Cách sử dụng

### Phân tích cổ phiếu đơn lẻ
1. Chọn "🔍 Phân tích đơn lẻ"
2. Nhập mã cổ phiếu (VD: VCB, FPT, VHM)
3. Chọn chuyên gia muốn tư vấn
4. Nhấn "🚀 Phân tích"

### Phân tích danh mục
1. Chọn "📊 Phân tích danh mục"
2. Nhập danh mục (thủ công hoặc upload CSV)
3. Nhấn "📊 Phân tích danh mục"

### Quick Overview
1. Chọn "⚡ Quick Overview"
2. Nhập nhiều mã cổ phiếu (cách nhau bởi dấu phẩy)
3. Nhấn "⚡ Phân tích nhanh"

## 📈 Dữ liệu hỗ trợ

### 21 ngành công nghiệp
- Hàng hóa và dịch vụ công nghiệp
- Ôtô & linh kiện phụ tùng
- Thực phẩm & Đồ uống
- Đồ dùng cá nhân và đồ gia dụng
- Y tế
- Dịch vụ bán lẻ
- Phương tiện truyền thông
- Du lịch & Giải trí
- Viễn thông
- Dịch vụ tiện ích
- Ngân hàng
- Bảo hiểm
- Bất động sản
- Dịch vụ tài chính
- Công nghệ

### Chỉ số phân tích
- **Kỹ thuật**: MA, RSI, MACD, Bollinger Bands, ATR
- **Cơ bản**: P/E, P/B, ROE, ROA, Debt/Equity
- **Rủi ro**: VaR, Maximum Drawdown, Volatility, Beta
- **Danh mục**: Correlation, Diversification, Concentration

## ⚙️ Cấu hình nâng cao

### Tùy chỉnh Agent
Mỗi AI Agent có thể được tùy chỉnh personality và prompt trong file tương ứng:
- `src/agents/technical_analyst.py`
- `src/agents/fundamental_analyst.py`
- `src/agents/portfolio_manager.py`
- `src/agents/risk_manager.py`

### Cache Management
- Cache tự động với TTL 30 phút
- Có thể xóa cache qua UI
- Tiết kiệm API cost và thời gian phân tích

### Logging
- Log files trong `logs/app.log`
- Debug mode hiển thị thông tin chi tiết
- Performance tracking cho mỗi phân tích

## 🔧 Development

### Code Structure
- **BaseAgent**: Abstract class cho tất cả AI agents
- **AnalysisPipeline**: Điều phối và tổng hợp kết quả
- **VNStockAPI**: Wrapper cho vnstock với industry-specific fields
- **Components**: UI components tái sử dụng

### Testing
```bash
pytest tests/
```

### Code Quality
```bash
black src/
flake8 src/
```

## 🚨 Lưu ý quan trọng

1. **API Key**: Cần Google Gemini API key để sử dụng AI features
2. **Rate Limiting**: Có giới hạn số request đồng thời để tránh rate limit
3. **Data Quality**: Luôn kiểm tra chất lượng dữ liệu trước khi phân tích
4. **Risk Disclaimer**: Đây là công cụ hỗ trợ, không phải lời khuyên đầu tư

## 🔄 Cập nhật và bảo trì

### Cập nhật dữ liệu
- VNStock API tự động cập nhật dữ liệu mới nhất
- Industry configs có thể được mở rộng trong `vn_stock_api.py`

### Monitoring
- Performance metrics trong dashboard
- Log monitoring cho debug
- Cache hit rate tracking

## 📞 Hỗ trợ

- **Issues**: Tạo issue trên GitHub repository
- **Docs**: Chi tiết trong source code docstrings
- **Examples**: Xem `examples/` directory (nếu có)

---

*Phát triển bởi GoldenKey Investment Team - Phiên bản 1.0*
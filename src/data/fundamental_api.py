"""
vn_stock_api.py

Module lấy, xử lý và xuất dữ liệu tài chính (Cash Flow, Income Statement,
Ratio, Balance Sheet) của cổ phiếu Việt Nam theo từng ngành cố định.
Tích hợp sẵn để sử dụng trong Streamlit và AI Agent phân tích chuyên sâu.
"""


from typing import List, Optional

import pandas as pd
from vnstock import Quote, Finance



from typing import List, Optional

class IndustryConfig:
    """
    Cấu hình chỉ tiêu cho từng ngành.

    Attributes:
        name (str): Tên ngành.
        codes (List[str]): Danh sách mã cổ phiếu thuộc ngành.
        cashflow_fields (List[str]): Cột lấy từ df_cash_flow.
        income_fields (List[str]): Cột lấy từ df_income_statement.
        ratio_fields (List[str]): Cột lấy từ df_ratio.
        balance_fields (List[str]): Cột lấy từ df_balance_sheet.
    """
    def __init__(self,
                 name: str,
                 codes: List[str],
                 cashflow_fields: List[str],
                 income_fields: List[str],
                 ratio_fields: List[str],
                 balance_fields: List[str]):
        self.name = name
        self.codes = codes
        self.cashflow_fields = cashflow_fields
        self.income_fields = income_fields
        self.ratio_fields = ratio_fields
        self.balance_fields = balance_fields


# Nhóm1: Bất động sản
NHOM1 = IndustryConfig(
    name="Nhóm1",
    codes="NBB,HPR,C21,DIH,NVT,SID,CEO,HD2,CKG,HBI,TN1,VPI,SIP,CRE,HPX,BCM,DXS,UNI,VCG,PVR,STL,TIG,PFL,LGL,FLC,LSG,VGC,DTI,CER,EIN,KOS,AGG,TBH,BIG,MBT,RCL,HDC,DXG,NHN,PNT,VNN,LAI,FIR,E29,SJS,CII,ITA,ITC,PPI,D11,VPH,IDV,NDN,IDJ,VNI,CLG,HU6,BAX,HTT,SZC,PLA,SSH,TDH,DIG,NTL,CSC,OCH,SZL,PFV,TNT,SGR,LEC,NTC,NVL,TID,VHM,HRB,IDC,BDP,SZB,KHG,BVL,KHA,LHG,QCG,PDR,SDI,FDC,DTA,HQC,KAC,HAR,TIP,SII,BII,HIZ,SLD,SNZ,BCR,ASM,BCI,SDU,OGC,SCR,NTB,CCL,DLR,VCR,NLG,VRE,DCH,PWA,FTI,SZG,TIX,D2D,VIC,KBC,VRC,KDH,DRH,PXL,PVL,CIG,NVN,HDG,FIT,HPI,TCH,LDG,MH3,HD8,NRC,HD3,HD6,PTN,MGR,TAL".split(","),
    cashflow_fields=[
            "CP","Năm","Kỳ","Khấu hao TSCĐ",
            "Lưu chuyển tiền tệ ròng từ các hoạt động SXKD",
            "Mua sắm TSCĐ","Lưu chuyển tiền thuần trong kỳ"
        ],
        income_fields=[
            "CP","Năm","Kỳ","Tăng trưởng doanh thu (%)","Doanh thu thuần",
            "Giá vốn hàng bán","Lãi gộp","Lãi/Lỗ từ hoạt động kinh doanh",
            "Lợi nhuận sau thuế của Cổ đông công ty mẹ (đồng)"
        ],
        ratio_fields=[
            "CP","Năm","Kỳ","Nợ/VCSH"
            ,"Biên lợi nhuận gộp (%)",
            "Biên lợi nhuận ròng (%)","ROE (%)","EBITDA (Tỷ đồng)",
            "EV/EBITDA","EBIT (Tỷ đồng)","Vòng quay tài sản","Đòn bẩy tài chính","Số CP lưu hành (Triệu CP)"
        ],
        balance_fields=[
            "CP","Năm","Kỳ","Tiền và tương đương tiền (đồng)",
            "Các khoản phải thu ngắn hạn (đồng)","Hàng tồn kho, ròng (đồng)",
            "Tài sản cố định (đồng)","TỔNG CỘNG TÀI SẢN (đồng)",
            "Vay và nợ thuê tài chính ngắn hạn (đồng)",
            "Vay và nợ thuê tài chính dài hạn (đồng)",
            "NỢ PHẢI TRẢ (đồng)","VỐN CHỦ SỞ HỮU (đồng)"
        ]
)

# Nhóm2: Ngân hàng
NHOM2 = IndustryConfig(
    name="Nhóm2",
    codes="ACB,STB,BID,SSB,HDB,MBB,BVB,ABB,PNB,VCB,BAB,PGB,TPB,VRB,OCB,DAB,TB,NAB,MSB,EIB,VAB,TCB,SGB,AGRB,KLB,MXBANK,VNDB,LPB,VIB,EAB,CTG,DCB,NVB,PACB,VBB,VPBF,GB,SCB,WEB,FCB,MHBB,SHB,MDB,VPB".split(","),
    cashflow_fields=[
         "CP","Năm","Kỳ","Khấu hao TSCĐ",
            "Lưu chuyển tiền tệ ròng từ các hoạt động SXKD",
            "Mua sắm TSCĐ","Lưu chuyển tiền thuần trong kỳ"
    ],
    income_fields=[
        "CP","Năm","Kỳ","Thu nhập lãi thuần","Lãi thuần từ hoạt động dịch vụ",
        "Tổng thu nhập hoạt động","LN từ HĐKD trước CF dự phòng","Chi phí dự phòng rủi ro tín dụng",
        "LN trước thuế","Lợi nhuận sau thuế của Cổ đông công ty mẹ (đồng)"
    ],
    ratio_fields=[
        "CP","Năm","Kỳ","Nợ/VCSH"
            ,"Biên lợi nhuận gộp (%)",
            "Biên lợi nhuận ròng (%)","ROE (%)","EBITDA (Tỷ đồng)",
            "EV/EBITDA","EBIT (Tỷ đồng)","Số CP lưu hành (Triệu CP)"
    ],
    balance_fields=[
        "CP","Năm","Kỳ","Cho vay khách hàng","Dự phòng rủi ro cho vay khách hàng",
        "Tiền gửi của khách hàng","Phát hành giấy tờ có giá","TỔNG CỘNG TÀI SẢN (đồng)",
        "NỢ PHẢI TRẢ (đồng)","VỐN CHỦ SỞ HỮU (đồng)"
    ]
)

# Nhóm3: fallback mặc định nếu không thuộc Nhóm1 hoặc Nhóm2
NHOM3 = IndustryConfig(
    name="Nhóm3",
        codes=[],  # không cần liệt kê
        cashflow_fields=[
            "CP","Năm","Kỳ","Khấu hao TSCĐ",
            "Lưu chuyển tiền tệ ròng từ các hoạt động SXKD",
            "Mua sắm TSCĐ","Lưu chuyển tiền thuần trong kỳ"
        ],
        income_fields=[
            "CP","Năm","Kỳ","Tăng trưởng doanh thu (%)","Doanh thu thuần",
            "Giá vốn hàng bán","Lãi gộp","Lãi/Lỗ từ hoạt động kinh doanh",
            "Lợi nhuận sau thuế của Cổ đông công ty mẹ (đồng)"
        ],
        ratio_fields=[
            "CP","Năm","Kỳ","Nợ/VCSH"
            ,"Biên lợi nhuận gộp (%)",
            "Biên lợi nhuận ròng (%)","ROE (%)","EBITDA (Tỷ đồng)",
            "EV/EBITDA","EBIT (Tỷ đồng)","Vòng quay tài sản","Đòn bẩy tài chính","Số CP lưu hành (Triệu CP)"
        ],
        balance_fields=[
            "CP","Năm","Kỳ","Tiền và tương đương tiền (đồng)",
            "Các khoản phải thu ngắn hạn (đồng)","Hàng tồn kho, ròng (đồng)",
            "Tài sản cố định (đồng)","TỔNG CỘNG TÀI SẢN (đồng)",
            "Vay và nợ thuê tài chính ngắn hạn (đồng)",
            "Vay và nợ thuê tài chính dài hạn (đồng)",
            "NỢ PHẢI TRẢ (đồng)","VỐN CHỦ SỞ HỮU (đồng)"
        ]
)

# Tập set để kiểm tra nhanh
NHOM1_SET = set(NHOM1.codes)
NHOM2_SET = set(NHOM2.codes)

# Helper: nếu không thuộc Nhóm1/2 thì mặc định Nhóm3
def find_industry_config(symbol: str) -> IndustryConfig:
    s = symbol.strip().upper()
    if s in NHOM1_SET:
        return NHOM1
    if s in NHOM2_SET:
        return NHOM2
    return NHOM3



  


class FundamentalAPI:
    """
    API chính:
      
      - get_cash_flow
      - get_income_statement
      - get_ratio_data
      - get_balance_sheet
    """
    def __init__(self, symbol:str, source="VCI"):
        
        self._quote=Quote(symbol=symbol)
        self._finance=Finance(symbol=symbol, source=source)
        self.industry=find_industry_config(symbol)
        if not self.industry:
            raise ValueError(f"Ngành cho {symbol} không xác định")


    def get_cash_flow(self)->pd.DataFrame:
        df=self._finance.cash_flow(period="quarter",lang="vi")
        cols_to_divide = [col for col in df.columns if col not in ['CP','Năm', 'Kỳ']]
        df[cols_to_divide] = df[cols_to_divide].div(1000000000).round(1)
        return df[self.industry.cashflow_fields].sort_values(["Năm","Kỳ"], ascending=[False, False])

    def get_income_statement(self)->pd.DataFrame:
        df=self._finance.income_statement(period="quarter",lang="vi")
        cols_to_divide = [col for col in df.columns if col not in ['CP','Năm', 'Kỳ','Tăng trưởng doanh thu (%)']]
        df[cols_to_divide] = df[cols_to_divide].div(1000000000).round(1)
        return df[self.industry.income_fields].sort_values(["Năm","Kỳ"], ascending=[False, False])

    def get_ratio(self)->pd.DataFrame:
        raw=self._finance.ratio(period="quarter",lang="vi",dropna=True)
        df=raw.droplevel(0,axis=1)
        cols_to_divide = [col for col in df.columns if col in ['Biên lợi nhuận gộp (%)', 'Biên lợi nhuận ròng (%)', 'ROE (%)']]
        df[cols_to_divide] = (df[cols_to_divide]*100).round(2)
        df['EBITDA (Tỷ đồng)'] = (df['EBITDA (Tỷ đồng)']/1000000000).round(1)
        df['EBIT (Tỷ đồng)'] = (df['EBIT (Tỷ đồng)']/1000000000).round(1)
        return df[self.industry.ratio_fields].sort_values(["Năm","Kỳ"], ascending=[False, False])

    def get_balance_sheet(self)->pd.DataFrame:
        df=self._finance.balance_sheet(period="quarter",lang="vi")
        cols_to_divide = [col for col in df.columns if col not in ['CP','Năm', 'Kỳ']]
        df[cols_to_divide] = df[cols_to_divide].div(1000000000).round(1)
        
        return df[self.industry.balance_fields].sort_values(["Năm","Kỳ"], ascending=[False, False])

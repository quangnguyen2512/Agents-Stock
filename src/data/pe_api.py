from datetime import datetime
from typing import List, Dict, Optional, Union
import numpy as np
import scipy.stats as stats
import pandas as pd
from vnstock import Quote, Finance

class DataProcessor:
    @staticmethod
    def add_year_quarter(df: pd.DataFrame, time_col="time") -> pd.DataFrame:
        df[time_col] = pd.to_datetime(df[time_col])
        df["Năm"] = df[time_col].dt.year
        df["Kỳ"] = df[time_col].dt.quarter
        return df

    @staticmethod
    def merge_price_ratio(price_df, ratio_df, eps_field="EPS (VND)"):
        # 1. Sắp xếp theo thời gian tăng dần
        eps = ratio_df[["Năm","Kỳ", eps_field]].copy()
        eps = eps.sort_values(["Năm","Kỳ"], ascending=[True, True])
        eps["EPS_nam"] = eps[eps_field].rolling(4).sum()

        # 3. Merge với price_df theo Năm và Kỳ
        df = pd.merge(price_df, eps, on=["Năm","Kỳ"], how="left")
        df.fillna(method="bfill", inplace=True)

        # 4. Tính PE_trailing
        df["PEtrailing"] = df["close"] * 1000 / df["EPS_nam"]
        df['time'] = df['time'].dt.strftime('%Y-%m-%d')
        return df

    @staticmethod
    def calculate_pe_distribution_stats(df: pd.DataFrame, pe_column: str = "PEtrailing") -> Dict:
        """
        Thực hiện phân tích thống kê toàn diện trên một chuỗi PE ratio.

        Hàm này làm sạch dữ liệu, tính toán các chỉ số thống kê mô tả, phân vị,
        phân tích xu hướng và so sánh với các đường trung bình động.
        Tất cả các kết quả sẽ được làm tròn tới một chữ số thập phân.

        Args:
            df (pd.DataFrame): DataFrame chứa dữ liệu, được sắp xếp theo thứ tự thời gian giảm dần
                              (dữ liệu mới nhất trên cùng).
            pe_column (str): Tên của cột chứa dữ liệu PE.

        Returns:
            Dict: Một từ điển chứa tất cả các chỉ số thống kê tính toán.
        """

        # FIX: Kiểm tra DataFrame có rỗng không
        if df.empty:
            return {"error": "DataFrame rỗng"}

        # FIX: Kiểm tra cột PE có tồn tại không
        if pe_column not in df.columns:
            return {"error": f"Không tìm thấy cột {pe_column}"}

        # 4. Tính PEtrailing
        pe_values = df[pe_column].replace([np.inf, -np.inf], np.nan).dropna()

        # FIX: Kiểm tra sau khi làm sạch dữ liệu
        if len(pe_values) == 0:
            return {"error": "Không có dữ liệu PEtrailing hợp lệ"}

        # Lọi bỏ NaN, inf
        current_pe = pe_values.iloc[0] if not pe_values.empty else np.nan

        stats_dict = {
            "current_pe": np.round(current_pe, 1),
            "count": len(pe_values),
            "mean": pe_values.mean().round(1),
            "median": pe_values.median().round(1),
            "std": pe_values.std().round(1),
            "var": pe_values.var().round(1),
            "skewness": round(stats.skew(pe_values), 1),
            "kurtosis": round(stats.kurtosis(pe_values), 1),
            "min": pe_values.min().round(1),
            "max": pe_values.max().round(1),
            "range": (pe_values.max() - pe_values.min()).round(1)
        }

        # Giá trị PEtrailing hiện tại (cuối cùng theo time)
        percentiles = [25,30, 40, 50, 60,70,75, 80, 90, 95, 99]
        for p in percentiles:
            stats_dict[f"percentile_{p}"] = np.percentile(pe_values, p).round(1)

        # Các phân vị quan trọng
        if not np.isnan(current_pe):
            current_percentile = stats.percentileofscore(pe_values, current_pe)
            stats_dict["current_percentile"] = round(current_percentile, 1)
        else:
            stats_dict["current_percentile"] = np.nan
            stats_dict["current_position"] = "Không xác định"



        # Khoảng tin cậy 95%
        q1, q3 = stats_dict["percentile_25"], stats_dict["percentile_75"]
        iqr = q3 - q1
        stats_dict["iqr"] = round(iqr, 1)
        stats_dict["outlier_lower_threshold"] = round(q1 -  2* iqr, 1)
        stats_dict["outlier_upper_threshold"] = round(q3 + 2 * iqr, 1)

        

        # Giá trị hiện tại có phải outlier?
        if stats_dict["mean"] != 0:
            cv = stats_dict["std"] / stats_dict["mean"]
            stats_dict["coefficient_of_variation"] = round(cv, 1)
        else:
            stats_dict["coefficient_of_variation"] = np.inf

        # Coefficient of Variation
        if not np.isnan(current_pe) and stats_dict["std"] != 0:
            z_score = (current_pe - stats_dict["mean"]) / stats_dict["std"]
            stats_dict["current_z_score"] = round(z_score, 1)
        else:
            stats_dict["current_z_score"] = np.nan




        # Đảo ngược y để trend tính từ cũ đến mới
        if len(pe_values) >= 200:
            # So sánh với MA20
            ma200 = pe_values.rolling(window=200).mean().iloc[199]  # MA đầu tiên được tính ở index 19
            stats_dict["ma200"] = round(ma200, 1)

            if not np.isnan(current_pe) and not np.isnan(ma200):
                deviation = ((current_pe - ma200) / ma200) * 100
                stats_dict["deviation_from_ma200"] = round(deviation, 1)

        return stats_dict


class PEAPI:
    def __init__(self, symbol: str, source="VCI"):
        self.symbol = symbol
        self.source = source
        self.quote = Quote(symbol=symbol)
        self.finance = Finance(symbol=symbol, source=source)

    def get_price_history(self, start: str = "2018-01-01", end: Optional[str] = None, interval: str = "1D") -> pd.DataFrame:
        if end is None:
            end = datetime.now().strftime("%Y-%m-%d")

        df = self.quote.history(start=start, end=end, interval=interval)
        df = DataProcessor.add_year_quarter(df)
        return df.sort_values("time", ascending=False)

    def get_ratio_data(self) -> pd.DataFrame:
        raw = self.finance.ratio(period="quarter", lang="vi", dropna=True)
        df = raw.droplevel(0, axis=1)
        return df.sort_values(["Năm","Kỳ"], ascending=[False, False])

    def compute_pe_trailing(self, price_df=None, ratio_df=None) -> pd.DataFrame:
        price_df = price_df or self.get_price_history()
        ratio_df = ratio_df or self.get_ratio_data()
        return DataProcessor.merge_price_ratio(price_df, ratio_df)

    def calculate_pe_distribution_stats(self,df=None):
        if df is None:  # ✅ Sửa lỗi
            df = self.compute_pe_trailing()
        return DataProcessor.calculate_pe_distribution_stats(df)


    # Sửa lỗi: Lấy MA20 của dữ liệu gần nhất

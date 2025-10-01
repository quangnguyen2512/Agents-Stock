# src/core/analysis_pipeline.py - Updated for 4 Agent System
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime
import logging

from ..agents.base_agent import FourAgentManager, MarketContext
from ..agents.technical_analyst import TechnicalAnalyst
from ..agents.fundamental_analyst import FundamentalAnalyst
from ..agents.pe_valuation_analyst import PEValuationAnalyst
from ..agents.investment_advisor import InvestmentAdvisor
from ..data.fundamental_api import VNStockAPI
from ..utils.config import load_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """
    Hệ thống điều phối 4 AI Agents chuyên biệt:
    1. Technical Analyst - Phân tích kỹ thuật
    2. Fundamental Analyst - Phân tích cơ bản
    3. PE Valuation Analyst - Định giá PE
    4. Investment Advisor - Tư vấn tổng hợp
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.config = load_config()
        self.api_key = api_key or self.config.api.api_keys.get('gemini', '')
        
        if not self.api_key:
            logger.error("❌ Không tìm thấy API key cho Google Gemini")
            raise ValueError("API key is required for AI analysis")
        
        # Khởi tạo 4-Agent Manager
        self.agent_manager = FourAgentManager()
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Khởi tạo tất cả 4 agents"""
        try:
            # 1. Technical Analyst
            technical_agent = TechnicalAnalyst(self.api_key)
            self.agent_manager.add_agent("technical", technical_agent)
            
            # 2. Fundamental Analyst
            fundamental_agent = FundamentalAnalyst(self.api_key)
            self.agent_manager.add_agent("fundamental", fundamental_agent)
            
            # 3. PE Valuation Analyst
            pe_agent = PEValuationAnalyst(self.api_key)
            self.agent_manager.add_agent("pe_valuation", pe_agent)
            
            # 4. Investment Advisor
            advisor_agent = InvestmentAdvisor(self.api_key)
            self.agent_manager.add_agent("investment_advisor", advisor_agent)
            
            logger.info("✅ All 4 agents initialized successfully")
            logger.info(self.agent_manager.get_system_status())
            
        except Exception as e:
            logger.error(f"❌ Error initializing agents: {e}")
            raise
    
    def _create_market_context(self, symbol: str, user_profile: Optional[Dict] = None) -> MarketContext:
        """Tạo context thị trường cho phân tích"""
        try:
            # Lấy dữ liệu cơ bản từ VNStockAPI
            api = VNStockAPI(symbol)
            
            # Get latest price data
            price_df = api.get_price_history(start="2024-01-01").tail(1)
            
            # Get ratio data for PE, PB
            ratio_df = api.get_ratio_data().tail(1)
            
            if price_df.empty:
                logger.warning(f"⚠️ No price data for {symbol}")
                current_price = 0
                volume = 0
            else:
                latest_price = price_df.iloc[-1]
                current_price = latest_price['close']
                volume = latest_price['volume']
            
            # Get PE, PB from ratio data
            pe_ratio = None
            pb_ratio = None
            if not ratio_df.empty:
                latest_ratio = ratio_df.iloc[-1]
                pe_ratio = latest_ratio.get('P/E')
                pb_ratio = latest_ratio.get('P/B')
            
            # Determine sector from API
            sector = api.industry.name if api.industry else "Unknown"
            
            # Simple market trend assessment
            market_trend = "Unknown"
            try:
                recent_prices = api.get_price_history(start="2024-01-01")
                if not recent_prices.empty and len(recent_prices) >= 20:
                    ma20 = recent_prices['close'].rolling(20).mean().iloc[-1]
                    current = recent_prices['close'].iloc[-1]
                    market_trend = "Tăng" if current > ma20 * 1.02 else \
                                  "Giảm" if current < ma20 * 0.98 else "Sideway"
            except Exception:
                pass
            
            return MarketContext(
                symbol=symbol,
                current_price=current_price,
                market_cap=0,  # Will be calculated if needed
                volume=volume,
                pe_ratio=pe_ratio,
                pb_ratio=pb_ratio,
                sector=sector,
                market_trend=market_trend,
                news_sentiment="Neutral",  # Can be enhanced with news API
                user_risk_tolerance=user_profile.get('risk_tolerance', 'moderate') if user_profile else 'moderate',
                user_time_horizon=user_profile.get('time_horizon', '6-12 months') if user_profile else '6-12 months',
                user_expected_growth=user_profile.get('expected_growth') if user_profile else None
            )
            
        except Exception as e:
            logger.error(f"❌ Error creating market context for {symbol}: {e}")
            # Return default context to prevent pipeline failure
            return MarketContext(
                symbol=symbol,
                current_price=0,
                market_cap=0,
                volume=0,
                pe_ratio=None,
                pb_ratio=None,
                sector="Unknown",
                market_trend="Unknown",
                news_sentiment="Neutral",
                user_risk_tolerance="moderate",
                user_time_horizon="6-12 months"
            )
    
    async def analyze_comprehensive(self, symbol: str, 
                                  user_profile: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Phân tích toàn diện với 4 agents
        
        Workflow:
        1. Technical + Fundamental + PE Valuation (song song)
        2. Investment Advisor (sử dụng kết quả từ 3 agents trước)
        
        Returns:
            Dict chứa kết quả từ tất cả agents và consensus cuối cùng
        """
        logger.info(f"🚀 Starting comprehensive 4-agent analysis for {symbol}")
        
        if not self.agent_manager.is_complete():
            missing = [t for t in self.agent_manager.analysis_order if t not in self.agent_manager.agents]
            raise ValueError(f"Missing agents for analysis: {missing}")
        
        # Tạo market context
        context = self._create_market_context(symbol, user_profile)
        logger.info(f"📊 Market context created: {context.current_price:,.0f} VND, {context.sector}")
        
        try:
            # Chạy comprehensive analysis
            result = await self.agent_manager.run_comprehensive_analysis(symbol, context)
            
            # Log summary
            successful_analyses = sum(1 for analysis in result['individual_analyses'].values() 
                                    if analysis.confidence_level > 0)
            logger.info(f"✅ Analysis completed: {successful_analyses}/4 agents successful")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Comprehensive analysis failed for {symbol}: {e}")
            raise
    
    async def analyze_single_agent(self, symbol: str, agent_type: str,
                                 user_profile: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Phân tích bằng một agent đơn lẻ (cho testing hoặc specific analysis)
        """
        logger.info(f"🔍 Single agent analysis: {agent_type} for {symbol}")
        
        agent = self.agent_manager.get_agent(agent_type)
        if not agent:
            raise ValueError(f"Agent '{agent_type}' not found")
        
        context = self._create_market_context(symbol, user_profile)
        
        try:
            result = await agent.analyze(symbol, context)
            
            return {
                "symbol": symbol,
                "agent_type": agent_type,
                "result": result,
                "context": context,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"❌ Single agent analysis failed: {e}")
            raise
    
    def get_quick_overview(self, symbol: str) -> Dict[str, Any]:
        """
        Lấy overview nhanh mà không sử dụng AI (tiết kiệm cost)
        Chỉ sử dụng data processing, không generate AI response
        """
        logger.info(f"⚡ Quick overview for {symbol}")
        
        try:
            api = VNStockAPI(symbol)
            
            # Basic data
            overview = {
                "symbol": symbol,
                "timestamp": datetime.now(),
                "data_sources": {},
                "quick_metrics": {},
                "status": "success"
            }
            
            # Price data
            try:
                price_df = api.get_price_history(add_tech=True, start="2024-01-01")
                if not price_df.empty:
                    latest = price_df.iloc[-1]
                    overview["quick_metrics"].update({
                        "current_price": latest['close'],
                        "change_1d": ((latest['close'] - price_df.iloc[-2]['close']) / price_df.iloc[-2]['close'] * 100) if len(price_df) >= 2 else 0,
                        "volume": latest['volume'],
                        "rsi": latest.get('RSI14', 0),
                        "ma20": latest.get('MA20', 0)
                    })
                    overview["data_sources"]["price"] = len(price_df)
            except Exception as e:
                logger.warning(f"Price data error: {e}")
                overview["data_sources"]["price"] = 0
            
            # Ratio data
            try:
                ratio_df = api.get_ratio_data()
                if not ratio_df.empty:
                    latest_ratio = ratio_df.iloc[-1]
                    overview["quick_metrics"].update({
                        "pe": latest_ratio.get('P/E', 0),
                        "pb": latest_ratio.get('P/B', 0),
                        "roe": latest_ratio.get('ROE (%)', 0),
                        "eps": latest_ratio.get('EPS (VND)', 0)
                    })
                    overview["data_sources"]["ratio"] = len(ratio_df)
            except Exception as e:
                logger.warning(f"Ratio data error: {e}")
                overview["data_sources"]["ratio"] = 0
            
            # PE Real data
            try:
                pe_df = api.compute_pe_real()
                if not pe_df.empty:
                    latest_pe = pe_df.iloc[-1]
                    overview["quick_metrics"]["pe_real"] = latest_pe.get('PE_Real', 0)
                    overview["data_sources"]["pe_real"] = len(pe_df)
            except Exception as e:
                logger.warning(f"PE real data error: {e}")
                overview["data_sources"]["pe_real"] = 0
            
            # Quick assessment
            metrics = overview["quick_metrics"]
            quick_signals = []
            
            if metrics.get("rsi", 50) > 70:
                quick_signals.append("RSI quá mua")
            elif metrics.get("rsi", 50) < 30:
                quick_signals.append("RSI quá bán")
            
            if metrics.get("pe", 0) > 0:
                if metrics["pe"] < 10:
                    quick_signals.append("PE thấp")
                elif metrics["pe"] > 25:
                    quick_signals.append("PE cao")
            
            overview["quick_signals"] = quick_signals
            overview["data_quality"] = sum(1 for v in overview["data_sources"].values() if v > 0) / 4
            
            return overview
            
        except Exception as e:
            logger.error(f"❌ Quick overview error for {symbol}: {e}")
            return {
                "symbol": symbol,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now()
            }
    
    async def batch_analysis(self, symbols: List[str],
                           user_profile: Optional[Dict] = None,
                           max_concurrent: int = 3) -> Dict[str, Any]:
        """
        Phân tích hàng loạt nhiều cổ phiếu
        Giới hạn số lượng đồng thời để tránh rate limiting
        """
        logger.info(f"🔄 Batch analysis for {len(symbols)} symbols")
        
        if len(symbols) > 20:
            logger.warning("⚠️ Too many symbols, limiting to first 20")
            symbols = symbols[:20]
        
        # Semaphore để giới hạn concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_with_semaphore(symbol):
            async with semaphore:
                try:
                    return await self.analyze_comprehensive(symbol, user_profile)
                except Exception as e:
                    logger.error(f"❌ Batch analysis failed for {symbol}: {e}")
                    return {
                        "symbol": symbol,
                        "error": str(e),
                        "timestamp": datetime.now()
                    }
        
        # Tạo và chạy tasks
        tasks = [analyze_with_semaphore(symbol) for symbol in symbols]
        
        results = {}
        completed = 0
        
        # Process results as they complete
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            symbol = result.get('symbol', f'unknown_{i}')
            results[symbol] = result
            completed += 1
            logger.info(f"✅ Batch progress: {completed}/{len(symbols)} - {symbol}")
        
        return {
            "batch_results": results,
            "summary": {
                "total_requested": len(symbols),
                "completed": completed,
                "successful": sum(1 for r in results.values() if 'error' not in r),
                "failed": sum(1 for r in results.values() if 'error' in r)
            },
            "timestamp": datetime.now()
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Lấy trạng thái hệ thống"""
        return {
            "pipeline_version": "4-Agent System v2.0",
            "api_key_configured": bool(self.api_key),
            "agents_status": self.agent_manager.get_system_status(),
            "supported_analyses": [
                "comprehensive_analysis",
                "single_agent_analysis", 
                "quick_overview",
                "batch_analysis"
            ],
            "timestamp": datetime.now()
        }
import groq
import json
import re
from typing import Dict, List, Optional
from ..utils.logging_utils import setup_logger
from ..config.settings import settings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from httpx import HTTPStatusError

# Set up logger for this module
logger = setup_logger("AIAnalysisService")

class AIAnalysisService:
    """Service for AI-powered market analysis using Groq."""
    
    def __init__(self):
        """Initialize the AI analysis service with API client."""
        self.api_key = settings.GROQ_API_KEY
        self.model_name = settings.MODEL_NAME
        self.client = None
        
        # Initialize usage tracker
        try:
            from ..database.usage_tracker import UsageTracker
            self.usage_tracker = UsageTracker()
        except ImportError:
            logger.warning("Usage tracker not available")
            self.usage_tracker = None
        
        # Cost estimation (adjust based on actual Groq pricing)
        self.groq_cost_per_1k_tokens = settings.GROQ_COST_PER_1K_TOKENS
        
        self.initialize_client()
        
    def initialize_client(self):
        """Initialize the Groq API client."""
        try:
            logger.info("Initializing Groq client")
            self.client = groq.Groq(api_key=self.api_key)
            logger.info("Groq client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {str(e)}")
            self.client = None
    
    def is_initialized(self):
        """Check if the client was initialized successfully."""
        return self.client is not None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=15),
        retry=retry_if_exception_type(HTTPStatusError),
        before_sleep=lambda retry_state: logger.info(
            f"Retrying API call (attempt {retry_state.attempt_number}) after {retry_state.idle_for}s"
        )
    )
    def _call_groq_api(self, ticker: str, analysis_prompt: str) -> dict:
        """Call the Groq API with retry logic."""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional financial analyst specializing in technical analysis. "
                        "Return a JSON object with exactly two keys: 'action' (a string) and 'justification' "
                        "(an object with exactly six fields: current_trend, bollinger_bands, vwap, price_momentum, "
                        "volume, overall_analysis). Use these exact field names with underscores, not camelCase or other variations. "
                        "Each field must contain plain text with no markdown, HTML, or formatting. If data for a specific analysis "
                        "is not available, state 'Data not available for [field] analysis.' Do not include additional or differently "
                        "named fields."
                    )
                },
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.05,
            max_tokens=2048,
            response_format={"type": "json_object"}
        )
        return response

    def _clean_response_text(self, text: str) -> str:
        """Clean response text by removing markdown, HTML, and unwanted formatting."""
        if not text:
            return text
        text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'\*([^\*]+)\*', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        text = re.sub(r'#+\s*', '', text)
        text = re.sub(r'-\s*', '', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\\n|\\t|\\r', ' ', text)
        text = ' '.join(text.split())
        return text

    def _reformat_justification(self, justification: dict) -> dict:
        """Reformat justification to ensure correct field names and all required fields are present."""
        required_fields = ['current_trend', 'bollinger_bands', 'vwap', 'price_momentum', 'volume', 'overall_analysis']
        key_mapping = {
            'currenttrend': 'current_trend',
            'bollingerbands': 'bollinger_bands',
            'vwap': 'vwap',
            'pricemomentum': 'price_momentum',
            'volume': 'volume',
            'overallanalysis': 'overall_analysis'
        }
        
        # Initialize result with required fields set to default messages
        result = {field: f"Data not available for {field.replace('_', ' ')} analysis." for field in required_fields}
        
        # Map and merge data from the input justification
        for key, value in justification.items():
            mapped_key = key_mapping.get(key.lower(), key)
            if mapped_key in required_fields:
                result[mapped_key] = str(value)
        
        return result    
    def analyze_market_data(self, ticker, data_description):
        """Analyze market data using Groq AI."""
        if not self.is_initialized():
            logger.error("Groq client not initialized")
            return {"action": "Error", "justification": "AI service not initialized"}
        
        logger.info(f"Analyzing market data for {ticker}")
        logger.debug(f"Input data description: {data_description}")
        
        analysis_prompt = (
            f"You are a Stock Trader specializing in Technical Analysis at a top financial institution. "
            f"Analyze the stock chart for {ticker} based on the following data:\n\n{data_description}\n\n"
            f"Provide a detailed justification by addressing each of the following points explicitly:\n"
            f"1. Current Trend: Analyze the current trend based on the price relative to the 20-Day SMA and 20-Day EMA.\n"
            f"2. Bollinger Bands: Examine the Bollinger Bands to determine if the price is near the upper, middle, or lower band.\n"
            f"3. VWAP: Compare the current price to the VWAP to assess if the stock is overvalued or undervalued.\n"
            f"4. Price Momentum: Evaluate the price momentum using the 52-week high and low, and the recent price change.\n"
            f"5. Volume: Consider the trading volume to gauge market interest and conviction.\n"
            f"6. Overall Analysis: Summarize the key points from the above analyses and justify the recommended action.\n\n"
            f"Based on your analysis, provide a recommendation from the following options: 'Strong Buy', 'Buy', 'Weak Buy', "
            f"'Hold', 'Weak Sell', 'Sell', or 'Strong Sell'.\n\n"
            f"Return your output as a JSON object with exactly two keys: 'action' (a string) and 'justification' "
            f"(an object with exactly six fields: current_trend, bollinger_bands, vwap, price_momentum, volume, overall_analysis). "
            f"Use these exact field names with underscores. Each field must contain plain text with no markdown, HTML, or formatting. "
            f"If data for a specific analysis is not available, state 'Data not available for [field] analysis.'"
        )

        try:
            logger.info(f"Calling Groq API for {ticker} analysis")
            response = self._call_groq_api(ticker, analysis_prompt)
            logger.info("Groq API call successful")
            
            result_text = response.choices[0].message.content
            logger.debug(f"Raw API response: {result_text}")
            
            cleaned_text = self._clean_response_text(result_text)
            logger.debug(f"Cleaned API response: {cleaned_text}")
            
            result = json.loads(cleaned_text)
            
            if not isinstance(result, dict) or 'action' not in result or 'justification' not in result:
                logger.warning("Invalid response structure, reformatting")
                result = {
                    "action": result.get("action", "Unknown"),
                    "justification": self._reformat_justification({})
                }
            else:
                # Apply reformatting immediately to ensure correct fields
                result['justification'] = self._reformat_justification(result['justification'])
                logger.debug(f"Final result: {json.dumps(result, indent=2)}")
            return result
                
        except json.JSONDecodeError as e:
            error_msg = f"JSON Parsing error: {e}"
            logger.error(error_msg)
            return {
                "action": "Error",
                "justification": self._reformat_justification({})
            }
            
        except Exception as e:
            error_msg = f"General Error in AI analysis: {e}"
            logger.error(error_msg)
            return {
                "action": "Error",
                "justification": self._reformat_justification({})
            }
    def analyze_stock_data(self, data, ticker, indicators, user_id: str = None):
        """Analyze stock data with usage tracking and cost control."""
        try:
            # Check user limits before processing if user_id is provided
            if user_id and self.usage_tracker:
                limits_check = self.usage_tracker.check_user_limits(user_id)
                if not limits_check['within_limits']:
                    return self._create_limit_exceeded_message(limits_check)
            
            # Generate data description from pandas DataFrame
            technical_summary = self._generate_data_description(data, ticker, indicators)
            
            # Estimate token usage (rough approximation)
            prompt_tokens = len(technical_summary.split()) * 1.3  # Rough token estimation
            
            # Call the analysis
            result = self.analyze_market_data(ticker, technical_summary)
            
            # Record usage if user_id is provided and usage tracker is available
            if user_id and self.usage_tracker and isinstance(result, dict):
                # Calculate token usage
                response_text = str(result)
                completion_tokens = len(response_text.split()) * 1.3
                total_tokens = int(prompt_tokens + completion_tokens)
                estimated_cost = (total_tokens / 1000) * self.groq_cost_per_1k_tokens
                
                # Record usage
                self.usage_tracker.record_usage(
                    user_id=user_id,
                    api_service='groq',
                    tokens_used=total_tokens,
                    estimated_cost=estimated_cost,
                    request_type='market_analysis',
                    metadata={
                        'symbol': ticker,
                        'indicators': indicators,
                        'prompt_tokens': int(prompt_tokens),
                        'completion_tokens': int(completion_tokens)
                    }
                )
                
                logger.info(f"Recorded usage for user {user_id}: ${estimated_cost:.4f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in analyze_stock_data: {e}")
            return {
                "action": "Error",
                "justification": "Analysis temporarily unavailable due to technical issues."
            }
    def _create_limit_exceeded_message(self, limits_check: Dict[str, any]) -> str:
        """Create a user-friendly message when limits are exceeded."""
        if limits_check['monthly_usage'] >= limits_check['monthly_limit']:
            return (f"🚫 **Monthly Usage Limit Reached**\n\n"
                   f"You've used ${limits_check['monthly_usage']:.2f} of your "
                   f"${limits_check['monthly_limit']:.2f} monthly AI analysis limit.\n\n"
                   f"Your limit will reset next month.")
        
        elif limits_check['daily_usage'] >= limits_check['daily_limit']:
            return (f"🚫 **Daily Usage Limit Reached**\n\n"
                   f"You've used ${limits_check['daily_usage']:.2f} of your "
                   f"${limits_check['daily_limit']:.2f} daily AI analysis limit.\n\n"
                   f"Your limit will reset tomorrow.")
        
        elif limits_check['hourly_requests'] >= limits_check['hourly_limit']:
            return (f"🚫 **Rate Limit Exceeded**\n\n"
                   f"You've made {limits_check['hourly_requests']} requests in the last hour. "
                   f"Please wait before making another request.\n\n"
                   f"Limit: {limits_check['hourly_limit']} requests per hour.")
        
        return "🚫 **Usage limit exceeded**. Please try again later."
    
    def _generate_data_description(self, data, ticker, indicators):
        """Generate data description from pandas DataFrame for AI analysis."""
        try:
            from ..config.settings import settings
            
            # Check if this is likely a cryptocurrency
            is_crypto = ticker in settings.CRYPTO_SYMBOLS
            
            # Format large numbers with commas for readability
            current_price = data['Close'].iloc[-1]
            formatted_price = f"${current_price:,.2f}"
            price_change = data['Close'].iloc[-1] - data['Close'].iloc[0]
            formatted_change = f"${price_change:,.2f}"
            pct_change = ((data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1) * 100
            high_price = f"${data['High'].max():,.2f}"
            low_price = f"${data['Low'].min():,.2f}"
            
            # Create comprehensive description
            data_description = f"""
            {'Cryptocurrency' if is_crypto else 'Stock'}: {ticker}{'-USD' if is_crypto else ''}
            Date Range: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}
            Current Price: {formatted_price}
            Price Change: {formatted_change} ({pct_change:.2f}%)
            52-week High: {high_price}
            52-week Low: {low_price}
            Volume: {data['Volume'].iloc[-1]:,}
            """
            
            # Add technical indicator data to description
            for ind in indicators:
                if ind == "20-Day SMA":
                    sma_value = data['Close'].rolling(window=20).mean().iloc[-1]
                    data_description += f"\n20-Day SMA: ${sma_value:.2f}"
                elif ind == "20-Day EMA":
                    ema_value = data['Close'].ewm(span=20).mean().iloc[-1]
                    data_description += f"\n20-Day EMA: ${ema_value:.2f}"
                elif ind == "20-Day Bollinger Bands":
                    sma = data['Close'].rolling(window=20).mean().iloc[-1]
                    std = data['Close'].rolling(window=20).std().iloc[-1]
                    bb_upper = sma + 2 * std
                    bb_lower = sma - 2 * std
                    data_description += f"\nBollinger Bands: Upper=${bb_upper:.2f}, Middle=${sma:.2f}, Lower=${bb_lower:.2f}"
                elif ind == "VWAP":
                    vwap_value = (data['Close'] * data['Volume']).sum() / data['Volume'].sum()
                    data_description += f"\nVWAP: ${vwap_value:.2f}"
            
            return data_description
            
        except Exception as e:
            logger.error(f"Error generating data description: {str(e)}")
            return f"Error generating data description for {ticker}"
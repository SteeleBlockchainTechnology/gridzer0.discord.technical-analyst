import groq
import json
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
                {"role": "system", "content": "You are a professional financial analyst specializing in technical analysis."},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.1,
            max_tokens=2048,
            response_format={"type": "json_object"}
        )
        return response

    def analyze_market_data(self, ticker, data_description):
        """Analyze market data using Groq AI."""
        if not self.is_initialized():
            logger.error("Groq client not initialized")
            return {"action": "Error", "justification": "AI service not initialized"}
        
        logger.info(f"Analyzing market data for {ticker}")
        
        # Create analysis prompt
        analysis_prompt = (
            f"You are a Stock Trader specializing in Technical Analysis at a top financial institution. "
            f"Analyze the stock chart for {ticker} based on the following data:\n\n{data_description}\n\n"
            f"Provide a detailed justification of your analysis, explaining what patterns, signals, and trends you observe. "
            f"Then, based solely on the data, provide a recommendation from the following options: "
            f"'Strong Buy', 'Buy', 'Weak Buy', 'Hold', 'Weak Sell', 'Sell', or 'Strong Sell'. "
            f"Return your output as a JSON object with two keys: 'action' and 'justification'."
        )

        try:
            logger.info(f"Calling Groq API for {ticker} analysis")
            
            # Call the Groq API with retry logic
            response = self._call_groq_api(ticker, analysis_prompt)
            
            logger.info("Groq API call successful")
            
            # Get response content from Groq
            result_text = response.choices[0].message.content
            logger.debug(f"API response received, length: {len(result_text) if result_text else 0}")
            
            # Parse JSON from the response text
            logger.debug("Parsing JSON response")
            result = json.loads(result_text)
            
            # Validate that we got the expected format
            if 'action' not in result or 'justification' not in result:
                # If the response doesn't have the expected structure, try to fix it
                if len(result) > 0:
                    # Maybe it has different key names but still usable data
                    keys = list(result.keys())
                    if len(keys) >= 2:
                        # Use whatever two keys we have
                        new_result = {
                            "action": result.get(keys[0], "Unknown"),
                            "justification": result.get(keys[1], "No justification provided")
                        }
                        result = new_result
                    else:
                        # Add missing fields
                        if 'action' not in result:
                            result['action'] = "Unknown"
                        if 'justification' not in result:
                            result['justification'] = "No justification provided"
                else:
                    raise ValueError("Empty or invalid JSON object from response")
            
            return result
                
        except json.JSONDecodeError as e:
            error_msg = f"JSON Parsing error: {e}"
            logger.error(error_msg)
            return {"action": "Error", "justification": f"{error_msg}. Raw response: {result_text if 'result_text' in locals() else 'Unknown'}"}
            
        except ValueError as ve:
            error_msg = f"Value Error: {ve}"
            logger.error(error_msg)
            return {"action": "Error", "justification": f"{error_msg}. Raw response: {result_text if 'result_text' in locals() else 'Unknown'}"}
            
        except Exception as e:
            error_msg = f"General Error in AI analysis: {e}"
            logger.error(error_msg)
            return {"action": "Error", "justification": f"{error_msg}. Raw response: {result_text if 'result_text' in locals() else 'Unknown'}"}
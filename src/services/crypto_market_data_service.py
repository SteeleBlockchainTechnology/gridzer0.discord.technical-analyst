"""
Cryptocurrency market data service using CoinGecko API.
"""
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List
import time
from ..utils.logging_utils import setup_logger
from ..config.settings import settings

# Set up logger for this module
logger = setup_logger("CryptoMarketDataService")

class CryptoMarketDataService:
    """Service for fetching cryptocurrency market data from CoinGecko API."""
    
    def __init__(self):
        """Initialize the crypto market data service."""
        self.base_url = "https://api.coingecko.com/api/v3"
        self.rate_limit_delay = 1.0  # 1 second between requests for free tier
        self.session = requests.Session()
        
        # Cache for coin mappings to avoid repeated API calls
        self._coins_cache = {}
        self._symbol_to_coins = {}  # For handling multiple coins with same symbol
        self._cache_timestamp = None
        self._cache_expiry_hours = 24  # Refresh cache every 24 hours
        
        logger.info("CryptoMarketDataService initialized with CoinGecko API")
          # Initialize the coins cache
        self._load_coins_list()
    
    def _load_coins_list(self) -> bool:
        """Load the complete list of coins from CoinGecko API."""
        try:
            # Check if cache is still valid
            if (self._cache_timestamp and 
                datetime.now() - self._cache_timestamp < timedelta(hours=self._cache_expiry_hours)):
                logger.debug("Using cached coins list")
                return True
            logger.info("Loading coins list from CoinGecko API...")
            time.sleep(self.rate_limit_delay)  # Rate limiting
            
            url = f"{self.base_url}/coins/list"
            headers = {"accept": "application/json"}
            
            # Only add API key if available
            if settings.COINGECKO_API_KEY:
                headers["x-cg-demo-api-key"] = settings.COINGECKO_API_KEY
            
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            coins_data = response.json()
            
            # Build comprehensive coin mapping
            new_cache = {}
            symbol_to_coins = {}  # For handling duplicate symbols
            
            for coin in coins_data:
                symbol = coin.get('symbol', '').upper()
                coin_id = coin.get('id', '')
                coin_name = coin.get('name', '')
                platforms = coin.get('platforms', {})
                
                if symbol and coin_id:
                    coin_info = {
                        'id': coin_id,
                        'name': coin_name,
                        'symbol': symbol,
                        'platforms': platforms
                    }
                    
                    # Handle duplicate symbols by keeping all matches
                    if symbol not in symbol_to_coins:
                        symbol_to_coins[symbol] = []
                    symbol_to_coins[symbol].append(coin_info)
                    
                    # For backwards compatibility, store the first (usually most popular) match
                    if symbol not in new_cache:
                        new_cache[symbol] = coin_info
            
            # Store both mappings
            self._coins_cache = new_cache
            self._symbol_to_coins = symbol_to_coins
            self._cache_timestamp = datetime.now()
            
            logger.info(f"Successfully loaded {len(self._coins_cache)} unique cryptocurrency symbols")
            logger.debug(f"Sample coins: {list(self._coins_cache.keys())[:10]}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading coins list from CoinGecko: {e}")
            return False
    def _get_coin_id(self, symbol: str, coin_name: str = None, contract_address: str = None) -> Optional[str]:
        """
        Convert cryptocurrency symbol to CoinGecko coin ID with disambiguation support.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC')
            coin_name: Optional coin name for disambiguation (e.g., 'Bitcoin')
            contract_address: Optional contract address for exact identification
            
        Returns:
            CoinGecko coin ID or None if not found
        """
        symbol_upper = symbol.upper()
        
        # Ensure we have a coins list loaded
        if not self._coins_cache:
            if not self._load_coins_list():
                logger.error("Failed to load coins list from CoinGecko")
                return None
        
        # If contract address is provided, search by contract address first
        if contract_address:
            coin_id = self._find_coin_by_contract_address(contract_address)
            if coin_id:
                logger.info(f"Found coin ID '{coin_id}' for contract address '{contract_address}'")
                return coin_id
        
        # If coin name is provided, search by symbol + name combination
        if coin_name:
            coin_id = self._find_coin_by_symbol_and_name(symbol_upper, coin_name)
            if coin_id:
                logger.info(f"Found coin ID '{coin_id}' for symbol '{symbol}' and name '{coin_name}'")
                return coin_id
        
        # Fallback to original symbol lookup
        if symbol_upper in self._coins_cache:
            coin_id = self._coins_cache[symbol_upper]['id']
            coin_matches = len(self._symbol_to_coins.get(symbol_upper, []))
            if coin_matches > 1:
                logger.warning(f"Symbol '{symbol}' has {coin_matches} matches. Using first match: '{coin_id}'. "
                             f"Consider providing coin name or contract address for precise identification.")
            else:
                logger.debug(f"Found coin ID '{coin_id}' for symbol '{symbol}'")
            return coin_id
        
        # If not found in cache, try to refresh cache and search again
        logger.info(f"Symbol '{symbol}' not found in cache, refreshing...")
        if self._load_coins_list() and symbol_upper in self._coins_cache:
            coin_id = self._coins_cache[symbol_upper]['id']
            logger.info(f"Found coin ID '{coin_id}' for symbol '{symbol}' after refresh")
            return coin_id
        
        logger.warning(f"No coin ID found for cryptocurrency symbol: {symbol}")
        return None
    
    def _find_coin_by_contract_address(self, contract_address: str) -> Optional[str]:
        """Find coin ID by contract address."""
        if not hasattr(self, '_symbol_to_coins'):
            return None
            
        for symbol_coins in self._symbol_to_coins.values():
            for coin in symbol_coins:
                platforms = coin.get('platforms', {})
                for platform, address in platforms.items():
                    if address.lower() == contract_address.lower():
                        logger.debug(f"Found coin '{coin['id']}' by contract address '{contract_address}' on {platform}")
                        return coin['id']
        return None
    
    def _find_coin_by_symbol_and_name(self, symbol: str, coin_name: str) -> Optional[str]:
        """Find coin ID by symbol and name combination."""
        if not hasattr(self, '_symbol_to_coins'):
            return None
            
        symbol_coins = self._symbol_to_coins.get(symbol, [])
        coin_name_lower = coin_name.lower()
        
        # Try exact name match first
        for coin in symbol_coins:
            if coin['name'].lower() == coin_name_lower:
                logger.debug(f"Found exact name match: '{coin['id']}' for '{symbol}' + '{coin_name}'")
                return coin['id']
        
        # Try partial name match
        for coin in symbol_coins:
            if coin_name_lower in coin['name'].lower() or coin['name'].lower() in coin_name_lower:
                logger.debug(f"Found partial name match: '{coin['id']}' for '{symbol}' + '{coin_name}'")
                return coin['id']
        
        return None
    
    def get_symbol_matches(self, symbol: str) -> List[Dict[str, str]]:
        """Get all coins that match a given symbol."""
        if not hasattr(self, '_symbol_to_coins'):
            return []
        return self._symbol_to_coins.get(symbol.upper(), [])
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported cryptocurrency symbols."""
        if not self._coins_cache:
            if not self._load_coins_list():
                logger.error("Failed to load coins list from CoinGecko")
                return []
        
        return sorted(list(self._coins_cache.keys()))
    
    def is_valid_crypto_symbol(self, symbol: str) -> bool:
        """Check if the given symbol is a valid cryptocurrency symbol."""
        if not self._coins_cache:
            if not self._load_coins_list():
                logger.error("Failed to load coins list from CoinGecko")
                return False
        
        return symbol.upper() in self._coins_cache
    
    def search_coins(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        """Search for coins by symbol or name."""
        if not self._coins_cache:
            if not self._load_coins_list():
                logger.error("Failed to load coins list from CoinGecko")
                return []
        
        query_upper = query.upper()
        matches = []
        
        for symbol, coin_data in self._coins_cache.items():
            # Check if query matches symbol or is in the name
            if (query_upper in symbol or 
                query_upper in coin_data['name'].upper()):
                matches.append(coin_data)
                
                if len(matches) >= limit:
                    break
        
        return matches
    
    def get_coin_info(self, symbol: str) -> Optional[Dict[str, str]]:
        """Get detailed coin information for a symbol."""
        symbol_upper = symbol.upper()
        
        if not self._coins_cache:
            if not self._load_coins_list():
                logger.error("Failed to load coins list from CoinGecko")
                return None
        
        return self._coins_cache.get(symbol_upper)
    
    def refresh_coins_cache(self) -> bool:
        """Manually refresh the coins cache."""
        logger.info("Manually refreshing coins cache...")
        self._cache_timestamp = None  # Force refresh
        return self._load_coins_list()
    
    def get_cache_info(self) -> Dict[str, any]:
        """Get information about the current cache state."""
        return {
            'cache_size': len(self._coins_cache),
            'cache_timestamp': self._cache_timestamp,
            'cache_age_hours': (datetime.now() - self._cache_timestamp).total_seconds() / 3600 if self._cache_timestamp else None,
            'is_cache_expired': (
                self._cache_timestamp is None or 
                datetime.now() - self._cache_timestamp >= timedelta(hours=self._cache_expiry_hours)
            )
        }
    
    def _fetch_historical_data(self, coin_id: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """Fetch historical price data from CoinGecko."""
        try:
            # Convert dates to timestamps
            start_timestamp = int(start_date.timestamp())
            end_timestamp = int(end_date.timestamp())
            
            time.sleep(self.rate_limit_delay)  # Rate limiting
            
            url = f"{self.base_url}/coins/{coin_id}/market_chart/range"
            params = {
                'vs_currency': 'usd',
                'from': start_timestamp,
                'to': end_timestamp
            }
            
            logger.info(f"Fetching historical data for {coin_id} from {start_date.date()} to {end_date.date()}")
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract price data
            prices = data.get('prices', [])
            market_caps = data.get('market_caps', [])
            total_volumes = data.get('total_volumes', [])
            
            if not prices:
                logger.warning(f"No price data returned for {coin_id}")
                return None
            
            # Convert to DataFrame with OHLCV structure (mimicking yfinance format)
            df_data = []
            
            for i, (timestamp, price) in enumerate(prices):
                # Convert timestamp to datetime
                dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
                
                # Get corresponding volume and market cap
                volume = total_volumes[i][1] if i < len(total_volumes) else 0
                market_cap = market_caps[i][1] if i < len(market_caps) else 0
                
                # For daily data, we approximate OHLC from price
                # Note: CoinGecko free tier doesn't provide OHLC data
                df_data.append({
                    'Open': price,
                    'High': price * 1.01,  # Approximate high (1% higher)
                    'Low': price * 0.99,   # Approximate low (1% lower)
                    'Close': price,
                    'Volume': volume,
                    'Market_Cap': market_cap
                })
            
            # Create DataFrame with datetime index
            df = pd.DataFrame(df_data)
            df.index = pd.to_datetime([datetime.fromtimestamp(ts / 1000, tz=timezone.utc) for ts, _ in prices])
            df.index.name = 'Date'
            
            # Convert timezone-aware index to timezone-naive for compatibility
            df.index = df.index.tz_localize(None)
            
            logger.info(f"Successfully fetched {len(df)} records for {coin_id}")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error fetching data for {coin_id}: {e}")            
            return None
        except KeyError as e:
            logger.error(f"Data format error for {coin_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching data for {coin_id}: {e}")
            return None
    
    def fetch_data(self, symbol: str, start_date, end_date, 
                   coin_name: str = None, contract_address: str = None) -> Optional[pd.DataFrame]:
        """
        Fetch cryptocurrency data for the given symbol and date range.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
            start_date: Start date for data retrieval (datetime.date or datetime.datetime)
            end_date: End date for data retrieval (datetime.date or datetime.datetime)
            coin_name: Optional coin name for disambiguation (e.g., 'Bitcoin')
            contract_address: Optional contract address for exact identification
            
        Returns:
            DataFrame with OHLCV data or None if error
        """
        try:
            # Get coin ID from symbol with disambiguation support
            coin_id = self._get_coin_id(symbol, coin_name, contract_address)
            if not coin_id:
                # If disambiguation info was provided, show helpful error message
                if coin_name or contract_address:
                    logger.error(f"Could not find coin ID for symbol: {symbol} "
                               f"(name: {coin_name}, contract: {contract_address})")
                    # Show available matches for this symbol
                    matches = self.get_symbol_matches(symbol)
                    if matches:
                        options_list = [f"{m['name']} (ID: {m['id']})" for m in matches[:5]]
                        logger.info(f"Available options for {symbol}: {options_list}")
                else:
                    logger.error(f"Could not find coin ID for symbol: {symbol}")
                    # Show available matches for this symbol
                    matches = self.get_symbol_matches(symbol)
                    if matches:
                        options_list = [f"{m['name']} (ID: {m['id']})" for m in matches[:5]]
                        logger.info(f"Multiple coins found for {symbol}. Consider providing coin name. "
                                  f"Options: {options_list}")
                return None
            
            # Convert dates to datetime objects with proper timezone handling
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            elif hasattr(start_date, 'date'):  # datetime object
                if start_date.tzinfo is None:
                    start_date = start_date.replace(tzinfo=timezone.utc)
            else:  # date object
                start_date = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            elif hasattr(end_date, 'date'):  # datetime object
                if end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=timezone.utc)
            else:  # date object
                end_date = datetime.combine(end_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            
            logger.info(f"Processed dates: {start_date} to {end_date}")
            
            # Fetch the data
            return self._fetch_historical_data(coin_id, start_date, end_date)
            
        except Exception as e:
            logger.error(f"Error in fetch_data for {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a cryptocurrency symbol."""
        try:
            coin_id = self._get_coin_id(symbol)
            if not coin_id:
                return None
            
            time.sleep(self.rate_limit_delay)  # Rate limiting
            
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            price = data.get(coin_id, {}).get('usd')
            
            return price
            
        except Exception as e:
            logger.error(f"Error fetching current price for {symbol}: {e}")
            return None

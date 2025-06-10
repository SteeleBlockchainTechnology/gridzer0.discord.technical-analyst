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
        
        # Common cryptocurrency symbol mappings
        self.symbol_to_id = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'ADA': 'cardano',
            'DOT': 'polkadot',
            'LINK': 'chainlink',
            'LTC': 'litecoin',
            'BCH': 'bitcoin-cash',
            'XLM': 'stellar',
            'VET': 'vechain',
            'ALGO': 'algorand',
            'ATOM': 'cosmos',
            'AVAX': 'avalanche-2',
            'LUNA': 'terra-luna',
            'SOL': 'solana',
            'MATIC': 'polygon',
            'UNI': 'uniswap',
            'DOGE': 'dogecoin',
            'SHIB': 'shiba-inu',
            'XRP': 'ripple',
            'BNB': 'binancecoin',
            'USDT': 'tether',
            'USDC': 'usd-coin',
            'BUSD': 'binance-usd',
            'AAVE': 'aave',
            'COMP': 'compound-coin',
            'MKR': 'maker',
            'SNX': 'havven',
            'SUSHI': 'sushi',
            'CRV': 'curve-dao-token',
            'YFI': 'yearn-finance',
            '1INCH': '1inch',
            'ENJ': 'enjincoin',
            'MANA': 'decentraland',
            'SAND': 'the-sandbox',
            'AXS': 'axie-infinity',
            'FTM': 'fantom',
            'NEAR': 'near',
            'ICP': 'internet-computer',
            'FLOW': 'flow',
            'XTZ': 'tezos',
            'EOS': 'eos',
            'TRX': 'tron',
            'FIL': 'filecoin',
            'APE': 'apecoin',
            'LDO': 'lido-dao',
            'CRO': 'crypto-com-chain',
            'QNT': 'quant-network',
            'EGLD': 'elrond-erd-2',
            'HBAR': 'hedera-hashgraph',
            'CHZ': 'chiliz',
            'MINA': 'mina-protocol',
            'XMR': 'monero',
            'ETC': 'ethereum-classic',
            'THETA': 'theta-token',
            'APT': 'aptos',
            'OP': 'optimism',
            'ARB': 'arbitrum',
            'SUI': 'sui',
            'PEPE': 'pepe',
            'WLD': 'worldcoin-wld'
        }
        
        logger.info("CryptoMarketDataService initialized with CoinGecko API")
    
    def _get_coin_id(self, symbol: str) -> Optional[str]:
        """Convert cryptocurrency symbol to CoinGecko coin ID."""
        symbol_upper = symbol.upper()
        
        # Check our predefined mapping first
        if symbol_upper in self.symbol_to_id:
            return self.symbol_to_id[symbol_upper]
        
        # If not found, try to search via API
        try:
            time.sleep(self.rate_limit_delay)  # Rate limiting
            url = f"{self.base_url}/search"
            params = {'query': symbol}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            coins = data.get('coins', [])
            
            # Look for exact symbol match
            for coin in coins:
                if coin.get('symbol', '').upper() == symbol_upper:
                    coin_id = coin.get('id')
                    logger.info(f"Found coin ID '{coin_id}' for symbol '{symbol}'")
                    return coin_id
            
            logger.warning(f"No exact match found for cryptocurrency symbol: {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching for coin ID for symbol {symbol}: {e}")
            return None
    
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
    
    def fetch_data(self, symbol: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """
        Fetch cryptocurrency data for the given symbol and date range.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            
        Returns:
            DataFrame with OHLCV data or None if error
        """
        try:
            # Get coin ID from symbol
            coin_id = self._get_coin_id(symbol)
            if not coin_id:
                logger.error(f"Could not find coin ID for symbol: {symbol}")
                return None
            
            # Ensure dates are datetime objects
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, "%Y-%m-%d")
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Add timezone info if not present
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)
            
            # Fetch the data
            return self._fetch_historical_data(coin_id, start_date, end_date)
            
        except Exception as e:
            logger.error(f"Error in fetch_data for {symbol}: {e}")
            return None
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported cryptocurrency symbols."""
        return list(self.symbol_to_id.keys())
    
    def is_valid_crypto_symbol(self, symbol: str) -> bool:
        """Check if the given symbol is a valid cryptocurrency symbol."""
        return symbol.upper() in self.symbol_to_id
    
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

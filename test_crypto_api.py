"""
Test script for CoinGecko API functionality
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.crypto_market_data_service import CryptoMarketDataService
from src.utils.logging_utils import setup_logger

logger = setup_logger("CryptoTest")

async def test_crypto_service():
    """Test the CryptoMarketDataService functionality."""
    print("🔬 Testing CoinGecko API Integration...")
    
    # Initialize the service
    crypto_service = CryptoMarketDataService()
    
    # Test symbols
    test_symbols = ['BTC', 'ETH', 'ADA']
    
    # Date range for testing (last 30 days)
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)
    
    print(f"📅 Testing date range: {start_date.date()} to {end_date.date()}")
    print(f"🪙 Testing symbols: {', '.join(test_symbols)}")
    print("-" * 50)
    
    for symbol in test_symbols:
        print(f"\n🔍 Testing {symbol}...")
        
        try:
            # Test coin ID lookup
            coin_id = crypto_service._get_coin_id(symbol)
            if coin_id:
                print(f"  ✅ Coin ID found: {coin_id}")
            else:
                print(f"  ❌ No coin ID found for {symbol}")
                continue
            
            # Test data fetching
            data = crypto_service.fetch_data(symbol, start_date, end_date)
            
            if data is not None and not data.empty:
                print(f"  ✅ Data fetched successfully: {len(data)} records")
                print(f"  📊 Columns: {list(data.columns)}")
                print(f"  💰 Latest price: ${data['Close'].iloc[-1]:.2f}")
                print(f"  📈 Price range: ${data['Low'].min():.2f} - ${data['High'].max():.2f}")
            else:
                print(f"  ❌ No data returned for {symbol}")
                
        except Exception as e:
            print(f"  ❌ Error testing {symbol}: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Testing supported symbols list...")
    supported = crypto_service.get_supported_symbols()
    print(f"  📋 {len(supported)} supported symbols: {', '.join(supported[:10])}...")
    
    print("\n✨ CoinGecko API test completed!")

if __name__ == "__main__":
    asyncio.run(test_crypto_service())

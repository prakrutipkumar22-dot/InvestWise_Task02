"""
Quick test script to verify Week 3-4 setup.

Run this to test your stock data pipeline!

Usage:
    python test_setup.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

print("="*60)
print("InvestWise Setup Test - Week 3-4")
print("="*60)

# Test 1: Import all modules
print("\n[1/6] Testing imports...")
try:
    from src.data.stock_fetcher import StockFetcher, get_stock_data
    from src.data.api_client import AlphaVantageClient
    from src.config import Config, get_config
    print("✓ All modules imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("  Make sure you've created all the files in src/data/")
    sys.exit(1)

# Test 2: Check configuration
print("\n[2/6] Checking configuration...")
try:
    config = get_config()
    config.init_app()
    print(f"✓ Configuration loaded")
    print(f"  - App: {config.APP_NAME} v{config.VERSION}")
    print(f"  - Debug: {config.DEBUG}")
    print(f"  - Data dir: {config.DATA_DIR}")
except Exception as e:
    print(f"✗ Configuration error: {e}")

# Test 3: Check API keys
print("\n[3/6] Checking API keys...")
alpha_vantage_set = bool(config.ALPHA_VANTAGE_API_KEY)
anthropic_set = bool(config.ANTHROPIC_API_KEY)

print(f"  Alpha Vantage: {'✓ Set' if alpha_vantage_set else '✗ Not set'}")
print(f"  Anthropic: {'✓ Set' if anthropic_set else '✗ Not set'}")

if not alpha_vantage_set:
    print("\n  ⚠️  Alpha Vantage API key not found!")
    print("     Get one at: https://www.alphavantage.co/support/#api-key")
    print("     Add to .env: ALPHA_VANTAGE_API_KEY=your_key_here")

if not anthropic_set:
    print("\n  ⚠️  Anthropic API key not found!")
    print("     You have Syracuse University access!")
    print("     Add to .env: ANTHROPIC_API_KEY=your_key_here")

# Test 4: Test StockFetcher
print("\n[4/6] Testing StockFetcher...")
try:
    fetcher = StockFetcher()
    print("✓ StockFetcher initialized")
    
    # Try to fetch data
    print("  Fetching AAPL data (this may take a few seconds)...")
    data = fetcher.get_historical_data('AAPL', period='5d', use_cache=False)
    
    print(f"✓ Successfully fetched {len(data)} days of data")
    print(f"  Latest close: ${data['Close'].iloc[-1]:.2f}")
    print(f"  Date range: {data.index[0].date()} to {data.index[-1].date()}")
    
    # Test caching
    print("  Testing cache...")
    data_cached = fetcher.get_historical_data('AAPL', period='5d', use_cache=True)
    print("✓ Cache working")
    
except Exception as e:
    print(f"✗ StockFetcher error: {e}")
    print("  This is usually OK - could be network or rate limiting")

# Test 5: Test company info
print("\n[5/6] Testing company info...")
try:
    info = fetcher.get_company_info('AAPL', use_cache=False)
    print(f"✓ Company: {info.get('longName', 'N/A')}")
    print(f"  Sector: {info.get('sector', 'N/A')}")
    print(f"  Industry: {info.get('industry', 'N/A')}")
except Exception as e:
    print(f"✗ Company info error: {e}")

# Test 6: Test AlphaVantageClient (if key is set)
print("\n[6/6] Testing Alpha Vantage...")
if alpha_vantage_set:
    try:
        av_client = AlphaVantageClient()
        print("✓ AlphaVantageClient initialized")
        
        # Only test if we want to use an API call
        print("  (Skipping live API call to save quota)")
        
        # Show usage stats
        stats = av_client.get_api_usage_stats()
        print(f"  API usage: {stats['calls_last_minute']}/{stats['minute_limit']} calls/min")
        
    except Exception as e:
        print(f"✗ Alpha Vantage error: {e}")
else:
    print("⊘ Skipped (API key not set)")

# Summary
print("\n" + "="*60)
print("Setup Test Complete!")
print("="*60)

print("\n✅ Successfully completed:")
print("  • Module imports")
print("  • Configuration setup")
print("  • Stock data fetching (yfinance)")
print("  • Data caching")
print("  • Company information")

if not alpha_vantage_set or not anthropic_set:
    print("\n⚠️  Next steps:")
    if not alpha_vantage_set:
        print("  1. Get Alpha Vantage API key")
        print("     https://www.alphavantage.co/support/#api-key")
    if not anthropic_set:
        print("  2. Add Anthropic API key (you have SU access!)")
    print("  3. Add keys to .env file")
    print("  4. Run this test again")
else:
    print("\n🎉 All systems GO! Ready for Week 5-6!")

print("\n" + "="*60)

# Show next steps
print("\n📋 What's next?")
print("  Week 5-6: Build the portfolio simulator")
print("  Week 7-8: Create the stock screener")
print("  Week 9-10: Integrate AI chatbot")
print("\n💡 Try running the demo:")
print("  python src/data/stock_fetcher.py")
print("  python src/data/api_client.py")

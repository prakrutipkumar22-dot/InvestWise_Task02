"""
Unit tests for StockFetcher module.

Run with: pytest tests/test_data/test_stock_fetcher.py -v
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.data.stock_fetcher import StockFetcher, StockDataError


@pytest.fixture
def fetcher():
    """Create a StockFetcher instance for testing."""
    return StockFetcher(cache_dir="data/cache/test")


@pytest.fixture
def cleanup_cache(fetcher):
    """Clean up test cache after tests."""
    yield
    fetcher.clear_cache()


class TestStockFetcherBasics:
    """Test basic functionality."""
    
    def test_initialization(self, fetcher):
        """Test StockFetcher initializes correctly."""
        assert fetcher.cache_dir.exists()
        assert fetcher.cache_dir.is_dir()
    
    def test_valid_periods(self, fetcher):
        """Test valid period constants."""
        assert '1y' in fetcher.VALID_PERIODS
        assert '5y' in fetcher.VALID_PERIODS
        assert 'max' in fetcher.VALID_PERIODS
    
    def test_valid_intervals(self, fetcher):
        """Test valid interval constants."""
        assert '1d' in fetcher.VALID_INTERVALS
        assert '1wk' in fetcher.VALID_INTERVALS
        assert '1mo' in fetcher.VALID_INTERVALS


class TestHistoricalData:
    """Test historical data fetching."""
    
    def test_get_historical_data_valid_symbol(self, fetcher, cleanup_cache):
        """Test fetching data for a valid symbol."""
        data = fetcher.get_historical_data('AAPL', period='1mo', use_cache=False)
        
        assert isinstance(data, pd.DataFrame)
        assert not data.empty
        assert 'Close' in data.columns
        assert 'Volume' in data.columns
        assert len(data) > 0
    
    def test_get_historical_data_invalid_symbol(self, fetcher):
        """Test fetching data for an invalid symbol."""
        with pytest.raises(StockDataError):
            fetcher.get_historical_data('INVALIDXYZ123', period='1mo', use_cache=False)
    
    def test_get_historical_data_empty_symbol(self, fetcher):
        """Test fetching data with empty symbol."""
        with pytest.raises(StockDataError):
            fetcher.get_historical_data('', period='1mo')
    
    def test_get_historical_data_invalid_period(self, fetcher):
        """Test fetching data with invalid period."""
        with pytest.raises(StockDataError):
            fetcher.get_historical_data('AAPL', period='invalid_period')
    
    def test_get_historical_data_invalid_interval(self, fetcher):
        """Test fetching data with invalid interval."""
        with pytest.raises(StockDataError):
            fetcher.get_historical_data('AAPL', period='1mo', interval='invalid')
    
    def test_get_historical_data_different_periods(self, fetcher):
        """Test fetching data for different time periods."""
        periods = ['1mo', '3mo', '6mo', '1y']
        
        for period in periods:
            data = fetcher.get_historical_data('AAPL', period=period, use_cache=False)
            assert not data.empty
            assert 'Close' in data.columns
    
    def test_data_structure(self, fetcher):
        """Test that returned data has correct structure."""
        data = fetcher.get_historical_data('AAPL', period='1mo', use_cache=False)
        
        # Check required columns
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_columns:
            assert col in data.columns
        
        # Check index is DatetimeIndex
        assert isinstance(data.index, pd.DatetimeIndex)
        
        # Check no all-NaN columns
        assert not data['Close'].isna().all()
    
    def test_data_values_reasonable(self, fetcher):
        """Test that data values are reasonable."""
        data = fetcher.get_historical_data('AAPL', period='1mo', use_cache=False)
        
        # Close prices should be positive
        assert (data['Close'] > 0).all()
        
        # High should be >= Low
        assert (data['High'] >= data['Low']).all()
        
        # Volume should be non-negative
        assert (data['Volume'] >= 0).all()


class TestCaching:
    """Test caching functionality."""
    
    def test_cache_creation(self, fetcher, cleanup_cache):
        """Test that cache files are created."""
        # Fetch data with caching enabled
        data1 = fetcher.get_historical_data('AAPL', period='1mo', use_cache=True)
        
        # Check cache file exists
        cache_file = fetcher._get_cache_filename('AAPL', '1mo', '1d')
        assert cache_file.exists()
    
    def test_cache_retrieval(self, fetcher, cleanup_cache):
        """Test that cached data is retrieved correctly."""
        # First fetch (creates cache)
        data1 = fetcher.get_historical_data('AAPL', period='1mo', use_cache=True)
        
        # Second fetch (should use cache)
        data2 = fetcher.get_historical_data('AAPL', period='1mo', use_cache=True)
        
        # Data should be identical
        pd.testing.assert_frame_equal(data1, data2)
    
    def test_cache_bypass(self, fetcher, cleanup_cache):
        """Test that cache can be bypassed."""
        # Fetch with cache
        data1 = fetcher.get_historical_data('AAPL', period='1mo', use_cache=True)
        
        # Fetch without cache
        data2 = fetcher.get_historical_data('AAPL', period='1mo', use_cache=False)
        
        # Both should have data
        assert not data1.empty
        assert not data2.empty
    
    def test_clear_cache_specific(self, fetcher, cleanup_cache):
        """Test clearing cache for specific symbol."""
        # Create cache for multiple symbols
        fetcher.get_historical_data('AAPL', period='1mo')
        fetcher.get_historical_data('MSFT', period='1mo')
        
        # Clear only AAPL
        deleted = fetcher.clear_cache('AAPL')
        assert deleted > 0
    
    def test_clear_cache_all(self, fetcher, cleanup_cache):
        """Test clearing all cache."""
        # Create cache for multiple symbols
        fetcher.get_historical_data('AAPL', period='1mo')
        fetcher.get_historical_data('MSFT', period='1mo')
        
        # Clear all
        deleted = fetcher.clear_cache()
        assert deleted >= 2


class TestCompanyInfo:
    """Test company information fetching."""
    
    def test_get_company_info_valid(self, fetcher):
        """Test getting company info for valid symbol."""
        info = fetcher.get_company_info('AAPL', use_cache=False)
        
        assert isinstance(info, dict)
        assert 'symbol' in info or 'longName' in info
    
    def test_get_company_info_invalid(self, fetcher):
        """Test getting company info for invalid symbol."""
        with pytest.raises(StockDataError):
            fetcher.get_company_info('INVALIDXYZ123', use_cache=False)
    
    def test_company_info_structure(self, fetcher):
        """Test that company info has expected fields."""
        info = fetcher.get_company_info('AAPL', use_cache=False)
        
        # Check for some common fields (may vary)
        expected_fields = ['symbol', 'longName', 'sector', 'industry']
        found_fields = [f for f in expected_fields if f in info]
        
        assert len(found_fields) > 0


class TestCurrentPrice:
    """Test current price fetching."""
    
    def test_get_current_price_valid(self, fetcher):
        """Test getting current price for valid symbol."""
        price = fetcher.get_current_price('AAPL')
        
        assert isinstance(price, float)
        assert price > 0
    
    def test_get_current_price_invalid(self, fetcher):
        """Test getting current price for invalid symbol."""
        with pytest.raises(StockDataError):
            fetcher.get_current_price('INVALIDXYZ123')
    
    def test_current_price_reasonable(self, fetcher):
        """Test that current price is reasonable."""
        price = fetcher.get_current_price('AAPL')
        
        # AAPL price should be between $50 and $500 (reasonable range)
        assert 50 < price < 500


class TestMultipleStocks:
    """Test fetching multiple stocks."""
    
    def test_get_multiple_stocks_valid(self, fetcher):
        """Test fetching multiple valid symbols."""
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        data = fetcher.get_multiple_stocks(symbols, period='1mo')
        
        assert isinstance(data, dict)
        assert len(data) == len(symbols)
        
        for symbol in symbols:
            assert symbol in data
            assert isinstance(data[symbol], pd.DataFrame)
            assert not data[symbol].empty
    
    def test_get_multiple_stocks_with_invalid(self, fetcher):
        """Test fetching mix of valid and invalid symbols."""
        symbols = ['AAPL', 'INVALIDXYZ', 'MSFT']
        data = fetcher.get_multiple_stocks(symbols, period='1mo')
        
        # Should return data for valid symbols only
        assert 'AAPL' in data
        assert 'MSFT' in data
        assert 'INVALIDXYZ' not in data


class TestSearchSymbols:
    """Test symbol search functionality."""
    
    def test_search_by_symbol(self, fetcher):
        """Test searching by ticker symbol."""
        results = fetcher.search_symbols('AAPL')
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert any(r['symbol'] == 'AAPL' for r in results)
    
    def test_search_by_name(self, fetcher):
        """Test searching by company name."""
        results = fetcher.search_symbols('Apple')
        
        assert isinstance(results, list)
        # Should find Apple
        assert any('Apple' in r['name'] for r in results)
    
    def test_search_limit(self, fetcher):
        """Test search result limit."""
        results = fetcher.search_symbols('a', limit=5)
        
        assert len(results) <= 5


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_get_stock_data_function(self):
        """Test get_stock_data convenience function."""
        from src.data.stock_fetcher import get_stock_data
        
        data = get_stock_data('AAPL', '1mo')
        assert isinstance(data, pd.DataFrame)
        assert not data.empty
    
    def test_get_current_price_function(self):
        """Test get_current_price convenience function."""
        from src.data.stock_fetcher import get_current_price
        
        price = get_current_price('AAPL')
        assert isinstance(price, float)
        assert price > 0


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_symbol_case_insensitive(self, fetcher):
        """Test that symbol lookup is case-insensitive."""
        data1 = fetcher.get_historical_data('aapl', period='1mo', use_cache=False)
        data2 = fetcher.get_historical_data('AAPL', period='1mo', use_cache=False)
        
        assert len(data1) == len(data2)
    
    def test_symbol_with_whitespace(self, fetcher):
        """Test that whitespace is handled correctly."""
        data = fetcher.get_historical_data(' AAPL ', period='1mo', use_cache=False)
        assert not data.empty
    
    def test_concurrent_fetches(self, fetcher):
        """Test that multiple fetches don't interfere."""
        data1 = fetcher.get_historical_data('AAPL', period='1mo', use_cache=False)
        data2 = fetcher.get_historical_data('MSFT', period='1mo', use_cache=False)
        
        assert not data1.empty
        assert not data2.empty
        assert len(data1) > 0
        assert len(data2) > 0


# Performance tests (marked as slow)
@pytest.mark.slow
class TestPerformance:
    """Performance tests (run with: pytest -m slow)."""
    
    def test_cache_performance(self, fetcher, cleanup_cache):
        """Test that caching improves performance."""
        import time
        
        # First fetch (no cache)
        start = time.time()
        data1 = fetcher.get_historical_data('AAPL', period='1y', use_cache=True)
        first_fetch_time = time.time() - start
        
        # Second fetch (with cache)
        start = time.time()
        data2 = fetcher.get_historical_data('AAPL', period='1y', use_cache=True)
        cached_fetch_time = time.time() - start
        
        # Cached fetch should be significantly faster
        assert cached_fetch_time < first_fetch_time * 0.5
        print(f"\nFirst fetch: {first_fetch_time:.3f}s")
        print(f"Cached fetch: {cached_fetch_time:.3f}s")
        print(f"Speedup: {first_fetch_time/cached_fetch_time:.1f}x")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])

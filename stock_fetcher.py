"""
Stock Data Fetcher Module
Fetches historical and real-time stock data using yfinance.

Author: InvestWise Team
Date: December 2025
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Union
import logging
import json
import os
from pathlib import Path
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockDataError(Exception):
    """Custom exception for stock data errors."""
    pass


class StockFetcher:
    """
    Fetches and manages stock market data.
    
    Features:
    - Historical price data
    - Company information
    - Real-time quotes
    - Data validation
    - Local caching
    
    Example:
        >>> fetcher = StockFetcher()
        >>> data = fetcher.get_historical_data('AAPL', period='1y')
        >>> print(data.head())
    """
    
    # Valid periods for yfinance
    VALID_PERIODS = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
    VALID_INTERVALS = ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo']
    
    def __init__(self, cache_dir: str = "data/cache"):
        """
        Initialize the StockFetcher.
        
        Args:
            cache_dir: Directory to store cached data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"StockFetcher initialized with cache at {self.cache_dir}")
    
    def get_historical_data(
        self, 
        symbol: str, 
        period: str = "1y",
        interval: str = "1d",
        use_cache: bool = True,
        cache_ttl_hours: int = 24
    ) -> pd.DataFrame:
        """
        Fetch historical stock price data.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
            period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            interval: Data interval ('1d', '1wk', '1mo' recommended for long periods)
            use_cache: Whether to use cached data
            cache_ttl_hours: Cache time-to-live in hours
            
        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume, Dividends, Stock Splits
            
        Raises:
            StockDataError: If data cannot be fetched or is invalid
            
        Example:
            >>> fetcher = StockFetcher()
            >>> df = fetcher.get_historical_data('AAPL', period='1y')
            >>> print(f"Got {len(df)} days of data")
        """
        # Validate inputs
        symbol = symbol.upper().strip()
        if not symbol:
            raise StockDataError("Symbol cannot be empty")
        
        if period not in self.VALID_PERIODS:
            raise StockDataError(f"Invalid period. Must be one of: {self.VALID_PERIODS}")
        
        if interval not in self.VALID_INTERVALS:
            raise StockDataError(f"Invalid interval. Must be one of: {self.VALID_INTERVALS}")
        
        # Check cache first
        if use_cache:
            cached_data = self._get_from_cache(symbol, period, interval, cache_ttl_hours)
            if cached_data is not None:
                logger.info(f"Returning cached data for {symbol}")
                return cached_data
        
        # Fetch from yfinance
        logger.info(f"Fetching {symbol} data for period={period}, interval={interval}")
        
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                raise StockDataError(f"No data returned for {symbol}. Symbol may be invalid.")
            
            # Validate data
            self._validate_data(data, symbol)
            
            # Cache the data
            if use_cache:
                self._save_to_cache(data, symbol, period, interval)
            
            logger.info(f"Successfully fetched {len(data)} records for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            raise StockDataError(f"Failed to fetch data for {symbol}: {str(e)}")
    
    def get_company_info(self, symbol: str, use_cache: bool = True) -> Dict:
        """
        Fetch company information and fundamentals.
        
        Args:
            symbol: Stock ticker symbol
            use_cache: Whether to use cached data
            
        Returns:
            Dictionary containing company info
            
        Example:
            >>> fetcher = StockFetcher()
            >>> info = fetcher.get_company_info('AAPL')
            >>> print(info['longName'])
            'Apple Inc.'
        """
        symbol = symbol.upper().strip()
        
        # Check cache
        if use_cache:
            cache_file = self.cache_dir / f"{symbol}_info.json"
            if cache_file.exists():
                cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
                if cache_age < timedelta(days=7):  # Info cached for 7 days
                    logger.info(f"Returning cached info for {symbol}")
                    with open(cache_file, 'r') as f:
                        return json.load(f)
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or 'symbol' not in info:
                raise StockDataError(f"No info available for {symbol}")
            
            # Cache the info
            if use_cache:
                cache_file = self.cache_dir / f"{symbol}_info.json"
                with open(cache_file, 'w') as f:
                    json.dump(info, f, indent=2)
            
            logger.info(f"Fetched info for {symbol}")
            return info
            
        except Exception as e:
            logger.error(f"Error fetching info for {symbol}: {e}")
            raise StockDataError(f"Failed to fetch info for {symbol}: {str(e)}")
    
    def get_current_price(self, symbol: str) -> float:
        """
        Get the current/latest price for a symbol.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Current price as float
            
        Example:
            >>> fetcher = StockFetcher()
            >>> price = fetcher.get_current_price('AAPL')
            >>> print(f"Current price: ${price:.2f}")
        """
        symbol = symbol.upper().strip()
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Try to get real-time price
            data = ticker.history(period='1d', interval='1m')
            if not data.empty:
                return float(data['Close'].iloc[-1])
            
            # Fallback to daily close
            data = ticker.history(period='1d')
            if not data.empty:
                return float(data['Close'].iloc[-1])
            
            # Last resort: from info
            info = ticker.info
            if 'currentPrice' in info:
                return float(info['currentPrice'])
            
            raise StockDataError(f"Could not get price for {symbol}")
            
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            raise StockDataError(f"Failed to get price for {symbol}: {str(e)}")
    
    def get_multiple_stocks(
        self, 
        symbols: List[str], 
        period: str = "1y",
        interval: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple stocks.
        
        Args:
            symbols: List of ticker symbols
            period: Time period
            interval: Data interval
            
        Returns:
            Dictionary mapping symbol to DataFrame
            
        Example:
            >>> fetcher = StockFetcher()
            >>> data = fetcher.get_multiple_stocks(['AAPL', 'MSFT', 'GOOGL'])
            >>> for symbol, df in data.items():
            ...     print(f"{symbol}: {len(df)} records")
        """
        results = {}
        
        for symbol in symbols:
            try:
                results[symbol] = self.get_historical_data(symbol, period, interval)
                # Be nice to the API
                time.sleep(0.5)
            except StockDataError as e:
                logger.warning(f"Skipping {symbol}: {e}")
                continue
        
        return results
    
    def search_symbols(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for stock symbols by company name.
        
        Args:
            query: Search query (company name or symbol)
            limit: Maximum number of results
            
        Returns:
            List of dictionaries with symbol info
            
        Note:
            This is a basic implementation. For production, consider using
            a dedicated search API.
        """
        # Common tickers for demonstration
        # In production, you'd use a proper search API
        common_stocks = {
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corporation',
            'GOOGL': 'Alphabet Inc.',
            'AMZN': 'Amazon.com Inc.',
            'TSLA': 'Tesla Inc.',
            'META': 'Meta Platforms Inc.',
            'NVDA': 'NVIDIA Corporation',
            'JPM': 'JPMorgan Chase & Co.',
            'V': 'Visa Inc.',
            'WMT': 'Walmart Inc.',
            'SPY': 'SPDR S&P 500 ETF',
            'QQQ': 'Invesco QQQ Trust',
            'VOO': 'Vanguard S&P 500 ETF',
        }
        
        query = query.lower()
        results = []
        
        for symbol, name in common_stocks.items():
            if query in symbol.lower() or query in name.lower():
                results.append({
                    'symbol': symbol,
                    'name': name
                })
                
                if len(results) >= limit:
                    break
        
        return results
    
    def _validate_data(self, data: pd.DataFrame, symbol: str) -> None:
        """
        Validate fetched stock data.
        
        Args:
            data: DataFrame to validate
            symbol: Stock symbol for error messages
            
        Raises:
            StockDataError: If data is invalid
        """
        if data.empty:
            raise StockDataError(f"Empty data returned for {symbol}")
        
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            raise StockDataError(f"Missing required columns for {symbol}: {missing_columns}")
        
        # Check for all NaN values
        if data['Close'].isna().all():
            raise StockDataError(f"All Close prices are NaN for {symbol}")
        
        # Check for unrealistic values
        if (data['Close'] <= 0).any():
            logger.warning(f"Found non-positive prices for {symbol}")
        
        # Check for extreme volatility (might indicate data error)
        if len(data) > 1:
            returns = data['Close'].pct_change()
            if (returns.abs() > 0.5).any():  # 50% daily change
                logger.warning(f"Extreme price changes detected for {symbol}")
    
    def _get_cache_filename(self, symbol: str, period: str, interval: str) -> Path:
        """Generate cache filename."""
        return self.cache_dir / f"{symbol}_{period}_{interval}.parquet"
    
    def _get_from_cache(
        self, 
        symbol: str, 
        period: str, 
        interval: str,
        ttl_hours: int
    ) -> Optional[pd.DataFrame]:
        """
        Retrieve data from cache if available and fresh.
        
        Returns:
            DataFrame if cache hit, None otherwise
        """
        cache_file = self._get_cache_filename(symbol, period, interval)
        
        if not cache_file.exists():
            return None
        
        # Check cache age
        cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if cache_age > timedelta(hours=ttl_hours):
            logger.info(f"Cache expired for {symbol} (age: {cache_age})")
            return None
        
        try:
            data = pd.read_parquet(cache_file)
            logger.info(f"Cache hit for {symbol} (age: {cache_age})")
            return data
        except Exception as e:
            logger.warning(f"Failed to read cache for {symbol}: {e}")
            return None
    
    def _save_to_cache(
        self, 
        data: pd.DataFrame, 
        symbol: str, 
        period: str, 
        interval: str
    ) -> None:
        """Save data to cache."""
        cache_file = self._get_cache_filename(symbol, period, interval)
        
        try:
            data.to_parquet(cache_file)
            logger.info(f"Cached data for {symbol}")
        except Exception as e:
            logger.warning(f"Failed to cache data for {symbol}: {e}")
    
    def clear_cache(self, symbol: Optional[str] = None) -> int:
        """
        Clear cached data.
        
        Args:
            symbol: If provided, only clear this symbol. Otherwise clear all.
            
        Returns:
            Number of files deleted
        """
        deleted = 0
        
        if symbol:
            # Clear specific symbol
            pattern = f"{symbol.upper()}_*"
            files = self.cache_dir.glob(pattern)
        else:
            # Clear all cache
            files = self.cache_dir.glob("*")
        
        for file in files:
            if file.is_file():
                file.unlink()
                deleted += 1
        
        logger.info(f"Cleared {deleted} cache file(s)")
        return deleted


# Convenience functions
def get_stock_data(symbol: str, period: str = "1y") -> pd.DataFrame:
    """
    Quick helper to fetch stock data.
    
    Example:
        >>> data = get_stock_data('AAPL', '1y')
        >>> print(data.tail())
    """
    fetcher = StockFetcher()
    return fetcher.get_historical_data(symbol, period)


def get_current_price(symbol: str) -> float:
    """
    Quick helper to get current price.
    
    Example:
        >>> price = get_current_price('AAPL')
        >>> print(f"${price:.2f}")
    """
    fetcher = StockFetcher()
    return fetcher.get_current_price(symbol)


if __name__ == "__main__":
    # Example usage and testing
    print("StockFetcher Demo\n" + "="*50)
    
    fetcher = StockFetcher()
    
    # Test 1: Fetch historical data
    print("\n1. Fetching AAPL historical data...")
    try:
        data = fetcher.get_historical_data('AAPL', period='1mo')
        print(f"✓ Got {len(data)} days of data")
        print(f"  Latest close: ${data['Close'].iloc[-1]:.2f}")
        print(f"  Date range: {data.index[0]} to {data.index[-1]}")
    except StockDataError as e:
        print(f"✗ Error: {e}")
    
    # Test 2: Get company info
    print("\n2. Fetching company info...")
    try:
        info = fetcher.get_company_info('AAPL')
        print(f"✓ Company: {info.get('longName', 'N/A')}")
        print(f"  Sector: {info.get('sector', 'N/A')}")
        print(f"  Market Cap: ${info.get('marketCap', 0):,}")
    except StockDataError as e:
        print(f"✗ Error: {e}")
    
    # Test 3: Get current price
    print("\n3. Getting current price...")
    try:
        price = fetcher.get_current_price('AAPL')
        print(f"✓ Current price: ${price:.2f}")
    except StockDataError as e:
        print(f"✗ Error: {e}")
    
    # Test 4: Multiple stocks
    print("\n4. Fetching multiple stocks...")
    try:
        stocks = fetcher.get_multiple_stocks(['AAPL', 'MSFT', 'GOOGL'], period='1mo')
        for symbol, df in stocks.items():
            print(f"✓ {symbol}: {len(df)} records, latest close ${df['Close'].iloc[-1]:.2f}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "="*50)
    print("Demo complete!")

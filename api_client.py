"""
Alpha Vantage API Client
Provides real-time stock quotes and technical indicators.

Author: InvestWise Team
Date: December 2025
"""

import requests
import pandas as pd
from typing import Dict, Optional, List
import logging
import time
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json
from pathlib import Path

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlphaVantageError(Exception):
    """Custom exception for Alpha Vantage API errors."""
    pass


class AlphaVantageClient:
    """
    Client for Alpha Vantage API.
    
    Features:
    - Real-time stock quotes
    - Technical indicators
    - Rate limiting (25 calls/day free tier)
    - Automatic retry with exponential backoff
    - Response caching
    
    Example:
        >>> client = AlphaVantageClient()
        >>> quote = client.get_quote('AAPL')
        >>> print(f"Price: ${quote['price']:.2f}")
    """
    
    BASE_URL = "https://www.alphavantage.co/query"
    FREE_TIER_DAILY_LIMIT = 25
    FREE_TIER_CALLS_PER_MINUTE = 5
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: str = "data/cache/alphavantage"):
        """
        Initialize Alpha Vantage client.
        
        Args:
            api_key: Alpha Vantage API key (or set ALPHA_VANTAGE_API_KEY env var)
            cache_dir: Directory to cache responses
        """
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        
        if not self.api_key:
            raise AlphaVantageError(
                "Alpha Vantage API key not found. "
                "Set ALPHA_VANTAGE_API_KEY environment variable or pass api_key parameter.\n"
                "Get a free key at: https://www.alphavantage.co/support/#api-key"
            )
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Track API calls for rate limiting
        self.call_history = []
        
        logger.info("AlphaVantageClient initialized")
    
    def get_quote(self, symbol: str, use_cache: bool = True) -> Dict:
        """
        Get real-time quote for a symbol.
        
        Args:
            symbol: Stock ticker symbol
            use_cache: Whether to use cached data (5 minute TTL)
            
        Returns:
            Dictionary with quote data:
                - symbol: str
                - price: float
                - change: float
                - change_percent: float
                - volume: int
                - timestamp: str
                
        Example:
            >>> client = AlphaVantageClient()
            >>> quote = client.get_quote('AAPL')
            >>> print(f"{quote['symbol']}: ${quote['price']:.2f}")
        """
        symbol = symbol.upper().strip()
        
        # Check cache first
        if use_cache:
            cached_data = self._get_from_cache(f"quote_{symbol}", ttl_minutes=5)
            if cached_data:
                logger.info(f"Cache hit for quote: {symbol}")
                return cached_data
        
        # Make API call
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        response_data = self._make_request(params)
        
        # Parse response
        if 'Global Quote' not in response_data:
            raise AlphaVantageError(f"Invalid response for {symbol}: {response_data}")
        
        quote_data = response_data['Global Quote']
        
        if not quote_data:
            raise AlphaVantageError(f"No quote data found for {symbol}")
        
        result = {
            'symbol': quote_data.get('01. symbol', symbol),
            'price': float(quote_data.get('05. price', 0)),
            'change': float(quote_data.get('09. change', 0)),
            'change_percent': float(quote_data.get('10. change percent', '0').rstrip('%')),
            'volume': int(quote_data.get('06. volume', 0)),
            'timestamp': quote_data.get('07. latest trading day', ''),
            'open': float(quote_data.get('02. open', 0)),
            'high': float(quote_data.get('03. high', 0)),
            'low': float(quote_data.get('04. low', 0)),
            'previous_close': float(quote_data.get('08. previous close', 0))
        }
        
        # Cache the result
        if use_cache:
            self._save_to_cache(f"quote_{symbol}", result)
        
        logger.info(f"Fetched quote for {symbol}: ${result['price']:.2f}")
        return result
    
    def get_intraday_data(
        self, 
        symbol: str, 
        interval: str = '5min',
        outputsize: str = 'compact'
    ) -> pd.DataFrame:
        """
        Get intraday time series data.
        
        Args:
            symbol: Stock ticker symbol
            interval: Time interval ('1min', '5min', '15min', '30min', '60min')
            outputsize: 'compact' (latest 100 points) or 'full' (all data)
            
        Returns:
            DataFrame with intraday data
            
        Note:
            This function uses API calls. Use sparingly!
        """
        symbol = symbol.upper().strip()
        
        valid_intervals = ['1min', '5min', '15min', '30min', '60min']
        if interval not in valid_intervals:
            raise AlphaVantageError(f"Invalid interval. Must be one of: {valid_intervals}")
        
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': interval,
            'outputsize': outputsize,
            'apikey': self.api_key
        }
        
        response_data = self._make_request(params)
        
        # Find the time series key (varies by interval)
        time_series_key = f'Time Series ({interval})'
        
        if time_series_key not in response_data:
            raise AlphaVantageError(f"No intraday data found for {symbol}")
        
        data = response_data[time_series_key]
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(data, orient='index')
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        
        # Rename columns
        df.columns = ['open', 'high', 'low', 'close', 'volume']
        
        # Convert to numeric
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
        
        logger.info(f"Fetched {len(df)} intraday records for {symbol}")
        return df
    
    def get_technical_indicator(
        self,
        symbol: str,
        indicator: str,
        interval: str = 'daily',
        time_period: int = 10,
        series_type: str = 'close'
    ) -> pd.DataFrame:
        """
        Get technical indicator data.
        
        Args:
            symbol: Stock ticker symbol
            indicator: Indicator name (e.g., 'SMA', 'EMA', 'RSI', 'MACD')
            interval: Time interval
            time_period: Number of data points
            series_type: Price type ('close', 'open', 'high', 'low')
            
        Returns:
            DataFrame with indicator values
            
        Example:
            >>> client = AlphaVantageClient()
            >>> sma = client.get_technical_indicator('AAPL', 'SMA', time_period=50)
            >>> print(sma.tail())
        """
        symbol = symbol.upper().strip()
        indicator = indicator.upper()
        
        params = {
            'function': indicator,
            'symbol': symbol,
            'interval': interval,
            'time_period': time_period,
            'series_type': series_type,
            'apikey': self.api_key
        }
        
        response_data = self._make_request(params)
        
        # Find technical analysis key
        tech_key = None
        for key in response_data:
            if 'Technical Analysis' in key:
                tech_key = key
                break
        
        if not tech_key:
            raise AlphaVantageError(f"No technical indicator data found for {symbol}")
        
        data = response_data[tech_key]
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(data, orient='index')
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        
        # Convert to numeric
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
        
        logger.info(f"Fetched {indicator} for {symbol}")
        return df
    
    def _make_request(self, params: Dict) -> Dict:
        """
        Make API request with rate limiting and error handling.
        
        Args:
            params: Query parameters
            
        Returns:
            Parsed JSON response
            
        Raises:
            AlphaVantageError: If request fails
        """
        # Check rate limits
        self._check_rate_limit()
        
        # Make request with retry logic
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = requests.get(self.BASE_URL, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                # Check for API error messages
                if 'Error Message' in data:
                    raise AlphaVantageError(f"API Error: {data['Error Message']}")
                
                if 'Note' in data:
                    # Rate limit message
                    logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
                    raise AlphaVantageError("API rate limit reached. Please try again later.")
                
                # Track successful call
                self.call_history.append(datetime.now())
                
                return data
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise AlphaVantageError(f"Request failed after {max_retries} attempts: {e}")
    
    def _check_rate_limit(self) -> None:
        """
        Check if we're within rate limits.
        
        Raises:
            AlphaVantageError: If rate limit would be exceeded
        """
        now = datetime.now()
        
        # Remove old calls from history
        self.call_history = [
            call_time for call_time in self.call_history
            if now - call_time < timedelta(minutes=1)
        ]
        
        # Check per-minute limit
        if len(self.call_history) >= self.FREE_TIER_CALLS_PER_MINUTE:
            wait_time = 60 - (now - self.call_history[0]).seconds
            logger.warning(f"Rate limit reached. Waiting {wait_time}s...")
            time.sleep(wait_time)
            self.call_history = []
    
    def _get_cache_filename(self, key: str) -> Path:
        """Generate cache filename."""
        return self.cache_dir / f"{key}.json"
    
    def _get_from_cache(self, key: str, ttl_minutes: int) -> Optional[Dict]:
        """
        Get data from cache if available and fresh.
        
        Args:
            key: Cache key
            ttl_minutes: Time to live in minutes
            
        Returns:
            Cached data or None
        """
        cache_file = self._get_cache_filename(key)
        
        if not cache_file.exists():
            return None
        
        # Check cache age
        cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if cache_age > timedelta(minutes=ttl_minutes):
            return None
        
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read cache: {e}")
            return None
    
    def _save_to_cache(self, key: str, data: Dict) -> None:
        """Save data to cache."""
        cache_file = self._get_cache_filename(key)
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def get_api_usage_stats(self) -> Dict:
        """
        Get API usage statistics.
        
        Returns:
            Dictionary with usage info
        """
        now = datetime.now()
        
        calls_last_minute = len([
            t for t in self.call_history 
            if now - t < timedelta(minutes=1)
        ])
        
        calls_last_hour = len([
            t for t in self.call_history 
            if now - t < timedelta(hours=1)
        ])
        
        return {
            'calls_last_minute': calls_last_minute,
            'calls_last_hour': calls_last_hour,
            'minute_limit': self.FREE_TIER_CALLS_PER_MINUTE,
            'daily_limit': self.FREE_TIER_DAILY_LIMIT,
            'minute_remaining': self.FREE_TIER_CALLS_PER_MINUTE - calls_last_minute
        }


# Convenience function
def get_real_time_quote(symbol: str) -> Dict:
    """
    Quick helper to get real-time quote.
    
    Example:
        >>> quote = get_real_time_quote('AAPL')
        >>> print(f"${quote['price']:.2f}")
    """
    client = AlphaVantageClient()
    return client.get_quote(symbol)


if __name__ == "__main__":
    # Example usage and testing
    print("AlphaVantageClient Demo\n" + "="*50)
    
    try:
        client = AlphaVantageClient()
        
        # Test 1: Get real-time quote
        print("\n1. Getting real-time quote for AAPL...")
        try:
            quote = client.get_quote('AAPL')
            print(f"✓ {quote['symbol']}: ${quote['price']:.2f}")
            print(f"  Change: ${quote['change']:.2f} ({quote['change_percent']:.2f}%)")
            print(f"  Volume: {quote['volume']:,}")
        except AlphaVantageError as e:
            print(f"✗ Error: {e}")
        
        # Test 2: API usage stats
        print("\n2. API Usage Statistics...")
        stats = client.get_api_usage_stats()
        print(f"✓ Calls in last minute: {stats['calls_last_minute']}/{stats['minute_limit']}")
        print(f"  Remaining: {stats['minute_remaining']}")
        
        print("\n" + "="*50)
        print("Demo complete!")
        print("\nNote: Free tier limits:")
        print(f"  - {client.FREE_TIER_CALLS_PER_MINUTE} calls per minute")
        print(f"  - {client.FREE_TIER_DAILY_LIMIT} calls per day")
        
    except AlphaVantageError as e:
        print(f"\n✗ Setup Error: {e}")
        print("\nTo use Alpha Vantage:")
        print("1. Get a free API key at: https://www.alphavantage.co/support/#api-key")
        print("2. Add to your .env file: ALPHA_VANTAGE_API_KEY=your_key_here")

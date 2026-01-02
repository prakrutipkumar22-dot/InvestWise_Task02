"""
Configuration settings for InvestWise platform.

Author: InvestWise Team
Date: December 2025
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Base configuration."""
    
    # Application
    APP_NAME = "InvestWise"
    VERSION = "1.0.0"
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # API Keys
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    
    # Data directories
    DATA_DIR = BASE_DIR / 'data'
    DATA_RAW_DIR = DATA_DIR / 'raw'
    DATA_PROCESSED_DIR = DATA_DIR / 'processed'
    CACHE_DIR = DATA_DIR / 'cache'
    
    # Cache settings
    CACHE_ENABLED = True
    CACHE_TTL_HOURS = 24  # Default cache time-to-live
    STOCK_QUOTE_CACHE_MINUTES = 5  # Real-time quotes
    COMPANY_INFO_CACHE_DAYS = 7  # Company info
    
    # API Rate Limits
    ALPHA_VANTAGE_CALLS_PER_MINUTE = 5
    ALPHA_VANTAGE_DAILY_LIMIT = 25
    
    # Stock Data Settings
    DEFAULT_PERIOD = '1y'
    DEFAULT_INTERVAL = '1d'
    VALID_PERIODS = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
    VALID_INTERVALS = ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo']
    
    # Portfolio Simulation Settings
    DEFAULT_ANNUAL_RETURN = 0.10  # 10% average
    DEFAULT_VOLATILITY = 0.15  # 15% standard deviation
    MIN_INVESTMENT = 1
    MAX_INVESTMENT = 1000000
    MIN_YEARS = 1
    MAX_YEARS = 50
    
    # LLM Settings
    LLM_MODEL = "claude-sonnet-4-20250514"
    LLM_MAX_TOKENS = 1000
    LLM_TEMPERATURE = 0.7
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Flask Settings
    FLASK_HOST = '0.0.0.0'
    FLASK_PORT = 5000
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = BASE_DIR / 'logs' / 'investwise.log'
    
    # CORS (for frontend)
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:3000').split(',')
    
    @classmethod
    def init_app(cls):
        """Initialize application directories."""
        # Create necessary directories
        cls.DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
        cls.DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate(cls):
        """Validate configuration."""
        errors = []
        
        # Check required API keys
        if not cls.ALPHA_VANTAGE_API_KEY:
            errors.append(
                "ALPHA_VANTAGE_API_KEY not set. "
                "Get one at: https://www.alphavantage.co/support/#api-key"
            )
        
        if not cls.ANTHROPIC_API_KEY:
            errors.append(
                "ANTHROPIC_API_KEY not set. "
                "Set in .env file or environment variables."
            )
        
        if errors:
            error_msg = "Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)
    
    @classmethod
    def get_info(cls) -> dict:
        """Get configuration info (safe for logging)."""
        return {
            'app_name': cls.APP_NAME,
            'version': cls.VERSION,
            'debug': cls.DEBUG,
            'cache_enabled': cls.CACHE_ENABLED,
            'data_dir': str(cls.DATA_DIR),
            'alpha_vantage_configured': bool(cls.ALPHA_VANTAGE_API_KEY),
            'anthropic_configured': bool(cls.ANTHROPIC_API_KEY),
        }


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    CACHE_TTL_HOURS = 1  # Shorter cache in development


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    CACHE_TTL_HOURS = 24
    
    @classmethod
    def validate(cls):
        """Additional validation for production."""
        super().validate()
        
        if cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            raise ValueError("SECRET_KEY must be changed for production!")


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    CACHE_ENABLED = False  # Disable caching in tests
    CACHE_DIR = Config.BASE_DIR / 'data' / 'cache' / 'test'


# Configuration selector
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env: str = None) -> Config:
    """
    Get configuration for specified environment.
    
    Args:
        env: Environment name ('development', 'production', 'testing')
             If None, uses FLASK_ENV environment variable
    
    Returns:
        Configuration class
    """
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    
    return config.get(env, config['default'])


# Export commonly used config
current_config = get_config()


if __name__ == "__main__":
    # Test configuration
    print("InvestWise Configuration\n" + "="*50)
    
    cfg = get_config()
    
    print(f"\nEnvironment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"Debug Mode: {cfg.DEBUG}")
    print(f"\nAPI Keys:")
    print(f"  Alpha Vantage: {'✓ Set' if cfg.ALPHA_VANTAGE_API_KEY else '✗ Not Set'}")
    print(f"  Anthropic: {'✓ Set' if cfg.ANTHROPIC_API_KEY else '✗ Not Set'}")
    print(f"\nDirectories:")
    print(f"  Base: {cfg.BASE_DIR}")
    print(f"  Data: {cfg.DATA_DIR}")
    print(f"  Cache: {cfg.CACHE_DIR}")
    print(f"\nCache Settings:")
    print(f"  Enabled: {cfg.CACHE_ENABLED}")
    print(f"  TTL: {cfg.CACHE_TTL_HOURS} hours")
    
    print("\n" + "="*50)
    
    # Validate configuration
    try:
        cfg.validate()
        print("✓ Configuration valid!")
    except ValueError as e:
        print(f"✗ Configuration errors:\n{e}")

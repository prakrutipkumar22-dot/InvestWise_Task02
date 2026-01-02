# Week 3-4 Setup Instructions

## 🎯 Goal
By the end of this week, you'll have a fully functional stock data pipeline that:
- Fetches real stock market data
- Caches data to avoid API limits
- Includes comprehensive error handling
- Has a full test suite

---

## 📁 Step 1: Create New Files

You need to create these files in your project:

### 1. src/data/stock_fetcher.py
Copy the complete code from the `stock_fetcher.py` artifact above.

### 2. src/data/api_client.py
Copy the complete code from the `api_client.py` artifact above.

### 3. src/config.py
Copy the complete code from the `config.py` artifact above.

### 4. tests/test_data/test_stock_fetcher.py
First create the directory:
```bash
mkdir -p tests/test_data
touch tests/test_data/__init__.py
```
Then copy the test code.

### 5. test_setup.py (root directory)
Copy the setup test script to your root directory.

---

## 🔑 Step 2: Get API Keys

### Alpha Vantage API Key (Free)

1. Go to: https://www.alphavantage.co/support/#api-key
2. Fill out the form (takes 30 seconds)
3. You'll get a key instantly (looks like: `ABC123XYZ456`)
4. Free tier limits:
   - 25 calls per day
   - 5 calls per minute

### Anthropic Claude API Key (Syracuse Access)

You mentioned you have Syracuse University access to Claude! 

1. Go to: https://console.anthropic.com/
2. Sign in with your Syracuse credentials
3. Navigate to API Keys section
4. Create a new API key
5. Copy it immediately (you can't view it again!)

---

## 🔧 Step 3: Configure Environment Variables

### Create .env file

In your project root, create a `.env` file:

```bash
# .env - DO NOT COMMIT THIS FILE TO GIT

# Alpha Vantage API Key
ALPHA_VANTAGE_API_KEY=your_actual_key_here

# Anthropic Claude API Key  
ANTHROPIC_API_KEY=your_actual_key_here

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-for-dev

# Optional: Redis (if using)
REDIS_URL=redis://localhost:6379/0
```

### Verify .env is Gitignored

Double-check that `.env` is in your `.gitignore` file (it should be already):

```bash
# Check if .env is gitignored
git check-ignore .env

# Should output: .env
```

**NEVER commit .env to Git!**

---

## 📦 Step 4: Install Additional Dependencies

Some packages might be missing. Install them:

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate  # Windows

# Install specific packages we need
pip install yfinance
pip install python-dotenv
pip install requests
pip install pyarrow  # For parquet files
pip install pytest
pip install anthropic

# Or just update all
pip install -r requirements.txt
```

---

## ✅ Step 5: Test Your Setup

### Run the Quick Test

```bash
python test_setup.py
```

You should see output like:
```
===========================================================
InvestWise Setup Test - Week 3-4
===========================================================

[1/6] Testing imports...
✓ All modules imported successfully

[2/6] Checking configuration...
✓ Configuration loaded
  - App: InvestWise v1.0.0
  - Debug: True
  - Data dir: /path/to/investwise/data

[3/6] Checking API keys...
  Alpha Vantage: ✓ Set
  Anthropic: ✓ Set

[4/6] Testing StockFetcher...
✓ StockFetcher initialized
  Fetching AAPL data (this may take a few seconds)...
✓ Successfully fetched 5 days of data
  Latest close: $234.56
  Date range: 2025-11-25 to 2025-11-29

[5/6] Testing company info...
✓ Company: Apple Inc.
  Sector: Technology
  Industry: Consumer Electronics

[6/6] Testing Alpha Vantage...
✓ AlphaVantageClient initialized
  (Skipping live API call to save quota)
  API usage: 0/5 calls/min

===========================================================
Setup Test Complete!
===========================================================
```

---

## 🧪 Step 6: Run the Full Test Suite

```bash
# Run all tests
pytest tests/test_data/test_stock_fetcher.py -v

# Run with coverage
pytest tests/test_data/test_stock_fetcher.py -v --cov=src/data

# Run only fast tests (skip slow ones)
pytest tests/test_data/test_stock_fetcher.py -v -m "not slow"
```

Expected output:
```
tests/test_data/test_stock_fetcher.py::TestStockFetcherBasics::test_initialization PASSED
tests/test_data/test_stock_fetcher.py::TestStockFetcherBasics::test_valid_periods PASSED
tests/test_data/test_stock_fetcher.py::TestHistoricalData::test_get_historical_data_valid_symbol PASSED
...

========== 25 passed in 45.23s ===========
```

---

## 🎮 Step 7: Try the Demo

Each module has a built-in demo. Try them:

### Stock Fetcher Demo

```bash
python src/data/stock_fetcher.py
```

Output:
```
StockFetcher Demo
==================================================

1. Fetching AAPL historical data...
✓ Got 21 days of data
  Latest close: $234.56
  Date range: 2025-11-01 to 2025-11-29

2. Fetching company info...
✓ Company: Apple Inc.
  Sector: Technology
  Market Cap: $3,654,000,000,000

3. Getting current price...
✓ Current price: $234.56

4. Fetching multiple stocks...
✓ AAPL: 21 records, latest close $234.56
✓ MSFT: 21 records, latest close $456.78
✓ GOOGL: 21 records, latest close $123.45

==================================================
Demo complete!
```

### Alpha Vantage Demo

```bash
python src/data/api_client.py
```

---

## 🐛 Troubleshooting

### Problem: ImportError: No module named 'yfinance'

**Solution:**
```bash
pip install yfinance
```

### Problem: "ALPHA_VANTAGE_API_KEY not set"

**Solution:**
1. Make sure you created the `.env` file
2. Make sure the key is on a new line
3. No quotes needed: `ALPHA_VANTAGE_API_KEY=ABC123`
4. Restart your terminal/IDE after creating .env

### Problem: "No data returned for AAPL"

**Solution:**
- Check your internet connection
- Try a different symbol (SPY, MSFT, etc.)
- yfinance might be temporarily down
- Wait a few minutes and try again

### Problem: Tests fail with "Invalid symbol"

**Solution:**
- This is normal if yfinance is having issues
- Try running tests again later
- Focus on passing the basic import tests first

### Problem: "Rate limit reached"

**Solution:**
- Alpha Vantage free tier: 25 calls/day
- Wait until tomorrow
- Or use only yfinance for now (it's unlimited)

---

## 📊 Step 8: Check Your Data

After running tests, check that cache files were created:

```bash
# List cache directory
ls -lh data/cache/

# Should see files like:
# AAPL_1mo_1d.parquet
# AAPL_info.json
# etc.
```

---

## 💾 Step 9: Commit Your Work

```bash
# Check what's changed
git status

# Add new files (but NOT .env!)
git add src/data/stock_fetcher.py
git add src/data/api_client.py
git add src/config.py
git add tests/test_data/
git add test_setup.py

# Commit
git commit -m "Week 3-4: Add stock data pipeline with yfinance and Alpha Vantage

- Implement StockFetcher with caching
- Add Alpha Vantage API client
- Create configuration system
- Add comprehensive test suite
- Verify data fetching works with real APIs"

# Push to GitHub
git push origin main
```

---

## ✅ Week 3-4 Checklist

- [ ] Created all Python modules
- [ ] Got Alpha Vantage API key
- [ ] Got Anthropic API key (Syracuse access)
- [ ] Created .env file with keys
- [ ] Verified .env is gitignored
- [ ] Ran `test_setup.py` successfully
- [ ] Ran pytest test suite
- [ ] Tried the demo scripts
- [ ] Checked cache directory has files
- [ ] Committed code to GitHub (without .env!)

---

## 🎉 Success Criteria

You're done with Week 3-4 when:

1. ✅ `test_setup.py` runs without errors
2. ✅ At least 20/25 pytest tests pass
3. ✅ You can fetch real stock data for AAPL
4. ✅ Cache directory contains data files
5. ✅ Both API keys are configured
6. ✅ Code is committed to GitHub

---

## 🚀 What's Next?

**Week 5-6: Portfolio Simulator**
- Build the investment calculator
- Add Monte Carlo simulation
- Create comparison tools
- Visualize results

**Week 7-8: Stock Screener**
- Filter stocks by criteria
- Beginner-friendly metrics
- Educational tooltips

---

## 📞 Need Help?

If you get stuck:

1. **Check the error message carefully** - it usually tells you exactly what's wrong
2. **Try the individual demos** - they help isolate problems
3. **Check API quotas** - you might have hit rate limits
4. **Google the error** - someone else has probably had the same issue
5. **Ask me** - I'm here to help!

---

## 📚 Additional Resources

- **yfinance docs**: https://pypi.org/project/yfinance/
- **Alpha Vantage docs**: https://www.alphavantage.co/documentation/
- **pytest docs**: https://docs.pytest.org/
- **Python dotenv**: https://pypi.org/project/python-dotenv/

---

**Good luck! You're building something real! 🚀**

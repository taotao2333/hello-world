## Cursor Cloud specific instructions

This is the **股智先知 (Stock Prophet)** project — a Chinese A-share stock analysis and prediction system built with Python/FastAPI.

### Architecture

- **Backend**: FastAPI (Python 3.12), SQLAlchemy + SQLite
- **Data sources**: `akshare` (Chinese stock market data), RSS feeds (Xinhua, People's Daily)
- **Analysis**: keyword-based news sentiment, sector correlation, technical indicators (RSI, MACD, MA)
- **Frontend**: Jinja2 templates with dark-themed responsive CSS

### Running the app

```bash
export PATH="/home/ubuntu/.local/bin:$PATH"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Running tests

```bash
python3 -m pytest tests/ -v
```

### Key caveats

- `akshare` stock data fetching can be slow (10-30s) due to network calls to Chinese financial APIs. The "生成预测" endpoint may take up to 60s.
- The app uses SQLite at `data/stock_prophet.db`. The DB is auto-created on first startup via `init_db()`.
- RSS feeds from Chinese news sources (Xinhua, People's Daily) may return stale/cached data depending on network access from the VM.
- The `PATH` must include `/home/ubuntu/.local/bin` for `uvicorn` and `pytest` to be found.
- The review/backtest feature requires predictions from a previous day to have meaningful results.

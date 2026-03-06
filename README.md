# 股智先知 — A股智能分析预测系统

每日采集中国新闻、政策和国际资讯，结合A股技术面分析，生成个股涨跌预测，并在次日复盘验证准确率。

## 功能

- **新闻采集**：从新华网、人民网等RSS源及财经平台采集新闻，分析情感倾向和行业关联
- **智能预测**：综合新闻面（政策/国际/行业情感）和技术面（RSI/MACD/均线/量比），生成个股预测
- **每日复盘**：对比昨日预测与实际走势，分析准确和不准确的原因

## 快速开始

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

浏览器打开 http://localhost:8000

## 技术栈

- Python 3.12 + FastAPI + SQLAlchemy + SQLite
- akshare（A股数据） + feedparser（RSS新闻）
- jieba（中文分词） + 自定义情感/关键词分析
- Jinja2 模板 + 暗色主题 CSS

## 运行测试

```bash
python3 -m pytest tests/ -v
```

⚠️ 免责声明：本系统仅供学习研究，不构成投资建议。股市有风险，投资需谨慎。

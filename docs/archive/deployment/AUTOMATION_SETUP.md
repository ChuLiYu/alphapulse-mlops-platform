# Automated Data Collection Setup

## 📋 Overview

This setup enables automatic data collection for AlphaPulse MLOps platform.

## 🔧 Scripts Created

### 1. `scripts/update_price_data.py`

- Collects latest BTC-USD price data from Yahoo Finance
- Updates `prices` table with new records
- Runs in ~5 seconds

### 2. `scripts/auto_collect_data.sh`

- Main automation workflow
- Steps:
  1. Update price data
  2. Collect news from RSS feeds
  3. Analyze sentiment
  4. Update model features
- Creates timestamped logs in `/tmp/alphapulse_logs/`

### 3. `scripts/setup_automation.sh`

- One-time setup script
- Configures automated scheduling:
  - **macOS**: Uses launchd
  - **Linux**: Uses cron
- Default schedule: 02:00, 08:00, 14:00, 20:00 daily

## 🚀 Quick Start

### Step 1: Test Scripts Manually

```bash
# Test price data collection
docker cp scripts/update_price_data.py airflow-webserver:/opt/airflow/src/
docker exec airflow-webserver python /opt/airflow/src/update_price_data.py

# Test full workflow
chmod +x scripts/auto_collect_data.sh
./scripts/auto_collect_data.sh
```

### Step 2: Enable Automation

```bash
chmod +x scripts/setup_automation.sh
./scripts/setup_automation.sh
```

This will:

- Create scheduled task (launchd on macOS, cron on Linux)
- Run data collection 4 times daily
- Log all activities to `/tmp/alphapulse_logs/`

## 📅 Collection Schedule

**Default Times (Local):**

- 02:00 - Early morning update
- 08:00 - Morning market update
- 14:00 - Afternoon update
- 20:00 - Evening update

**Customize Schedule:**

For macOS (launchd):

```bash
# Edit the plist file
nano ~/Library/LaunchAgents/com.alphapulse.datacollection.plist
# Then reload
launchctl unload ~/Library/LaunchAgents/com.alphapulse.datacollection.plist
launchctl load ~/Library/LaunchAgents/com.alphapulse.datacollection.plist
```

For Linux (cron):

```bash
crontab -e
# Edit times: minute hour * * * command
# Example: 0 */6 * * * = every 6 hours
```

## 📊 Monitoring

### Check Status

```bash
# View pipeline status
./scripts/check_pipeline_status.sh

# View latest logs
tail -f /tmp/alphapulse_logs/auto_collect_*.log

# Check data freshness
docker exec postgres psql -U postgres -d alphapulse -c "
SELECT 'prices', MAX(timestamp) FROM prices
UNION ALL SELECT 'news', MAX(published_at) FROM market_news
UNION ALL SELECT 'sentiment', MAX(analyzed_at) FROM sentiment_scores
"
```

### Verify Automation (macOS)

```bash
# Check if job is loaded
launchctl list | grep alphapulse

# View output logs
tail -f /tmp/alphapulse_auto_collect.log
tail -f /tmp/alphapulse_auto_collect_error.log
```

### Verify Automation (Linux)

```bash
# Check crontab
crontab -l

# View cron logs
grep CRON /var/log/syslog | grep alphapulse
```

## 🛠️ Manual Operations

### Run Collection Manually

```bash
# Full workflow
./scripts/auto_collect_data.sh

# Individual components
docker exec airflow-webserver python /opt/airflow/src/update_price_data.py
docker exec airflow-webserver python /opt/airflow/src/collect_news_and_sentiment.py
docker exec airflow-webserver python /opt/airflow/src/integrate_sentiment_features.py
```

### Disable Automation

**macOS:**

```bash
launchctl unload ~/Library/LaunchAgents/com.alphapulse.datacollection.plist
rm ~/Library/LaunchAgents/com.alphapulse.datacollection.plist
```

**Linux:**

```bash
crontab -e
# Delete the alphapulse line
```

## 🔍 Troubleshooting

### Issue: Scripts not running

**Check logs:**

```bash
ls -lh /tmp/alphapulse_logs/
cat /tmp/alphapulse_logs/auto_collect_*.log | tail -50
```

**Verify permissions:**

```bash
chmod +x scripts/auto_collect_data.sh
chmod +x scripts/update_price_data.py
chmod +x scripts/collect_news_and_sentiment.py
```

### Issue: Database connection failed

**Check containers:**

```bash
docker ps | grep alphapulse
docker logs postgres | tail -20
```

**Verify connection:**

```bash
docker exec postgres psql -U postgres -d alphapulse -c "SELECT 1"
```

### Issue: No new data

**Check data sources:**

```bash
# Test Yahoo Finance connection
docker exec airflow-webserver python -c "import yfinance as yf; print(yf.Ticker('BTC-USD').history(period='1d'))"

# Test RSS feeds
curl -I https://www.coindesk.com/arc/outboundfeeds/rss/
curl -I https://cointelegraph.com/rss
```

## 📈 Expected Results

After automation is running:

- **Price Data**: Updated 4x daily with latest BTC prices
- **News Articles**: ~30-50 new articles per day
- **Sentiment Analysis**: 90%+ coverage of news articles
- **Model Features**: Refreshed with latest data 4x daily

## 🎯 Next Steps

1. **Monitor first 24 hours**: Check logs after each scheduled run
2. **Adjust schedule**: Modify times if needed for your timezone
3. **Set up alerts**: Consider adding email/Slack notifications
4. **Model retraining**: Schedule weekly model retraining:
   ```bash
   # Add to cron/launchd
   0 3 * * 0 cd /path/to/alphapulse && ./scripts/complete_data_pipeline.sh
   ```

## 📞 Quick Commands Reference

```bash
# Status check
./scripts/check_pipeline_status.sh

# Manual collection
./scripts/auto_collect_data.sh

# View logs
tail -f /tmp/alphapulse_logs/auto_collect_$(date +%Y%m%d)*.log

# Check automation status
launchctl list | grep alphapulse  # macOS
crontab -l                         # Linux

# Database status
docker exec postgres psql -U postgres -d alphapulse -c "
SELECT table_name, COUNT(*) FROM (
    SELECT 'prices' as table_name FROM prices
    UNION ALL SELECT 'news' FROM market_news
    UNION ALL SELECT 'sentiment' FROM sentiment_scores
) t GROUP BY table_name
"
```

# flask-varcalculator

Welcome to FxRiskApp, the Forex VaR Calculator!

## VaR Calculation

Individual VaR of Currency Pair = sqrt(variance of currency pair price changes) * z-score(confidence %) * exposure amt.

Portfolio VaR = sqrt(variance of portfolio price changes) * z-score(confidence %) * total exposure amt. (all pairs)

Beta of Currency Pair = (Co-variance of currency pair w/ portfolio)/(variance of currency pair)

Component VaR of Currency Pair = Portfolio VaR * beta(currency pair w/ portfolio) * (fractional weight of currency pair in portfolio b/w 0-1)

Note: all price changes are n-day price changes (like 7-day price changes, etc.)

## Dataset

Rates API: `api.ratesapi.io`

Currency Rates Data file: `data.json`

Currency Rates Data Fetch Script: `scripts/daily_rates.js`

Data script run command: `node scripts/daily_rates.js`
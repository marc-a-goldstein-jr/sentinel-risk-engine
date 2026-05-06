# sentinel-risk-engine
Automated quantitative risk &amp; liquidity engine utilizing REST APIs to monitor real-time market sensitivity, 95% VaR, and portfolio drift.
[Screenshot 1.pdf](https://github.com/user-attachments/files/27422199/Screenshot.1.pdf)
[Screenshot 2.pdf](https://github.com/user-attachments/files/27422198/Screenshot.2.pdf)
[Screenshot 3.pdf](https://github.com/user-attachments/files/27422197/Screenshot.3.pdf)
[Screenshot 4.pdf](https://github.com/user-attachments/files/27422196/Screenshot.4.pdf)
# Sentinel V5.57 | Dynamic Risk & Execution Engine

Sentinel is a specialized FinTech dashboard designed to bridge the gap between live market data and disciplined trade execution. By integrating with the Kraken REST API, the system provides a "State-Aware" environment that monitors portfolio drift, calculates institutional-grade risk metrics, and enforces execution rules to prevent emotional trading.

## 🚀 Key Features
* [cite_start]**Live Portfolio Synchronization**: Real-time tracking of asset balances and current market valuations via Kraken API[cite: 45].
* **Institutional Risk Metrics**: 
    * [cite_start]**95% Value at Risk (VaR)**: Statistical calculation of potential daily downside[cite: 49].
    * [cite_start]**High Water Mark (HWM) Tracking**: Persistent recording of lifetime portfolio peaks[cite: 46, 50].
    * [cite_start]**Max Drawdown**: Calculation of the largest peak-to-trough decline to monitor risk exposure[cite: 51].
* [cite_start]**Dynamic Execution Layer**: Logic-gate system that evaluates technical positioning (Support/Resistance) against strategic needs (Underweight/Overweight) to issue "Strike" or "Block" directives[cite: 66, 69, 71].
* [cite_start]**Audit Trail**: Persistent logging of rebalancing needs and trade session activity to local CSV and TXT files[cite: 15, 79].

## 🛠️ Tech Stack
* **Language**: Python 3.x
* **Interface**: Streamlit (Responsive Web UI)
* **Data Handling**: Pandas, NumPy
* **API Integration**: Krakenex (REST)
* **Security**: Python-Dotenv (Environment Variable isolation)

## 📊 Logic Verification
The system includes a "Trophy of Pain" (Max Drawdown) persistence layer. By storing the High Water Mark and Max Drawdown in external files, the engine maintains historical memory across different sessions, ensuring that risk reporting remains accurate even after a market recovery or app restart.

## 🛡️ Security Note
This repository contains the logic only. API keys are managed via local `.env` files and are excluded from version control via `.gitignore` to ensure security best practices.

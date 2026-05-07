Sentinel V5.94 | Quantitative Trading & DePIN Intelligence Environment
Sentinel is a high-performance quantitative dashboard designed to bridge the gap between live market forensics and disciplined execution. By integrating the Kraken REST API with a Monte Carlo forecasting engine, Sentinel provides an "Executive Command" suite that manages risk, monitors portfolio drift, and enforces execution rules for high-volatility assets (RENDER, TAO, FET).

📱 Executive Mobile Command
Unlike static dashboards, Sentinel is engineered for the mobile executive. Utilizing ngrok secure tunneling, the entire suite is broadcast from a local environment to a secure, mobile-responsive web interface, allowing for real-time "Tactical Directives" and portfolio monitoring from any device, anywhere.

🚀 Key Technical Pillars
Real-Time Data Orchestration: Integrated a high-concurrency pipeline via Kraken API to automate multi-asset valuation and eliminate latency-driven pricing errors.

Probabilistic Wealth Forecasting: Engineered a Monte Carlo Simulation engine that runs 1,000+ iterations to project 90-day portfolio trajectories and "Milestone Attainment" probabilities.

Institutional Risk Intelligence:

95% Value at Risk (VaR): Statistical quantification of daily capital at risk.

Sharpe & Calmar Ratios: Real-time calculation of risk-adjusted returns.

Persistent State Management: Engineered a local database layer to maintain a High Water Mark (HWM) and audit trail across asynchronous sessions.

Asset Forensics (Tape Intelligence): Synthesizes live Order Book pressure (Buy/Sell dominance) with qualitative "Soundness Scores" to validate trade convictions.

🛠️ Tech Stack
Engine: Python 3.11+

Interface: Streamlit (Responsive Web UI)

Analytics: NumPy, Pandas, Plotly (Interactive Financial Visualizations)

Networking: ngrok (Secure Tunneling), Krakenex (REST)

Security: Python-Dotenv (Environment Variable Isolation)

📊 Strategic Logic
The system enforces a Systematic Rebalancing Engine. It monitors "Portfolio Drift" against a target 65/17.5/17.5 allocation, issuing "Strike" or "Block" directives only when assets cross dynamic technical support/resistance zones. This prevents "over-trading" and ensures capital is only deployed at high-probability entry points.

🛡️ Security & Deployment
This repository contains the core logic and architectural framework. Sensitive credentials (API Keys, Email Tokens) are managed via localized .env files and are excluded from version control to ensure security best practices.

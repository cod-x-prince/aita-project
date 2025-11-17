# AITA-01: Intraday Agentic AI

This project is an autonomous, multi-agent AI designed to identify and signal intraday trading opportunities. The system was built from the ground up, starting with research and backtesting and culminating in a live, "Advisor Mode" agent.

## Current Strategy

The current live agent (`live_agent_orb.py`) implements a profitable, backtested **Opening Range Breakout (ORB)** strategy.

- **Asset:** HDFCBANK (NSE)
- **Timeframe:** 1-Minute
- **Logic:**
  1.  Defines the high and low of the first 30 minutes of trading (9:15 - 9:45 AM).
  2.  Generates one signal per day on the first breakout of this range.
  3.  The agent runs autonomously, but in **Advisor Mode** (it generates signals on a dashboard but does not execute trades).

## Core Components

- `live_agent_orb.py`: The main, live-ready agent that runs 24/7, monitors the market, and generates signals.
- `dashboard.py`: The Streamlit-based visual dashboard for monitoring the agent in real-time.
- `strategy_logic.py`: A library containing the functions for our trading strategies (ORB, VWAP, Bollinger Bands) and performance calculation.
- `archive/`: Contains all the research, backtesting, and optimization scripts used to scientifically validate the profitable strategy.
- `utils/`: Contains helper scripts for tasks like finding instrument keys and generating access tokens.

## Setup and Installation

1.  **Environment:** This project uses Conda. Create the environment using:
    ```bash
    conda create --name aita_env python=3.11
    conda activate aita_env
    ```
2.  **Dependencies:** Install all necessary packages:
    ```bash
    pip install upstox-python-sdk pandas pandas-ta streamlit python-dotenv upstox-instrument-query
    ```
3.  **API Keys:** Create a `.env` file in the root directory and add your Upstox credentials:
    ```
    UPSTOX_API_KEY="YOUR_API_KEY"
    UPSTOX_ACCESS_TOKEN="YOUR_ACCESS_TOKEN"
    ```
4.  **Instrument Database:** Initialize the local instrument database for the utility scripts:
    ```bash
    upstox-query init
    ```

## How to Run (Live Advisor Mode)

The system requires two terminals running simultaneously.

1.  **Terminal 1 (Start the Agent):**
    ```bash
    python live_agent_orb.py
    ```
2.  **Terminal 2 (Start the Dashboard):**
    ```bash
    streamlit run dashboard.py
    ```

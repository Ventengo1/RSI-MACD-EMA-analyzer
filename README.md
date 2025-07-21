# RSI-MACD-EMA-analyzer

This program analyzes the RSI, MACD, and EMA for entered stocks and gives a recommended action which is weither buy, sell, or hold.

# Installation Instructions:

This project uses uv for dependency management. uv provides a fast and robust way to manage Python environments and lock dependencies.

1. Install uv
If you don't have uv installed, use one of the following commands based on your operating system:

Linux/macOS:

Bash

curl -LsSf https://astral.sh/uv/install.sh | sh
Windows (PowerShell):

PowerShell

irm https://astral.sh/uv/install.ps1 | iex
2. Set up the Project
Create a new directory for your project and navigate into it:

Bash

mkdir stock-analyzer-project
cd stock-analyzer-project
3. Create the stock_analyzer.py file
Create a file named stock_analyzer.py in your project directory and paste the entire code provided in the Code section below into it.

4. Initialize uv Script Metadata and Add Dependencies
Run the following commands to add the necessary uv script metadata to stock_analyzer.py and declare the project's dependencies:

Bash

uv init --script stock_analyzer.py --python 3.9 # You can specify your preferred Python version here, e.g., 3.10, 3.11, 3.12
uv add --script stock_analyzer.py yfinance pandas numpy scikit-learn scipy
These commands will automatically add a /// script block at the top of your stock_analyzer.py file, listing the dependencies.

5. Lock Dependencies
To ensure reproducible environments, lock the exact versions of all dependencies. This will create a stock_analyzer.py.lock file in your project directory.

Bash

uv lock --script stock_analyzer.py
Usage
Once you've completed the installation steps, you can run the script using uv:

Bash

uv run stock_analyzer.py
The script will prompt you to enter one or more stock symbols (separated by commas). For example:

Symbols: AAPL,MSFT,GOOG
The output for each symbol will display the current price, key indicator values, and a calculated decision (Buy, Sell, Hold, etc.).

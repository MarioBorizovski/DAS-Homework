from flask import Flask, jsonify, request
from typing import Dict, List, Optional
import pandas as pd
import os
from datetime import datetime
import subprocess
import logging
from os import environ


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import local modules with error handling
try:
    from data_processor import DataProcessor
    from trading_signals import SignalGenerator
    from scrape_functions import get_codes, clean_nulls
    from config import Config
except ImportError as e:
    logger.error(f"Failed to import required modules: {str(e)}")
    raise

app = Flask(__name__)


class TradingAPI:
    @staticmethod
    def get_available_symbols() -> List[str]:
        """Get list of available trading symbols."""
        try:
            # First check if the directory exists
            if not os.path.exists(Config.FILES_DIRECTORY):
                os.makedirs(Config.FILES_DIRECTORY)
                logger.warning(f"Created directory: {Config.FILES_DIRECTORY}")

            # Get files from directory first
            files = [f.replace('.csv', '') for f in os.listdir(Config.FILES_DIRECTORY)
                     if f.endswith('.csv')]

            if not files:  # If no files, try getting from web
                files = get_codes()

            return files
        except Exception as e:
            logger.error(f"Error in get_available_symbols: {str(e)}")
            raise APIError(f"Error fetching symbols: {str(e)}")

    @staticmethod
    def get_symbol_data(symbol: str, window: str = Config.DEFAULT_WINDOW) -> Dict:
        """Get processed trading data for a specific symbol."""
        try:
            file_path = os.path.join(Config.FILES_DIRECTORY, f"{symbol}.csv")

            if not os.path.isfile(file_path):
                logger.error(f"File not found: {file_path}")
                raise APIError(f"Data not found for symbol: {symbol}")

            # Read and process data
            df = pd.read_csv(file_path)
            df.columns = df.columns.str.strip()

            if len(df) < 2:
                raise APIError("Insufficient data for calculations")

            window_size = Config.WINDOW_MAP.get(window, Config.DEFAULT_WINDOW_SIZE)

            # Process data and generate signals
            processor = DataProcessor(df, window_size)
            df = processor.process()

            signal_generator = SignalGenerator(df)
            df['Signal'] = signal_generator.generate_signals()

            # Format response
            df = df.fillna(0)
            latest_date = df['Datum'].max()
            df = df.sort_values(by='Datum', ascending=False)

            return {
                'symbol': symbol,
                'latest_date': str(latest_date),
                'data': df.to_dict(orient='records')
            }
        except Exception as e:
            logger.error(f"Error in get_symbol_data: {str(e)}")
            raise APIError(f"Error processing data: {str(e)}")

    @staticmethod
    def trigger_data_scrape() -> Dict:
        """Trigger the data scraping process."""
        try:
            # Check if scrape.py exists
            if not os.path.exists("scrape.py"):
                raise APIError("Scraping script not found")

            subprocess.run(["python", "scrape.py"], check=True)
            return {"status": "success", "message": "Data scrape initiated successfully"}
        except subprocess.CalledProcessError as e:
            logger.error(f"Scraping process failed: {str(e)}")
            raise APIError(f"Scraping process failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during scraping: {str(e)}")
            raise APIError(f"Unexpected error during scraping: {str(e)}")


class APIError(Exception):
    """Custom exception for API errors."""
    pass


@app.errorhandler(APIError)
def handle_api_error(error):
    """Handle custom API errors."""
    logger.error(f"API Error: {str(error)}")
    response = jsonify({
        'error': str(error),
        'timestamp': datetime.utcnow().isoformat()
    })
    response.status_code = 400
    return response


@app.errorhandler(Exception)
def handle_generic_error(error):
    """Handle all other exceptions."""
    logger.error(f"Unhandled Exception: {str(error)}")
    response = jsonify({
        'error': 'Internal server error',
        'detail': str(error),
        'timestamp': datetime.utcnow().isoformat()
    })
    response.status_code = 500
    return response


# API Routes
@app.route('/api/v1/symbols', methods=['GET'])
def get_symbols():
    """Get all available trading symbols."""
    try:
        trading_api = TradingAPI()
        symbols = trading_api.get_available_symbols()
        return jsonify({
            'symbols': symbols,
            'count': len(symbols)
        })
    except Exception as e:
        logger.error(f"Error in get_symbols endpoint: {str(e)}")
        raise


@app.route('/api/v1/data/<symbol>', methods=['GET'])
def get_data(symbol):
    """Get trading data for a specific symbol."""
    try:
        window = request.args.get('window', Config.DEFAULT_WINDOW)
        trading_api = TradingAPI()
        data = trading_api.get_symbol_data(symbol, window)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error in get_data endpoint: {str(e)}")
        raise


@app.route('/api/v1/scrape', methods=['POST'])
def trigger_scrape():
    """Trigger data scraping process."""
    try:
        trading_api = TradingAPI()
        result = trading_api.trigger_data_scrape()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in trigger_scrape endpoint: {str(e)}")
        raise


# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })


if __name__ == '__main__':
    try:
        # Ensure the data directory exists
        if not os.path.exists(Config.FILES_DIRECTORY):
            os.makedirs(Config.FILES_DIRECTORY)
            logger.info(f"Created directory: {Config.FILES_DIRECTORY}")

        # Start the Flask app
        logger.info("Starting API server...")
        port = int(environ.get('PORT', 5007))
        app.run(debug=True, host='0.0.0.0', port=port)
    except Exception as e:
        logger.critical(f"Failed to start API server: {str(e)}")
        raise

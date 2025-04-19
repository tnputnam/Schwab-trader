import unittest
from datetime import datetime
import os
from schwab_trader.config import Config, DevelopmentConfig, TestingConfig, ProductionConfig

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        # Store original environment variables
        self.original_env = dict(os.environ)

    def tearDown(self):
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_base_configuration(self):
        """Test base configuration values."""
        self.assertIsNotNone(self.config.SECRET_KEY)
        self.assertIsNotNone(self.config.SQLALCHEMY_DATABASE_URI)
        self.assertTrue(self.config.SESSION_COOKIE_SECURE)
        self.assertTrue(self.config.REMEMBER_COOKIE_SECURE)

    def test_validation_rules(self):
        """Test configuration validation rules."""
        # Test valid values
        self.config.NEWS_UPDATE_INTERVAL = 300
        self.config.ANALYSIS_HISTORICAL_DAYS = 365
        self.config.REALTIME_UPDATE_INTERVAL = 5
        self.config.STRATEGY_TEST_INITIAL_CAPITAL = 100000
        self.config.STRATEGY_TEST_COMMISSION = 0.01

        errors = self.config.validate_config()
        self.assertEqual(len(errors), 0)

        # Test invalid values
        self.config.NEWS_UPDATE_INTERVAL = 30  # Below minimum
        self.config.ANALYSIS_HISTORICAL_DAYS = 4000  # Above maximum
        self.config.REALTIME_UPDATE_INTERVAL = 0  # Below minimum
        self.config.STRATEGY_TEST_INITIAL_CAPITAL = 500  # Below minimum
        self.config.STRATEGY_TEST_COMMISSION = 0.2  # Above maximum

        errors = self.config.validate_config()
        self.assertGreater(len(errors), 0)

    def test_format_validation(self):
        """Test format validation rules."""
        # Test valid formats
        self.config.STRATEGY_TEST_START_DATE = '2020-01-01'
        self.config.STRATEGY_TEST_END_DATE = '2023-12-31'
        self.config.NEWS_SOURCES = '["reuters", "bloomberg"]'
        self.config.SCHWAB_API_BASE_URL = 'https://api.schwab.com'

        errors = self.config.validate_config()
        self.assertEqual(len(errors), 0)

        # Test invalid formats
        self.config.STRATEGY_TEST_START_DATE = '2020/01/01'  # Wrong format
        self.config.NEWS_SOURCES = 'not a json array'  # Invalid JSON
        self.config.SCHWAB_API_BASE_URL = 'not a url'  # Invalid URL

        errors = self.config.validate_config()
        self.assertGreater(len(errors), 0)

    def test_date_dependency_validation(self):
        """Test date dependency validation."""
        # Test valid dates
        self.config.STRATEGY_TEST_START_DATE = '2020-01-01'
        self.config.STRATEGY_TEST_END_DATE = '2023-12-31'

        errors = self.config.validate_config()
        self.assertEqual(len(errors), 0)

        # Test invalid dates (end before start)
        self.config.STRATEGY_TEST_START_DATE = '2023-12-31'
        self.config.STRATEGY_TEST_END_DATE = '2020-01-01'

        errors = self.config.validate_config()
        self.assertGreater(len(errors), 0)

    def test_environment_variables(self):
        """Test environment variable loading."""
        # Set environment variables
        os.environ['NEWS_UPDATE_INTERVAL'] = '300'
        os.environ['ANALYSIS_HISTORICAL_DAYS'] = '365'
        os.environ['NEWS_SOURCES'] = '["reuters", "bloomberg"]'
        os.environ['STRATEGY_TEST_START_DATE'] = '2020-01-01'

        # Create new config instance to load environment variables
        config = Config()
        
        self.assertEqual(config.NEWS_UPDATE_INTERVAL, 300)
        self.assertEqual(config.ANALYSIS_HISTORICAL_DAYS, 365)
        self.assertEqual(config.NEWS_SOURCES, '["reuters", "bloomberg"]')
        self.assertEqual(config.STRATEGY_TEST_START_DATE, '2020-01-01')

    def test_missing_required_values(self):
        """Test handling of missing required values."""
        # Remove required environment variables
        if 'SCHWAB_API_KEY' in os.environ:
            del os.environ['SCHWAB_API_KEY']
        if 'SCHWAB_API_SECRET' in os.environ:
            del os.environ['SCHWAB_API_SECRET']

        config = Config()
        self.assertIsNone(config.SCHWAB_API_KEY)
        self.assertIsNone(config.SCHWAB_API_SECRET)

    def test_invalid_numeric_values(self):
        """Test handling of invalid numeric values."""
        # Set invalid numeric values
        os.environ['NEWS_UPDATE_INTERVAL'] = 'not a number'
        os.environ['ANALYSIS_HISTORICAL_DAYS'] = 'invalid'
        os.environ['STRATEGY_TEST_INITIAL_CAPITAL'] = 'abc'

        config = Config()
        errors = config.validate_config()
        self.assertGreater(len(errors), 0)

    def test_directory_creation(self):
        """Test automatic directory creation."""
        # Set custom directory paths
        os.environ['LOG_DIR'] = 'test_logs'
        os.environ['SESSION_FILE_DIR'] = 'test_sessions'

        config = Config()
        config.init_app(None)  # Pass None as app since we only need directory creation

        self.assertTrue(os.path.exists('test_logs'))
        self.assertTrue(os.path.exists('test_sessions'))
        self.assertTrue(os.path.exists('data'))

        # Clean up
        os.rmdir('test_logs')
        os.rmdir('test_sessions')
        os.rmdir('data')

class TestEnvironmentConfigs(unittest.TestCase):
    def setUp(self):
        # Store original environment variables
        self.original_env = dict(os.environ)

    def tearDown(self):
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_development_config(self):
        """Test development environment configuration."""
        config = DevelopmentConfig()
        self.assertTrue(config.DEBUG)
        self.assertTrue(config.SQLALCHEMY_ECHO)
        self.assertFalse(config.SESSION_COOKIE_SECURE)
        self.assertEqual(config.NEWS_UPDATE_INTERVAL, 60)
        self.assertEqual(config.REALTIME_UPDATE_INTERVAL, 2)

    def test_testing_config(self):
        """Test testing environment configuration."""
        config = TestingConfig()
        self.assertTrue(config.TESTING)
        self.assertFalse(config.WTF_CSRF_ENABLED)
        self.assertEqual(config.SQLALCHEMY_DATABASE_URI, 'sqlite:///:memory:')
        self.assertEqual(config.NEWS_UPDATE_INTERVAL, 30)
        self.assertEqual(config.REALTIME_UPDATE_INTERVAL, 1)

    def test_production_config(self):
        """Test production environment configuration."""
        config = ProductionConfig()
        self.assertFalse(config.DEBUG)
        self.assertFalse(config.SQLALCHEMY_ECHO)
        self.assertTrue(config.SESSION_COOKIE_SECURE)
        self.assertEqual(config.NEWS_UPDATE_INTERVAL, 300)
        self.assertEqual(config.REALTIME_UPDATE_INTERVAL, 5)

    def test_environment_switching(self):
        """Test switching between environments."""
        # Test development environment
        os.environ['FLASK_ENV'] = 'development'
        config = DevelopmentConfig()
        self.assertTrue(config.DEBUG)

        # Test production environment
        os.environ['FLASK_ENV'] = 'production'
        config = ProductionConfig()
        self.assertFalse(config.DEBUG)

        # Test default environment
        del os.environ['FLASK_ENV']
        config = Config()
        self.assertFalse(config.DEBUG)  # Default should be production-like

if __name__ == '__main__':
    unittest.main() 
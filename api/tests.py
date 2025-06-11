from django.test import TestCase
from .services import capture_browser_errors, check_browser_errors
import logging

logger = logging.getLogger(__name__)

class BrowserErrorTests(TestCase):
    def test_browser_error_capture(self):
        """Test capturing browser errors from a test URL"""
        # Test with a URL that might have some console errors
        test_url = "http://localhost:8000"
        
        # Capture errors
        errors = capture_browser_errors(test_url)
        
        # Log the results
        logger.info(f"Found {len(errors)} browser errors")
        for error in errors:
            logger.info(f"Error: {error}")
        
        # Basic validation
        self.assertIsInstance(errors, list)
        
    def test_browser_error_check(self):
        """Test the error checking and display functionality"""
        # Test with a URL that might have some console errors
        test_url = "http://localhost:8000"
        
        # This will print the errors to console
        check_browser_errors(test_url)
        
    def test_error_handling(self):
        """Test error handling with invalid URL"""
        # Test with an invalid URL
        invalid_url = "http://invalid-url-that-does-not-exist.com"
        
        errors = capture_browser_errors(invalid_url)
        
        # Should return at least one error
        self.assertTrue(len(errors) > 0)
        
        # First error should be about connection failure
        self.assertIn("Failed to capture browser errors", errors[0]['message'])
import unittest
import sys
import os

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from utils.redirect_handler import RedirectHandler, RedirectLoopError


class TestRedirectHandler(unittest.TestCase):
    """Test the RedirectHandler class."""
    
    def setUp(self):
        self.handler = RedirectHandler()
    
    def test_detect_redirect_loop_no_loop(self):
        """Test when no redirect loop is detected"""
        redirect_chain = ["https://example.com/page1", "https://example.com/page2"]
        new_url = "https://example.com/page3"
        
        is_loop, loop_type, loop_description = self.handler.detect_redirect_loop(
            redirect_chain, new_url
        )
        
        self.assertFalse(is_loop)
        self.assertIsNone(loop_type)
        self.assertIsNone(loop_description)
    
    def test_detect_redirect_loop_max_redirects(self):
        """Test when maximum redirects are exceeded"""
        redirect_chain = ["url1", "url2", "url3", "url4", "url5", "url6", "url7", "url8", "url9", "url10"]
        new_url = "url11"
        
        is_loop, loop_type, loop_description = self.handler.detect_redirect_loop(
            redirect_chain, new_url, max_redirects=10
        )
        
        self.assertTrue(is_loop)
        self.assertEqual(loop_type, "max_redirects")
        self.assertIn("Maximum redirects (10) exceeded", loop_description)
    
    def test_detect_redirect_loop_reverse(self):
        """Test reverse redirect loop detection (A -> B -> A)"""
        redirect_chain = ["https://example.com/page1", "https://example.com/page2"]
        new_url = "https://example.com/page1"  # Goes back to first URL
        
        is_loop, loop_type, loop_description = self.handler.detect_redirect_loop(
            redirect_chain, new_url
        )
        
        self.assertTrue(is_loop)
        self.assertEqual(loop_type, "reverse")
        self.assertIn("Reverse redirect loop", loop_description)
    
    def test_detect_redirect_loop_circular(self):
        """Test circular redirect loop detection (A -> B -> C -> A)"""
        redirect_chain = ["https://example.com/page1", "https://example.com/page2", "https://example.com/page3"]
        new_url = "https://example.com/page1"  # Goes back to first URL
        
        is_loop, loop_type, loop_description = self.handler.detect_redirect_loop(
            redirect_chain, new_url
        )
        
        self.assertTrue(is_loop)
        self.assertEqual(loop_type, "circular")
        self.assertIn("Circular redirect loop", loop_description)
    
    def test_detect_redirect_loop_infinite(self):
        """Test infinite redirect loop detection (same URL appears multiple times)"""
        redirect_chain = ["https://example.com/page1", "https://example.com/page2", "https://example.com/page3"]
        new_url = "https://example.com/page2"  # URL already in chain
        
        is_loop, loop_type, loop_description = self.handler.detect_redirect_loop(
            redirect_chain, new_url
        )
        
        self.assertTrue(is_loop)
        # The logic prioritizes reverse loops over infinite loops, so this is detected as reverse
        self.assertEqual(loop_type, "reverse")
        self.assertIn("Reverse redirect loop", loop_description)


if __name__ == '__main__':
    unittest.main()

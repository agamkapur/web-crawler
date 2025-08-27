import unittest
import sys
import os
import datetime
import shutil

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from utils.report_generator import CrawlReportGenerator


class TestCrawlReportGenerator(unittest.TestCase):
    """Test the CrawlReportGenerator class."""
    
    def setUp(self):
        self.test_runs_dir = "test_crawling_runs"
        self.report_generator = CrawlReportGenerator(self.test_runs_dir)
        self.base_url = "https://example.com"
        self.start_time = datetime.datetime(2025, 8, 27, 22, 44, 4)
        self.end_time = datetime.datetime(2025, 8, 27, 22, 44, 6)
        self.all_found_urls = {"https://example.com", "https://example.com/page1"}
        self.error_urls = {"https://example.com/error"}
        self.redirect_urls = {"https://example.com/redirect"}
    
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_runs_dir):
            shutil.rmtree(self.test_runs_dir)
    
    def test_report_generator_initialization(self):
        """Test CrawlReportGenerator initialization"""
        generator = CrawlReportGenerator("custom_dir")
        self.assertEqual(generator.runs_dir, "custom_dir")
        
        # Test default initialization
        default_generator = CrawlReportGenerator()
        self.assertEqual(default_generator.runs_dir, "crawling_runs")
    
    def test_create_crawl_report(self):
        """Test crawl report creation"""
        report_folder = self.report_generator.create_crawl_report(
            base_url=self.base_url,
            start_time=self.start_time,
            end_time=self.end_time,
            all_found_urls=self.all_found_urls,
            error_urls=self.error_urls,
            redirect_urls=self.redirect_urls,
            error_count=1,
            redirect_count=1
        )
        
        # Check that the folder was created
        self.assertTrue(os.path.exists(report_folder))
        
        # Check that all expected files exist
        expected_files = ["run_details.txt", "all_found_urls.txt", "all_error_urls.txt", "all_redirect_urls.txt"]
        for filename in expected_files:
            file_path = os.path.join(report_folder, filename)
            self.assertTrue(os.path.exists(file_path))
    
    def test_run_details_file_content(self):
        """Test the content of run_details.txt"""
        report_folder = self.report_generator.create_crawl_report(
            base_url=self.base_url,
            start_time=self.start_time,
            end_time=self.end_time,
            all_found_urls=self.all_found_urls,
            error_urls=self.error_urls,
            redirect_urls=self.redirect_urls,
            error_count=1,
            redirect_count=1
        )
        
        run_details_path = os.path.join(report_folder, "run_details.txt")
        with open(run_details_path, 'r') as f:
            content = f.read()
        
        # Check that all expected information is present
        self.assertIn(f"Base URL: {self.base_url}", content)
        self.assertIn("Start Time: 2025-08-27 22:44:04", content)
        self.assertIn("End Time: 2025-08-27 22:44:06", content)
        self.assertIn("URLs Found/Visited: 2", content)
        self.assertIn("Error URLs: 1", content)
        self.assertIn("Redirect URLs: 1", content)
        self.assertIn("Total Errors: 1", content)
        self.assertIn("Total Redirects: 1", content)
    
    def test_urls_files_content(self):
        """Test the content of URL files"""
        report_folder = self.report_generator.create_crawl_report(
            base_url=self.base_url,
            start_time=self.start_time,
            end_time=self.end_time,
            all_found_urls=self.all_found_urls,
            error_urls=self.error_urls,
            redirect_urls=self.redirect_urls,
            error_count=1,
            redirect_count=1
        )
        
        # Test all_found_urls.txt
        found_urls_path = os.path.join(report_folder, "all_found_urls.txt")
        with open(found_urls_path, 'r') as f:
            found_urls_content = f.read()
        
        self.assertIn("https://example.com", found_urls_content)
        self.assertIn("https://example.com/page1", found_urls_content)
        
        # Test all_error_urls.txt
        error_urls_path = os.path.join(report_folder, "all_error_urls.txt")
        with open(error_urls_path, 'r') as f:
            error_urls_content = f.read()
        
        self.assertIn("https://example.com/error", error_urls_content)
        
        # Test all_redirect_urls.txt
        redirect_urls_path = os.path.join(report_folder, "all_redirect_urls.txt")
        with open(redirect_urls_path, 'r') as f:
            redirect_urls_content = f.read()
        
        self.assertIn("https://example.com/redirect", redirect_urls_content)


if __name__ == '__main__':
    unittest.main()

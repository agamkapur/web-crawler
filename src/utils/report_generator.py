import os
import datetime
from typing import Set
import logging

logger = logging.getLogger(__name__)


class CrawlReportGenerator:
    """Handles generation of detailed crawl reports."""

    def __init__(self, runs_dir: str = "crawling_runs"):
        """
        Initialize the report generator.

        Args:
            runs_dir: Directory where crawl reports will be stored
        """
        self.runs_dir = runs_dir

    def create_crawl_report(
        self,
        base_url: str,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        all_found_urls: Set[str],
        error_urls: Set[str],
        redirect_urls: Set[str],
        error_count: int,
        redirect_count: int,
    ) -> str:
        """
        Create a detailed crawl report in a timestamped folder.

        Args:
            base_url: The base URL that was crawled
            start_time: When the crawl started
            end_time: When the crawl ended
            all_found_urls: Set of all URLs found during the crawl
            error_urls: Set of URLs that encountered errors
            redirect_urls: Set of URLs that issued redirects
            error_count: Total number of errors encountered
            redirect_count: Total number of redirects followed

        Returns:
            Path to the created report folder
        """
        try:
            # Create crawling_runs directory if it doesn't exist
            if not os.path.exists(self.runs_dir):
                os.makedirs(self.runs_dir)

            # Create timestamped folder name
            timestamp = start_time.strftime("%Y-%m-%d_%H-%M-%S")
            run_folder = os.path.join(self.runs_dir, timestamp)
            os.makedirs(run_folder, exist_ok=True)

            # Calculate total time taken
            total_time = end_time - start_time

            # Create run_details.txt
            self._create_run_details_file(
                run_folder,
                base_url,
                start_time,
                end_time,
                total_time,
                all_found_urls,
                error_urls,
                redirect_urls,
                error_count,
                redirect_count,
            )

            # Create all_found_urls.txt
            self._create_urls_file(run_folder, "all_found_urls.txt", all_found_urls)

            # Create all_error_urls.txt
            self._create_urls_file(run_folder, "all_error_urls.txt", error_urls)

            # Create all_redirect_urls.txt
            self._create_urls_file(run_folder, "all_redirect_urls.txt", redirect_urls)

            logger.info(f"Crawl report created in: {run_folder}")
            return run_folder

        except Exception as e:
            logger.error(f"Failed to create crawl report: {e}")
            raise

    def _create_run_details_file(
        self,
        run_folder: str,
        base_url: str,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        total_time: datetime.timedelta,
        all_found_urls: Set[str],
        error_urls: Set[str],
        redirect_urls: Set[str],
        error_count: int,
        redirect_count: int,
    ) -> None:
        """
        Create the run_details.txt file with crawl statistics.

        Args:
            run_folder: Path to the report folder
            base_url: The base URL that was crawled
            start_time: When the crawl started
            end_time: When the crawl ended
            total_time: Total time taken for the crawl
            all_found_urls: Set of all URLs found during the crawl
            error_urls: Set of URLs that encountered errors
            redirect_urls: Set of URLs that issued redirects
            error_count: Total number of errors encountered
            redirect_count: Total number of redirects followed
        """
        run_details_path = os.path.join(run_folder, "run_details.txt")
        with open(run_details_path, "w") as f:
            f.write(f"Base URL: {base_url}\n")
            f.write(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Time: {total_time}\n")
            f.write(f"URLs Found/Visited: {len(all_found_urls)}\n")
            f.write(f"Error URLs: {len(error_urls)}\n")
            f.write(f"Redirect URLs: {len(redirect_urls)}\n")
            f.write(f"Total Errors: {error_count}\n")
            f.write(f"Total Redirects: {redirect_count}\n")

    def _create_urls_file(self, run_folder: str, filename: str, urls: Set[str]) -> None:
        """
        Create a file containing a list of URLs.

        Args:
            run_folder: Path to the report folder
            filename: Name of the file to create
            urls: Set of URLs to write to the file
        """
        file_path = os.path.join(run_folder, filename)
        with open(file_path, "w") as f:
            for url in sorted(urls):
                f.write(f"{url}\n")

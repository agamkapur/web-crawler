import asyncio
import aiohttp
from urllib.parse import urljoin
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class RedirectLoopError(Exception):
    """Exception raised when a redirect loop is detected."""

    pass


class RedirectHandler:
    """Handles redirect logic and loop detection."""

    @staticmethod
    def detect_redirect_loop(
        redirect_chain: List[str], new_url: str, max_redirects: int = 10
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Detect various types of redirect loops.

        Args:
            redirect_chain: List of URLs in the current redirect chain
            new_url: The new URL to check
            max_redirects: Maximum number of redirects allowed

        Returns:
            tuple: (is_loop, loop_type, loop_description)
        """
        if len(redirect_chain) >= max_redirects:
            return (
                True,
                "max_redirects",
                f"Maximum redirects ({max_redirects}) exceeded",
            )

        # Check for reverse loop (A -> B -> A pattern)
        if len(redirect_chain) >= 2:
            if new_url == redirect_chain[-2]:
                return (
                    True,
                    "reverse",
                    f"Reverse redirect loop: {redirect_chain[-1]} -> {new_url}",
                )

        # Check for circular loop (A -> B -> C -> A pattern)
        if len(redirect_chain) >= 3:
            if new_url == redirect_chain[-3]:
                return (
                    True,
                    "circular",
                    f"Circular redirect loop: {redirect_chain[-2]} -> "
                    f"{redirect_chain[-1]} -> {new_url}",
                )

        # Check for longer circular patterns
        if len(redirect_chain) >= 4:
            for i in range(len(redirect_chain) - 3):
                if new_url == redirect_chain[i]:
                    return (
                        True,
                        "circular",
                        f"Circular redirect loop detected at position {i}",
                    )

        # Check for infinite loop (same URL appears multiple times)
        if new_url in redirect_chain:
            return True, "infinite", f"Infinite redirect loop detected: {new_url}"

        return False, None, None

    async def follow_redirects(
        self, session: aiohttp.ClientSession, url: str, config
    ) -> tuple[str, List[str], Optional[tuple[aiohttp.ClientResponse, str]]]:
        """
        Follow redirects safely with loop detection.

        Args:
            session: aiohttp client session
            url: The URL to follow redirects for
            config: Crawl configuration object with timeout and max_redirects attributes

        Returns:
            tuple: (final_url, redirect_chain, response_data) where response_data is
            (response, content) or None

        Raises:
            RedirectLoopError: If a redirect loop is detected
        """
        redirect_chain = [url]
        current_url = url

        timeout_obj = aiohttp.ClientTimeout(total=config.timeout)

        for redirect_count in range(config.max_redirects):
            try:
                async with session.get(
                    current_url, timeout=timeout_obj, allow_redirects=False
                ) as response:
                    # Check if we got a redirect response
                    if response.status in [301, 302, 303, 307, 308]:
                        # Get the redirect location
                        redirect_url = response.headers.get("Location")
                        if not redirect_url:
                            # No Location header, read content and return
                            try:
                                content = await response.text()
                                return current_url, redirect_chain, (response, content)
                            except Exception as e:
                                logger.warning(
                                    f"  Failed to read response content: {e}"
                                )
                                return current_url, redirect_chain, None

                        # Convert relative redirect URL to absolute
                        redirect_url = urljoin(current_url, redirect_url)

                        # Check for redirect loop
                        is_loop, loop_type, loop_description = (
                            self.detect_redirect_loop(
                                redirect_chain, redirect_url, config.max_redirects
                            )
                        )
                        if is_loop:
                            raise RedirectLoopError(
                                f"Redirect loop detected: {loop_description}"
                            )

                        # Add to redirect chain and continue
                        redirect_chain.append(redirect_url)
                        current_url = redirect_url

                        logger.info(
                            f"  Redirect {redirect_count + 1}: "
                            f"{redirect_chain[-2]} -> {redirect_chain[-1]}"
                        )

                    else:
                        # No more redirects, read content and return the final URL
                        try:
                            content = await response.text()
                            return current_url, redirect_chain, (response, content)
                        except Exception as e:
                            logger.warning(f"  Failed to read response content: {e}")
                            return current_url, redirect_chain, None

            except (aiohttp.ClientError, asyncio.TimeoutError):
                # If we can't follow redirects, return what we have
                return current_url, redirect_chain, None

        # If we've reached max redirects, raise an error
        raise RedirectLoopError(f"Maximum redirects ({config.max_redirects}) exceeded")

import json
import time
import logging
import requests

from logging import Logger
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log

from utils.Config import Config
from utils.Constants import Constants

class CircuitBreakerException(Exception):
    """Custom exception to raise when the circuit breaker trips."""
    pass

class QueryHandler:
    def __init__(
        self,
        config: Config,
        logger: Logger,
        session,
        leetcode_headers:str = None):

        self.config = config
        self.logger = logger
        self.leetcode_headers = leetcode_headers or Constants.LEETCODE_HEADERS
        self.session = session
        self.circuit_open = False
        self.circuit_reset_time = 0
        self.retry_count = self.config.api_retry_count
        self.max_failures = 3  # Number of failures before the circuit breaker trips
        self.circuit_timeout = 60  # Timeout duration for circuit breaker (in seconds)

    def is_circuit_open(self):
        """Check if the circuit breaker is open."""
        if self.circuit_open and time.time() >= self.circuit_reset_time:
            # Reset the circuit breaker after the timeout period
            self.circuit_open = False
            self.retry_count = 0
            self.logger.info("Circuit breaker closed. Requests can proceed.")
        return self.circuit_open

    def open_circuit(self):
        """Open the circuit breaker."""
        self.circuit_open = True
        self.circuit_reset_time = time.time() + self.circuit_timeout
        self.logger.error("Circuit breaker opened. No requests will be made for 60 seconds.")

    def log_before_retry(self, retry_state):
        """Custom logger function to access self.logger before retry."""
        self.logger.warning(f"Retrying... Attempt number: {retry_state.attempt_number}")

    @retry(
        stop=stop_after_attempt(3),  # Retry 3 times
        wait=wait_exponential(multiplier=1, min=1, max=10),  # Exponential backoff
        before_sleep=log_before_retry,  # Use the custom logger method
        reraise=True  # Raise the final exception after retries are exhausted
    )
    def query(self, method="post", query=None, selector=None, url=None, headers=None):
        # Check if the circuit is open
        if self.is_circuit_open():
            raise CircuitBreakerException("Circuit breaker is open, requests are blocked.")

        headers = headers or self.leetcode_headers
        url = url or Constants.LEETCODE_GRAPHQL_URL

        try:
            # Make the request
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=query
            )

            # Raise an error if the response status is not 2xx
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '').lower()
            is_json = 'application/json' in content_type

            if is_json:
                response_content = json.loads(response.content)
                data = response_content

                # Check if the selector is callable (a method) or a list of keys
                if callable(selector):
                    data = selector(response_content)
                elif isinstance(selector, list):
                    data = self.extract_by_selector(response_content, selector)
            else:
                data = response.text

            # If the request is successful, reset retry count
            self.retry_count = 0
            return data

        except requests.RequestException as e:
            # Increment the failure counter
            self.retry_count += 1
            self.logger.error(f"Request failed: {e}. Failure count: {self.retry_count}")

            # If max failures are reached, open the circuit breaker
            if self.retry_count >= self.max_failures:
                self.open_circuit()

            # Reraise the exception to trigger the retry mechanism in @retry
            raise e

    #region basic method
    def extract_by_selector(self, response_content, selector):
        """
        Navigate through the response_content using the keys and/or indices in the selector.
        The selector can contain both dictionary keys (strings) and list indices (integers).
        """
        data = response_content

        for key in selector:
            # Check if the current element is a dictionary and the key is a string
            if isinstance(data, dict) and isinstance(key, str):
                if key in data:
                    data = data[key]
                else:
                    raise KeyError(f"Key '{key}' not found in response_content")
            # Check if the current element is a list and the key is an integer (index)
            elif isinstance(data, list) and isinstance(key, int):
                try:
                    data = data[key]
                except IndexError:
                    raise IndexError(f"Index '{key}' out of range in response_content list")
            else:
                raise ValueError(f"Unexpected type for key: {key}. Expected str for dict or int for list.")

        return data

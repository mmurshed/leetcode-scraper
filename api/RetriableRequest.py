import json
import time
import requests

from logging import Logger
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log, retry_if_exception

from utils.Config import Config
from utils.Constants import Constants

class CircuitBreakerException(Exception):
    """Custom exception to raise when the circuit breaker trips."""
    pass

class RetriableRequest:
    def __init__(
        self,
        config: Config,
        logger: Logger,
        session):

        self.config = config
        self.logger = logger
        self.session = session
        self.circuit_open = False
        self.circuit_reset_time = 0
        self.retry_count = 0
        self.max_failures = self.config.api_max_failures  # Number of failures before the circuit breaker trips
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

    def log_before_retry(retry_state):
        """Custom logger function to access self.logger before retry."""
        # self.logger.warning(f"Retrying... Attempt number: {retry_state.attempt_number}")

    def should_retry(exception):
        """
        Custom retry condition to skip retries for HTTP 4xx errors.
        """
        if isinstance(exception, requests.HTTPError):
            # Ensure the response object exists and has a valid status code
            if exception.response:
                status_code = exception.response.status_code
                if 400 <= status_code < 500:
                    # Skip retry for client-side HTTP errors (4xx)
                    return False
        # Retry for all other exceptions
        return True

    @retry(
        stop=stop_after_attempt(3),  # Retry 3 times
        wait=wait_exponential(multiplier=1, min=1, max=10),  # Exponential backoff
        before_sleep=log_before_retry,  # Use the custom logger method
        retry=retry_if_exception(should_retry),  # Use custom retry condition
        reraise=True  # Raise the final exception after retries are exhausted
    )
    def request(self, method="post", request=None, selector=None, url=None, headers=None):
        # Check if the circuit is open
        if self.is_circuit_open():
            raise CircuitBreakerException("Circuit breaker is open, requests are blocked.")

        try:
            # Make the request
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=request
            )

            # Raise an error if the response status is not 2xx
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '').lower()

            if 'application/json' in content_type:
                response_content = json.loads(response.content)
                data = response_content

                # Check if the selector is callable (a method) or a list of keys
                if callable(selector):
                    data = selector(response_content)
                elif isinstance(selector, list):
                    data = self.extract_by_selector(response_content, selector)
            elif 'text/' in content_type:
                # Handle text data
                data = response.text
            else:
                # Handle binary data
                data = response.content  # Raw binary data

            # If the request is successful, reset retry count
            self.retry_count = 0
            return data

        except requests.RequestException as e:
            # Check if this is a 404 error - don't count it towards circuit breaker
            is_404 = False
            if isinstance(e, requests.HTTPError) and e.response and e.response.status_code == 404:
                is_404 = True
                self.logger.warning(f"404 Not Found: {e}. Skipping without counting towards circuit breaker.")
            else:
                # Increment the failure counter only for non-404 errors
                self.retry_count += 1
                self.logger.error(f"Request failed: {e}. Failure count: {self.retry_count}")
                self.logger.error(f"method: {method}")
                self.logger.error(f"request: {request}")

                # If max failures are reached, open the circuit breaker
                if self.retry_count >= self.max_failures:
                    self.open_circuit()

            # Reraise the exception to trigger the retry mechanism in @retry (or exit if 404)
            raise e

    #region basic method
    def extract_by_selector(self, response_content, selector):
        """
        Navigate through the response_content using the keys and/or indices in the selector.
        The selector can contain both dictionary keys (strings) and list indices (integers).
        """
        data = response_content

        for key in selector:
            if not data:
                self.logger.error(f"Data is null for key: {key}, selector: {selector}, response: {response_content}")
                return data
            # Check if the current element is a dictionary and the key is a string
            elif isinstance(data, dict) and isinstance(key, str):
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
                self.logger.debug(f"Response content: {response_content}")
                raise ValueError(f"Unexpected type for key: {key}. Expected str for dict or int for list. Data: {data}")

        return data

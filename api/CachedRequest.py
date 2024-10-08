import requests

from logging import Logger

from api.RetriableRequest import CircuitBreakerException, RetriableRequest
from utils.Config import Config
from utils.Constants import Constants

class CachedRequest:
    def __init__(
        self,
        config: Config,
        logger: Logger,
        cache):

        self.config = config
        self.logger = logger
        self.cache = cache

        self.cache_expiration_seconds = self.config.cache_expiration_days * 24 * 60 * 60
        self.reqh = RetriableRequest(
            config=self.config,
            logger=self.logger,
            session=requests.Session())
    
    def key(self, *args):
        # Convert all arguments to strings and join them with '-'
        return '-'.join(map(str, args))
        
    def request(self, key, method="post", request=None, selector=None, url=None, headers=None):
        """
        This function caches and performs a request if data is not already cached.
        Optionally uses a selector to filter out the required part of the response.
        """

        headers = headers or Constants.LEETCODE_HEADERS
        url = url or Constants.LEETCODE_GRAPHQL_URL

        if not self.config.cache_api_calls:
            self.logger.debug(f"Cache bypass {key}")
            try:
                data = self.reqh.request(
                    method=method,
                    request=request,
                    selector=selector,
                    url=url,
                    headers=headers)
                return data
            except CircuitBreakerException as e:
                self.logger.warning(f"Request blocked by circuit breaker: {e}")
            except requests.RequestException as e:
                self.logger.error(f"Request failed after retries: {e}")
            return data

        # Check if data exists in the cache and retrieve it
        data = self.cache.get(key=key)

        if data is None:
            self.logger.debug(f"Cache miss {key}")
            # If cache miss, make the request
            try:
                data = self.reqh.request(
                    method=method,
                    request=request,
                    selector=selector,
                    url=url,
                    headers=headers)
            except CircuitBreakerException as e:
                self.logger.warning(f"Request blocked by circuit breaker: {e}")
            except requests.RequestException as e:
                self.logger.error(f"Request failed after retries: {e}")

            # Store data in the cache
            if data:
                self.cache.set(
                    key=key,
                    value=data,
                    expire=self.cache_expiration_seconds)
        else:
            self.logger.debug(f"Cache hit {key}")

        return data

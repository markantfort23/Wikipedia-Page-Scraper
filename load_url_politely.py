
import re
from urllib.parse import urlparse
import requests
from os import mkdir
from os.path import exists
import time

requested_urls = []
max_url_requests = 50

def load_url_politely(url, cache_file_name=None, ignore_cache=False):
	

	"""
	webscraping as politely as possible

	When requesting site, make local "cached copy"
	if we have a cached copy, use that instead of asking server.

	"""

	print(f"--- LOAD URL: '{url}' (politely) ---")
		
	# Make a cache folder if we don't have one
	cache_dir = "cache"
	if not exists(cache_dir):
		print("\t...No cache directory yet, creating one")
		mkdir(cache_dir)

	# Set the initial last request time
	if not hasattr(load_url_politely, "last_request_time"):
		load_url_politely.last_request_time = -10

	# Generate a cache name, if we don't have one, by parsing the URL
	if not cache_file_name:
		parsed = urlparse(url)
		cache_file_name = parsed.netloc.split(".")[-2] + re.sub(
							"[^0-9a-zA-Z]+", "_", parsed.path)
		if cache_file_name[-1] == "_": cache_file_name = cache_file_name[0:-1]


	file_path = f"{cache_dir}/{cache_file_name}.html"
	
	# file already exist? Use the cache!
	if exists(file_path) and not ignore_cache:
		
		# Read from cache
		cached_html = open(file_path).read()
		print(f"\t...Successfully loaded '{url}' from cache '{file_path}'")
		return cached_html

	else:
		# Cache doesn't exist- Load from real Wikipedia

		# How long has it been since we made a request?
		current_time = time.process_time()
		time_elapsed = (current_time - load_url_politely.last_request_time) * 1000
		load_url_politely.last_request_time = current_time 

		# If we made a request recently, wait 1 second before making a new request
		if time_elapsed < 100:
			print(f'\tLast request at time {load_url_politely.last_request_time:.5f}s, elapsed {round(time_elapsed)} ms ({url})')
			print("\t*** Sleeping for 1 second ***")
			time.sleep(.2)
			# return None

		# Add to total requests
		requested_urls.append(url)
		if len(requested_urls) > max_url_requests:
			print("**** YOU MAY HAVE A BUG CAUSING TOO MANY URL REQUESTS: ****")
			print("**** FREEZING REQUEST ACCESS FOR SAFETY FOR THIS PROGRAM RUN ****")
			print("Last URLs requested: ", requested_urls)
			raise ValueError('Requested too many URLS')


		# Start a timer
		start_request = time.process_time()

		# Attempt to read the URL from Wikipedia
		try:
			page_response = requests.get(url)

		# Deal with if the site is down or doesn't exist	
		except Exception as e:
			print(f"\t*** ERROR: Could not connect to url: {url} ***")
			print(e)
			return

		# Stop the timer and calculate how long the request took 
		stop_request = time.process_time()
		print(f"\tSuccessfully loaded from Wikipedia in {round((stop_request - start_request)*1000):4}ms:  {url}")

		# Save a cached copy
		with open(file_path, "w") as file:
			file.write(str(page_response.content))

		# Return the HTML content
		return page_response.content

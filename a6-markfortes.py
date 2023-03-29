from load_url_politely import load_url_politely
from bs4 import BeautifulSoup
import re
from treelib import Node, Tree
from datetime import datetime

def get_title(soup):
	assert isinstance(soup, BeautifulSoup), "Expected a soup object"
	# gets title of page
	title = soup.title.text
	remove = title.find(' - Wikipedia')
	return title[0:remove]

def get_last_edit(soup):
	assert isinstance(soup, BeautifulSoup), "Expected a soup object"

	# substrings that surround necessary info
	start_text = " on "
	end_text = ", at"

	# gets date of the last edit of this page (e.g. 9 November 2021)
	sentence = soup.find(id='footer-info-lastmod').text
	start = sentence.find(start_text)
	end = sentence.find(end_text)
	return sentence[(start + 4):end]
	# + 4 to remove the "on " before the date

def get_wordcount(soup):
	assert isinstance(soup, BeautifulSoup), "Expected a soup object"

	all_text = (soup.text)
	new = all_text.replace('\n', '')
	split_text = new.split()
	return len(split_text)

def get_all_links(soup):
	assert isinstance(soup, BeautifulSoup), "Expected a soup object"

	# gets a list of all urls linked to in this page
	all_a_tags = soup.find_all('a')
	urls = []
	for a in all_a_tags:
		if 'href' in a.attrs and a.attrs['href'] != '':
			urls.append(a.attrs['href'])
	return urls

def get_all_wiki_link_ids(soup):
	prefix = "/wiki/"
	urls = get_all_links(soup)
	article_ids = []
	for url in urls:
		if url.startswith(prefix) and ':' not in url and '#' not in url:
			article_ids.append(url[6:])
	return article_ids



def get_shortest_page(page_directory):
	# Assuming no wiki articles have more than a million words, any article will beat this
	winning_count = 999999
	winner = ''
	for id in page_directory:
		page = page_directory[id]
		if page.wordcount < winning_count:
			winning_count = page.wordcount
			winner = page
	
	return winner

def get_oldest_page(page_directory):
	# The timestamp for right now, any article is older than this
	winning_timestamp = datetime.today() 
	winner = None

	for id in page_directory:
		page = page_directory[id]
		time = datetime.strptime(page.last_edit, '%d %B %Y')
		if time<winning_timestamp:
			winning_timestamp = time
			winner = page
	
	return winner


class WikiPage:
	def __init__(self, page_directory, page_id):

		# asserts to catch if we pass in the wrong parameters
		assert isinstance(page_directory, dict), f"page_directory should be a dict not {page_directory}"
		assert not page_id.startswith("/wiki/"), "Expecting just the id a wiki article, not /wiki/some_id"
		assert not page_id.startswith("http"), "Expecting just the id of a wiki article, not the full url"

		# alerts whenever creating a new WikiPage
		print(f"\n★ Create WikiPage for '{page_id}'")

		# Create the URL of this page 
		# (what we need to pass to the load_url_politely function)
		wiki_prefix = "https://en.wikipedia.org/wiki/"
		self.url = wiki_prefix + page_id
		self.page_id = page_id
		self.page_directory = page_directory
		html = load_url_politely(self.url)
		self.soup = BeautifulSoup(html, 'html.parser')
		self.title = get_title(self.soup)
		self.wordcount = get_wordcount(self.soup)
		self.last_edit = get_last_edit(self.soup)

		self.page_directory[self.page_id] = self
		
		self.wiki_links = get_all_wiki_link_ids(self.soup)
		
	def load_links(self, recursion_count=0, links_per_article=5):
		"""
		Load the pages linked to from this article by making new
		WikiPage instances for them

		Parameters: 
			recursion_count: how "deep" we are recursing 
				(how many steps we can take away from the original page)
			links_per_article: how "broad" we are exploring 
				(how many links to load per page)
		"""

		print(f"\n➡ LOADING LINKS {links_per_article} links from {self.title}, recursion count {recursion_count} (this number should go down)")

		short_list = self.wiki_links[:links_per_article]
		for link in short_list:
			if link not in self.page_directory:
				page = WikiPage(self.page_directory, link)
				if recursion_count > 0:
					recursion_count -= 1
					page.load_links(recursion_count, links_per_article)


	def print_summary(self):
		# A utility to print out page facts
		
		print(f"{self.page_id} (title:'{self.title}')")
		print(f"\tURL:       {self.url}")
		print(f"\tLast edit: {self.last_edit}")
		print(f"\tWordcount: {self.wordcount}")
		link_text = ",".join(self.wiki_links[:5]) + "..." + ",".join(self.wiki_links[-5:])
		print(f"\t{len(self.wiki_links)} links:     {link_text}")

	def find_path(self, current_path, query_id, max_path_length=4):
		"""
		If this page has a path to this id, return the path

		Parameters: 
			current_path (list of str): The path we have taken so far, we need this 
				so we can see if we in a loop 
				(ie "Illinois -> US State -> Indiana -> Illinois -> US State".....) 
			query_id (str): The page id we are trying to get to
			max_path_length: the longest path we are allowed to take 
				(prevents unproductively long searches)
		"""
		next_path = current_path + [self.page_id]

		if self.page_id in current_path:
			return None

		if self.page_id == query_id:
			return next_path

		# Search all subpages
		for wiki_id in self.wiki_links:

			if wiki_id == query_id:
				return next_path + [wiki_id]

			# recurse
			if wiki_id in self.page_directory and len(current_path) < max_path_length:
				subpage = self.page_directory[wiki_id]
				potential_path = subpage.find_path(next_path, query_id, max_path_length)
				if potential_path:
					return potential_path
					
		return None


	def display_tree(self):
		""" 
		Tree visualization
		Create a new tree with this page as a starting node, then 
		recursively add all the subsequent pages and their links 
		"""

		print(f"\nTree diagram, starting at page '{self.title}'")
		tree = Tree()

		tree.create_node(self.page_id, self.page_id)
		self.add_to_tree(tree)
		tree.show()


	def add_to_tree(self, tree):
		""" 
		Add this node and all its links to this tree
		If any of the links are in the directory, also add them 
		recursively to the tree
		"""
		max_links_to_display = 15

		for link_id in self.wiki_links[0:max_links_to_display]:
			
			# Add this link to our tree, if it's not already in the tree
			if not tree.contains(link_id):

				tree.create_node(link_id, link_id, parent=self.page_id)
				if link_id in self.page_directory:	
					# recurse
					self.page_directory[link_id].add_to_tree(tree)
				

if __name__ == "__main__":


	#------------------------------------------------------------------
	# Clear the directory and load Cat
	print("\n------ Load RECURSIVELY ------")
	page_directory = {}
	cat_page = WikiPage(page_directory, "Cat")

	cat_page.load_links(links_per_article=2, recursion_count=3)
	cat_page.display_tree()
	print("All loaded pages ", page_directory.keys())
	assert "Istanbul" in page_directory, "If it loaded the links 3 links deep from Cat, 'Istanbul' should be in the directory (may change if Wikipedia is edited)"

	#------------------------------------------------------------------
	# Play Six Degrees of Wikipedia using find_path
	# (https://en.wikipedia.org/wiki/Wikipedia:Six_degrees_of_Wikipedia)

	# Try loading different pages, and find unexpected paths between topics

	# # Make sure we have some cat pages loaded
	cat_page = WikiPage(page_directory, "Cat")
	cat_page.load_links(links_per_article=5, recursion_count=1)

	# # Lets load two more sets of pages so we have more pages to play with
	evanston_page = WikiPage(page_directory, "Evanston,_Illinois")
	evanston_page.load_links(links_per_article=5, recursion_count=1)
	
	cs_page = WikiPage(page_directory, "Computer_science")
	cs_page.load_links(links_per_article=5, recursion_count=1)
	cs_page.display_tree()

	# # print("Total pages loaded", page_directory.keys())

	
	# # What other paths can we find with only 80 or so pages loaded?
	
	print(f"Path found from Cat to Evanston,_Illinois", page_directory["Cat"].find_path([], "Evanston,_Illinois"))
	print(f"Path found from Cat to Dinosaur", page_directory["Cat"].find_path([], "Dinosaur"))
	print(f"Path found from Cat to Computer_science", page_directory["Cat"].find_path([], "Computer_science"))
	print(f"Path found from Evanston,_Illinois to Cat", page_directory["Evanston,_Illinois"].find_path([], "Cat"))
	print(f"Path found from Cat to Cosplay", page_directory["Cat"].find_path([], "Cosplay"))
	print(f"Path found from Computer_science to Half-Life_(series)", page_directory["Computer_science"].find_path([], "Half-Life_(series)"))
	print(f"Path found from Computer_science to Chicago", page_directory["Computer_science"].find_path([], "Chicago"))
	print(f"Path found from Cats_(2019_film) to Chicago", page_directory["Cats_(2019_film)"].find_path([], "Chicago"))
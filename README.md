# Wikipedia Page Scraper
Using BeautifulSoup and Treelib libraries, builds a class "WikiPage" that stores information about individual wikipedia pages (e.g. RaisingofChicago)
and uses that class to build a directory of pages (a dict of WikiPage instances) indexed by the page name (eg. "raisingofchicago") to make queries and
display charts of how pages are connected. This project emphasizes object oriented programming and recursion techniques as well as working with the tree
data structure.

Also plays Six Degrees of Wikipedia (https://en.wikipedia.org/wiki/Wikipedia:Six_degrees_of_Wikipedia) to find often interesting paths between topics.

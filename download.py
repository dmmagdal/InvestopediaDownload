# download.py
# Download all articles organized by starting character in investopedia.
# Python 3.11
# Windows/MacOS/Linux


import argparse
import json
import os
import re
from typing import Dict, List

from bs4 import BeautifulSoup
import requests
from tqdm import tqdm


base_url = "https://www.investopedia.com/"
category_pages = [
	"terms-beginning-with-num-4769350",
	"terms-beginning-with-a-4769351",
	"terms-beginning-with-b-4769352",
	"terms-beginning-with-c-4769353",
	"terms-beginning-with-d-4769354",
	"terms-beginning-with-e-4769355",
	"terms-beginning-with-f-4769356",
	"terms-beginning-with-g-4769357",
	"terms-beginning-with-h-4769358",
	"terms-beginning-with-i-4769359",
	"terms-beginning-with-j-4769360",
	"terms-beginning-with-k-4769361",
	"terms-beginning-with-l-4769362",
	"terms-beginning-with-m-4769363",
	"terms-beginning-with-n-4769364",
	"terms-beginning-with-o-4769365",
	"terms-beginning-with-p-4769366",
	"terms-beginning-with-q-4769367",
	"terms-beginning-with-r-4769368",
	"terms-beginning-with-s-4769369",
	"terms-beginning-with-t-4769370",
	"terms-beginning-with-u-4769371",
	"terms-beginning-with-v-4769372",
	"terms-beginning-with-w-4769373",
	"terms-beginning-with-x-4769374",
	"terms-beginning-with-y-4769375",
	"terms-beginning-with-z-4769376",
]
category_pattern = r"terms-beginning-with-(.*?)-\d+"
article_pattern = r"\/([^\/]+)\.asp$"


def get_articles_from_term_page(term_link: str) -> List[str]:
	'''
	Retrieve all article links from the term patch.
	@param: term_link (str), the URL of the term page.
	@preturn: returns a list of links to key words from the term page.
	'''
	# Query the category/starting letter page.
	response = requests.get(term_link)
	return_status = response.status_code
	if return_status != 200:
		print(f"Request returned {return_status} status code for {term_link}")
		return []

	# Set up BeautifulSoup object.
	soup = BeautifulSoup(response.text, "lxml")

	# Isolate and return the article links.
	article_links  = soup.find_all(
		'a', 
		class_='dictionary-top300-list__list mntl-text-link'
	)
	article_links = [link["href"] for link in article_links]
	return article_links


def get_article(article_link: str, file_path: str) -> None:
	'''
	Download article (HTML) to file.
	@param: article_link (str), the URL of the article.
	@param: file_path (str), the path to the file.
	@preturn: returns nothing.
	'''
	# Query the article page.
	response = requests.get(article_link)
	return_status = response.status_code
	if return_status != 200:
		print(f"Request returned {return_status} status code for {article_link}")
		return
	
	# Output the article HTML content to file.
	with open(file_path, "w+") as f:
		f.write(response.text)


def main():
	'''
	Main method. Download the articles from investopedia organized by
		starting character/number.
	@param: takes no arguments.
	@return: returns nothing.
	'''
	###################################################################
	# PROGRAM ARGUMENTS
	###################################################################
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"--restart",
		action="store_true",
		help="Whether to restart the entire download from scratch. Default is false/not specified."
	)
	args = parser.parse_args()

	# Root dir for data.
	root_dir = "./data"
	os.makedirs(root_dir, exist_ok=True)

	# Map of all articles.
	article_map = dict()

	# Iterate through each category.
	for category_link in category_pages:
		# Extract directory name.
		match = re.search(category_pattern, category_link)
		if not match:
			# NOTE:
			# There are some good articles that are easy to scrape and
			# download that do not match the above pattern. We will 
			# consider these acceptable to not be captured upon the 
			# initial scan.

			# Skip if not found. 
			print(f"Was not able to isolate name for {category_link}")
			continue

		name = match.group(1)
		folder_path = os.path.join(
			root_dir,
			name
		)
		print(f"Processing articles in {name} category")

		# Check for directory. Create if it doesn't exist.
		if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
			os.makedirs(folder_path, exist_ok=True)

		# Identify all articles for each term.
		article_links = get_articles_from_term_page(
			base_url + category_link
		)

		# Move along if the number of article links returned is 0 (sign 
		# of bad HTTP request response).
		if len(article_links) == 0:
			continue

		# print(json.dumps(article_links, indent=4))

		# Download remaining articles.
		for article_link in tqdm(article_links):
			# Get article name.
			match = re.search(article_pattern, article_link)
			if not match:
				# Skip if not found.
				print(f"Was not able to isolate name for article {article_link}")
				continue

			name = match.group(1)
			file_path = os.path.join(
				folder_path,
				name + ".html"
			)
			# print(name)
			# print(file_path)

			# Update article map.
			article_map[name] = {
				"path": file_path,
				"link": article_link
			}

			# Get article if --restart OR article does not already exist.
			if args.restart or not os.path.exists(file_path):
				# Download article.
				get_article(article_link, file_path)

	# Save the article map.
	with open("article_map.json", "w+") as f:
		json.dump(article_map, f, indent=4)

	# Exit the program.
	exit(0)


if __name__ == '__main__':
	main()
# build_graph.py
# Take the initial articles data and expand upon it into a full fledged 
# graph, connecting to related terms and articles.
# Python 3.11
# Windows/MacOS/Linux


import argparse
import copy
import gc
import json
import os
from typing import Dict, List, Tuple

from bs4 import BeautifulSoup
from tqdm import tqdm

from download import get_article


def explore_related(
	article_map: Dict[str, Dict[str, str]], 
	# graph: Dict[str, List[Tuple[str, str]]], 
	article: str, 
	article_url: str, 
	is_term: bool = True,
	depth: int = 1, 
	restart: bool = False
) -> Tuple[Dict[str, Dict[str, str]], Dict[str, List[Tuple[str, str]]]]:
	'''
	Explore related terms and articles that are connected to the 
		current term/article.
	@param: article_map (Dict[str, Dict[str, str]]), the mapping for
		each article/entry and its associated local copy and url on 
		investopedia.
	@param: graph (Dict[str, List[Tuple[str, str]]]), the mapping for each 
		article/entry and its associated related terms and articles.
	@param: article (str), the target article of interest.
	@param: article_url (str), the URL associated with the article of
		interest.
	@param: depth (int), the level of depth that is to be explored in
		this graph. Default is 1.
	@param: restart (bool). whether to re-scrape the article of 
		interest and update its local copy with the new data.
	@return: returns a tuple containing two dictionaries serving as 
		submappings that will be used to update the reference 
		article_map and graphs respectively.
	'''
	# Return submaps.
	article_submap = dict()
	graph_submap = dict()

	# Folder path for related articles.
	related_articles_folder = f"./data/{'term' if is_term else 'article'}/"

	###################################################################
	# DOWNLOAD/LOAD ARTICLE
	###################################################################

	# Isolate whether the current article of interest is already 
	# scraped. Scrape the data if that is not the case OR if the 
	# restart flag is true.
	article_unseen = article not in list(article_map.keys())
	if restart or article_unseen:
		# Isolate the necessary path for the local copy of the 
		# article.
		if article_unseen:
			# Initialize the path since this article has not been seen
			# before and has to be downloaded.
			article_cleaned = article.replace("/", "-")
			article_path = os.path.join(
				related_articles_folder,
				article_cleaned + ".html"
			)

			# Update the article submap (and the main article map) for 
			# this entry.
			article_data = {
				"path": article_path,
				"link": article_url
			}
			article_submap[article] = article_data
			article_map[article] = article_data
		else:
			# Read the path from the article map.
			article_path = article_map[article]["path"]

		# Download the article.
		get_article(article_url, article_path)

	# Isolate the local copy of the article.
	# if article_unseen:
	# 	article_path = article_submap[article]["path"]
	# else:
	# 	article_path = article_map[article]["path"]
	article_path = article_map[article]["path"]

	# Skip this level if the local copy of the article is not 
	# available (it very much should be at this point or else someone
	# messed up the data pulled from download.py).
	if not os.path.exists(article_path):
		print(f"Error: Did not detect local file {article_path} for {article}")
		print("Please make sure download.py has been run to completion before running this script.")
		return article_submap, graph_submap
	
	###################################################################
	# PARSE ARTICLE FOR RELATED DATA
	###################################################################
		
	# Load local copy of the article and isolate all related terms and
	# articles to the article.
	with open(article_path, "r") as f:
		soup = BeautifulSoup(f.read(), "lxml")

	# List of outbound links for the current article (related terms and 
	# articles).
	outbound_links = list()

	# Isolate related articles.
	term_tags = soup.find_all(
		'a', 
		class_='related-terms__title mntl-text-link' 
	)
	outbound_links += [
		(tag.text, tag["href"], True)
		for tag in term_tags
	]

	# Isolate related terms.
	article_tags = soup.find_all(
		'a', 
		class_='comp mntl-card-list-items mntl-document-card mntl-card related-articles__link card' 
	)
	outbound_links += [
		(
			tag.find('span', class_='card__title-text').text, 
			tag["href"], 
			True
		)
		for tag in article_tags
	]

	# Update graph subgraph.
	if article in graph_submap:
		graph_submap[article] += [
			new_article[0] for new_article in outbound_links
		]
	else:
		graph_submap[article] = [
			new_article[0] for new_article in outbound_links
		]

	###################################################################
	# EXPLORE RELATED ARTICLES
	###################################################################

	# Continue exploring the links via recursive call if the depth is
	# non-zero.
	if depth > 0:
		# Iterate through all found outbound links.
		for outbound_link in outbound_links:
			# Unpack the outbound like.
			article_name, article_link, is_term = outbound_link

			# Implement the recursive call.
			article_sub_submap, graph_sub_submap = explore_related(
				article_map,
				# graph,
				article_name,
				article_link,
				is_term,
				depth - 1,
				restart
			)

			# Update the subgraphs.
			article_submap.update(article_sub_submap)
			for graph_node, graph_values in graph_sub_submap.items():
				if graph_node in graph_submap:
					graph_submap[graph_node] += graph_values
				else:
					graph_submap[graph_node] = graph_values

			# Memory cleanup.
			del article_name
			del article_link
			del article_sub_submap
			del graph_sub_submap
			gc.collect()
	
	###################################################################
	# AGGREGATE RELATED DATA
	###################################################################

	# Help reduce memory of graph.
	for key, value in graph_submap.items():
		graph_submap[key] = list(set(value))

	# Return the updated submaps.
	return article_submap, graph_submap


def main():
	'''
	Main method. Download articles related to the ones already pulled
		with download.py.
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
	parser.add_argument(
		"--max_depth",
		type=int,
		default=1,
		help="How deep should the graph traversal go across links. Default is 1/not specified."
	)
	args = parser.parse_args()

	# Unpack the arguments.
	restart = args.restart
	depth = args.max_depth

	###################################################################
	# CHECK PATH VARIABLES AND FILES
	###################################################################

	# Path variables.
	data_folder = "./graph"
	article_json = os.path.join(
		data_folder,
		"article_map.json"
	)

	# Check for path to graph folder. Make it if it doesn't exist.
	if not os.path.exists(data_folder) or not os.path.isdir(data_folder):
		os.makedirs(data_folder, exist_ok=True)

	# Check for article map JSON.
	if not os.path.exists(article_json):
		print(f"Error: Could not detect required file {article_json}")
		print("Please be sure to run download.py before running this script.")
		exit(1)

	# Load articles.
	with open(article_json, "r") as f:
		article_map = json.load(f)

	# Initialize necessary folder paths if they don't already exist.
	term_folder = "./data/term/"
	article_folder = "./data/article/"
	if not os.path.exists(term_folder):
		os.makedirs(term_folder, exist_ok=True)
	if not os.path.exists(article_folder):
		os.makedirs(article_folder, exist_ok=True)

	###################################################################
	# EXPLORE RELATED ARTICLES
	###################################################################

	# Clone article map. This will contain the expanded map information
	# for articles (link and path). Initialize a graph to keep track of 
	# which articles link together.
	expanded_map = copy.deepcopy(article_map)
	graph = {article: list() for article in article_map}

	# Iterate through each article and recrusively explore its related
	# links to other terms and articles.
	for article in tqdm(list(article_map.keys())):
		# Compute all visited links. Current placement in the code is
		# not ideal.
		# visited_links = [
		# 	expanded_map[key]["link"] for key in expanded_map
		# ]

		# Verify the local file exists.
		article_path = article_map[article]["path"]
		article_link = article_map[article]["link"]
		if not os.path.exists(article_path):
			print(f"Could not find path {article_path}")
			print(f"Skipping {article}")
			continue

		# Build out the graph by exploring the related terms and 
		# articles.
		article_submap, graph_submap = explore_related(
			expanded_map, 
			# graph, 
			article, 
			article_link,
			True, # is_term is true for all values in article_map.
			depth, 
			restart
		)

		# Update the graphs.
		expanded_map.update(article_submap)
		for graph_node, graph_value in graph_submap.items():
			if graph_node in graph:
				graph[graph_node] += graph_value
			else:
				graph[graph_node] = graph_value
		
		# Memory cleanup.
		del article_path
		del article_link
		del article_submap
		del graph_submap
		gc.collect()

	###################################################################
	# AGGREGATE AND SAVE RELATED DATA
	###################################################################
	
	# Help reduce memory of graph.
	for key, value in graph.items():
		graph[key] = list(set(value))

	# Save the graphs.
	expanded_json = os.path.join(
		data_folder,
		f"expanded_article_map_depth{depth}.json"
	)
	graph_json= os.path.join(
		data_folder,
		f"term_article_graph_depth{depth}.json"
	)
	with open(expanded_json, "w+") as f:
		json.dump(expanded_map, f, indent=4)
	with open(graph_json, "w+") as f:
		json.dump(graph, f, indent=4)

	# Exit the program.
	exit(0)


if __name__ == '__main__':
	main()
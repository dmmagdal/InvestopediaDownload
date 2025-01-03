# Investopedia Download

Description: Download key terms defined in Investopedia as well as any related articles.


### Setup

 - Conda
 - Python Virtualenv


### Run Downloaders

 - Initial download script
 - Build graph script
 - Download from huggingface


### Notes

 - Calling `download.py`
     - 6,243 (as of 12/31/24) total number of documents.
     - Completed in hours.
 - Calling `build_graph.py`
     - The graph method of exhaustively searching (BFS) is the most efficient.
     - Still is *very* slow compared to the more direct download method in `download.py` but that is due to the information for `download.py` being in a relatively central place (rather than having to explore to discover it).
     - TODO: Go back and allow this program to build off of existing graphs from previous (smaller) runs.
     - Setting `max_depth` 2
         - 9,844 total number of documents (~3.7GB).
         - Completed in 26 hours.


### Investopedia References

 - [About us](https://www.investopedia.com/about-us-5093223)
 - [Robots.txt](https://www.investopedia.com/robots.txt)
 - [Financial research data hub](https://www.investopedia.com/financial-research-data-hub-5192040)
 - [Financial term dictionary](https://www.investopedia.com/financial-term-dictionary-4769738)
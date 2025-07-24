#
# Copyright 2025 Lukasz Jablonski <lukasz.jablonski@wp.eu>
#
# This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>
#
"""
Access NIH BioArt Source.
"""

import re
import requests

import os,sys
import zipfile # Still useful if some files are actually zips
import io # To work with in-memory files

# Assuming import_sources.py is in the same directory or accessible
from import_sources import RemoteSource

SVG_FILE_ID_REX = re.compile(r"SVG:([^|]+)")
TN_FILE_ID_REX = re.compile(r"JPG:([^|]+)") # Regex for JPG thumbnails

err_file = "C:\\Users\\lukaszjablonski\\bioart_debug.log"

# These class-level prints might run multiple times depending on how Inkscape loads extensions
with open(err_file, 'a') as f:
    print('hello world', file=f)
with open(err_file, 'a') as f:
    print('hello world 2', file=f)

class BioArt(RemoteSource):
    name = "NIH BioArt Source"
    icon = "sources/bioart.svg"
    
    # Class-level prints that indicate the class definition is being processed
    with open(err_file, 'a') as f:
        print(f'[{os.getpid()}] Class BioArt definition loaded: hello world', file=f)
    with open(err_file, 'a') as f:
        print(f'[{os.getpid()}] Class BioArt definition loaded: hello world 2', file=f)

    def __init__(self, cache_dir):
        super().__init__(cache_dir) 
        self.session = requests.Session()
        self.base_url = "https://bioart.niaid.nih.gov/api/search/"
        self.entry_url_base = "https://bioart.niaid.nih.gov/api/bioarts/"
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        self.cache_dir = cache_dir # Ensure cache_dir is stored
        os.makedirs(self.cache_dir, exist_ok=True) # Ensure cache directory exists
        with open(err_file, 'a') as f:
            print(f'[{os.getpid()}] BioArt __init__ called. Cache dir: {cache_dir}', file=f)

    def search_json(self, query_term):
        """Helper to perform the initial search API call."""
        with open(err_file, 'a') as f:
            print(f'[{os.getpid()}] In search_json for query: {query_term}', file=f)
        self.search_url = f"{self.base_url}type:bioart AND {query_term}/"
        response = self.session.get(self.search_url, headers=self.headers)
        response.raise_for_status()
        json_data = response.json()
        with open(err_file, 'a') as f:
            print(f'[{os.getpid()}] search_json got response (truncated): {str(json_data)[:200]}...', file=f)
        return json_data

    def get_entry_details(self, entry_id):
        """Helper to get detailed information for a specific entry."""
        with open(err_file, 'a') as f:
            print(f'[{os.getpid()}] In get_entry_details for ID: {entry_id}', file=f)
        details_url = f"{self.entry_url_base}{entry_id}"
        response = self.session.get(details_url, headers=self.headers)
        response.raise_for_status()
        json_data = response.json()
        with open(err_file, 'a') as f:
            print(f'[{os.getpid()}] get_entry_details got response (truncated): {str(json_data)[:200]}...', file=f)
        return json_data

    def _download_and_save_image(self, entry_id, file_id, extension):
        """
        Downloads the image file from the BioArt API (which sends as attachment)
        and saves it to a local cache, returning its local path.
        """
        # Correct URL construction: using entry_id and the specific file_id
        # This URL is confirmed by the user to serve the direct file,
        # but with a Content-Disposition that causes download in browsers.
        remote_url = f"https://bioart.niaid.nih.gov/api/bioarts/{entry_id}/zip?file-ids={file_id}"
        
        # Define a local path within your cache_dir
        local_filename = f"{entry_id}_{file_id}{extension}"
        local_file_path = os.path.join(self.cache_dir, local_filename)

        # Check if file already exists in cache (for efficiency)
        if os.path.exists(local_file_path):
            with open(err_file, 'a') as f:
                print(f'[{os.getpid()}] Using cached file: {local_file_path}', file=f)
            return local_file_path

        with open(err_file, 'a') as f:
            print(f'[{os.getpid()}] Attempting to download file from: {remote_url}', file=f)
            
        try:
            response = self.session.get(remote_url, headers=self.headers, stream=True)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            # Write content to local file
            with open(local_file_path, 'wb') as f_local:
                for chunk in response.iter_content(chunk_size=8192): # Read in 8KB chunks
                    f_local.write(chunk)
            
            with open(err_file, 'a') as f:
                print(f'[{os.getpid()}] Downloaded and saved to: {local_file_path}', file=f)
            return local_file_path

        except requests.exceptions.RequestException as e:
            with open(err_file, 'a') as f:
                print(f'[{os.getpid()}] ERROR downloading file from {remote_url}: {e}', file=f)
            return None # Indicate failure
        except Exception as e:
            with open(err_file, 'a') as f:
                print(f'[{os.getpid()}] UNEXPECTED ERROR saving file {local_file_path}: {e}', file=f)
            return None

    def search(self, query):
        with open(err_file, 'a') as f:
            print(f'[{os.getpid()}] --- search method START for query: "{query}" ---', file=f)
        
        try:
            # Calling the helper method on self
            results = self.search_json(query) 
            with open(err_file, 'a') as f:
                print(f'[{os.getpid()}] Initial search_json call successful.', file=f)
        except requests.exceptions.RequestException as e:
            with open(err_file, 'a') as f:
                print(f'[{os.getpid()}] ERROR: Initial search_json request failed: {e}', file=f)
            return
        except Exception as e: # Catch any other unexpected errors during initial search
            with open(err_file, 'a') as f:
                print(f'[{os.getpid()}] UNEXPECTED ERROR during initial search: {e}', file=f)
            return

        if "hits" not in results or results["hits"]["found"] == 0:
            with open(err_file, 'a') as f:
                print(f'[{os.getpid()}] No hits found for query: "{query}"', file=f)
            return

        with open(err_file, 'a') as f:
            print(f'[{os.getpid()}] Total hits found: {results["hits"]["found"]}. Processing entries...', file=f)

        for i, entry in enumerate(results["hits"]["hit"]):
            with open(err_file, 'a') as f:
                print(f'[{os.getpid()}] Processing entry {i+1}/{results["hits"]["found"]}', file=f)
            entry_id = entry["fields"]["id"][0]
            
            try:
                # Calling the helper method on self
                detailed_info = self.get_entry_details(entry_id) 
                with open(err_file, 'a') as f:
                    print(f'[{os.getpid()}] Successfully got detailed info for entry ID: {entry_id}', file=f)
            except requests.exceptions.RequestException as e:
                with open(err_file, 'a') as f:
                    print(f'[{os.getpid()}] ERROR: Failed to get details for entry ID {entry_id}: {e}', file=f)
                continue 
            except Exception as e:
                with open(err_file, 'a') as f:
                    print(f'[{os.getpid()}] UNEXPECTED ERROR getting details for ID {entry_id}: {e}', file=f)
                continue
            
            popularity = detailed_info.get("downloadCount", 0)

            # Safely get filesinfo, default to empty string if not found
            files_info_str = entry["fields"].get("filesinfo", [""])[0] 
            
            svg_file_id = None # Store the actual ID needed for SVG download
            tn_file_id = None  # Store the actual ID needed for TN download
            
            matchSVG = SVG_FILE_ID_REX.search(files_info_str)
            matchTN = TN_FILE_ID_REX.search(files_info_str)
            
            with open(err_file, 'a') as f:
                print(f'[{os.getpid()}] Processed files_info_str: {files_info_str}. SVG match: {bool(matchSVG)}, TN match: {bool(matchTN)}', file=f)
            
            # --- Handle SVG files ---
            if matchSVG:
                svg_ids_str = matchSVG.group(1)
                svg_ids_to_find = [int(id_str) for id_str in svg_ids_str.split(',') if id_str.isdigit()]
                
                with open(err_file, 'a') as f:
                    print(f'[{os.getpid()}] Found SVG IDs in filesinfo: {svg_ids_to_find}', file=f)
                
                file_groups = detailed_info.get("fileGroups", [])
                
                found_at_least_one_svg = False 

                for group_idx, group in enumerate(file_groups):
                    for file_detail_idx, file_details in enumerate(group.get("files", [])):
                        with open(err_file, 'a') as f:
                            print(f'[{os.getpid()}] file_details: {file_details}', file=f)
                        current_file_id = file_details.get("fileId")
                        if current_file_id in svg_ids_to_find:
                            with open(err_file, 'a') as f:
                                print(f'[{os.getpid()}] Matching SVG fileId found in details: {current_file_id}', file=f)
                            
                            svg_file_id = current_file_id # Store the specific SVG file ID for download
                            
                            # --- Handle Thumbnail (JPG) for this specific SVG entry ---
                            if matchTN:
                                tn_ids_str = matchTN.group(1)
                                tn_ids_to_find = [int(id_str) for id_str in tn_ids_str.split(',') if id_str.isdigit()]
                                
                                with open(err_file, 'a') as f:
                                    print(f'[{os.getpid()}] Searching for TN IDs: {tn_ids_to_find}', file=f)
                                
                                for tn_group_idx, tn_group in enumerate(file_groups):
                                    for tn_file_details in tn_group.get("files", []):
                                        current_tn_file_id = tn_file_details.get("fileId")
                                        if current_tn_file_id in tn_ids_to_find:
                                            tn_file_id = current_tn_file_id # Store the specific TN file ID for download
                                            with open(err_file, 'a') as f:
                                                print(f'[{os.getpid()}] Found TN file ID: {tn_file_id}', file=f)
                                            break 
                                    if tn_file_id: # If thumbnail ID was found
                                        break

                            # --- Download and save files locally, then yield with local paths ---
                            local_svg_path = None
                            local_tn_path = None

                            if svg_file_id: # Only download if we have a valid SVG file ID
                                local_svg_path = self._download_and_save_image(entry_id, svg_file_id, '.svg')
                            
                            if tn_file_id: # Only download if we have a valid TN file ID
                                local_tn_path = self._download_and_save_image(entry_id, tn_file_id, '.jpg') # Assuming TN is JPG

                            # Fallback for thumbnail if local TN not obtained or original thumbnail field from API
                            final_thumbnail_path = local_tn_path if local_tn_path else entry["fields"].get("thumbnail", [""])[0]

                            if local_svg_path: # ONLY YIELD IF WE SUCCESSFULLY DOWNLOADED THE MAIN SVG FILE
                                with open(err_file, 'a') as f:
                                    print(f'[{os.getpid()}] >>> YIELDING item for entry ID {entry_id}, SVG ID {svg_file_id} with LOCAL paths {local_svg_path}.', file=f)

                                yield {
                                    "id": entry_id,
                                    "name": entry["fields"]["title"][0],
                                    "author": entry["fields"]["creator"][0],
                                    "summary": entry["fields"].get("description", [""])[0],# if entry["fields"].get("description") else None,
                                    "created": entry["fields"].get("created", [""])[0],# if entry["fields"].get("created") else None,
                                    "popularity": popularity,
                                    "thumbnail": local_svg_path,#final_thumbnail_path, # Provide local path or fallback
                                    "file": local_svg_path,     # Provide local path for the main file
                                    "license": "cc-0",#entry["fields"]["license"][0],
                                }
                                found_at_least_one_svg = True
                            else:
                                with open(err_file, 'a') as f:
                                    print(f'[{os.getpid()}] SKIPPING yield for {entry_id} because SVG download failed or no SVG ID found.', file=f)

            if not found_at_least_one_svg:
                with open(err_file, 'a') as f:
                    print(f'[{os.getpid()}] No matching SVG was successfully processed and yielded for entry {entry_id}.', file=f)
            else:
                with open(err_file, 'a') as f:
                    print(f'[{os.getpid()}] Finished processing entry {entry_id}.', file=f)

        with open(err_file, 'a') as f:
            print(f'[{os.getpid()}] --- search method END for query: "{query}" ---', file=f)
from urllib.parse import urlparse, urlunparse, parse_qs
import os
import logging as log


def normalizeUrl(url) -> str:
    # parse for domain, and handle per domain
    url_parts = urlparse(url)

    if url_parts.hostname in ["youtube.com", "youtu.be", "www.youtube.com"]:
        return normalizeYT(url_parts)

    return urlunparse(url_parts)

def normalizeLocal(url) -> str:
    local_path = "/mnt/d/homeword/"
    local_url = local_path + url
    log.debug(f"local_url: {local_url}")
    # Generates a directory listing of the local path
    log.debug(f"Normalize:Local: Generating directory tree of {local_path}")

    local_path_tree = []
    with open("./cache/rootmap.txt", 'w') as file:
        for root, dirs, files in os.walk(local_path):
            for name in files:
                file.write(os.path.join(root, name) + "\n")
                local_path_tree.append(os.path.join(root, name))
    log.debug(f"Normalizer:Local:Tree: Generated")
    # Checks if the url_parts.path is in the directory listing
    if local_url in local_path_tree:
        # If it is, it returns the fill path
        return local_url
    else:
        return 404

def normalizeYT(url_parts) -> str:
    # remove the list query param as it causes excess delay in loading information
    url_query = parse_qs(url_parts.query)
    new_query = ""
    if "v" in url_query:
        new_query = f"v={url_query['v'][0]}"
    url_parts = url_parts._replace(query=new_query)
    return urlunparse(url_parts)


def normalizeVimeo(url_parts) -> str:
    return urlunparse(url_parts)


def normalizeTwitch(url_parts) -> str:
    return urlunparse(url_parts)

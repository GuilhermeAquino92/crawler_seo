import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque
from tqdm import tqdm

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def is_internal_link(base_url, link):
    parsed_base = urlparse(base_url)
    parsed_link = urlparse(link)
    return parsed_link.netloc == '' or parsed_link.netloc == parsed_base.netloc

def get_links(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    for tag in soup.find_all('a', href=True):
        href = tag.get('href')
        full_url = urljoin(base_url, href)
        if is_internal_link(base_url, full_url):
            links.add(full_url.split('#')[0])  # Remove anchors
    return links

def fetch_url(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=3)
        content_type = response.headers.get('Content-Type', '')
        status = response.status_code
        html = response.text if 'text/html' in content_type else ''
        return {'url': url, 'status': status, 'content_type': content_type, 'html': html}
    except requests.RequestException as e:
        return {'url': url, 'status': None, 'content_type': f'Erro: {str(e)}', 'html': ''}

def crawl(base_url, max_urls=1000, max_workers=10):
    visited = set()
    queue = deque([base_url])
    resultados = []

    pbar = tqdm(total=max_urls, desc='🚀 Crawleando')
    executor = ThreadPoolExecutor(max_workers=max_workers)

    while queue and len(visited) < max_urls:
        futures = []
        urls_this_batch = []

        while queue and len(futures) < max_workers:
            url = queue.popleft()
            if url not in visited:
                futures.append(executor.submit(fetch_url, url))
                urls_this_batch.append(url)
                visited.add(url)

        for future in as_completed(futures):
            result = future.result()
            resultados.append({
                'url': result['url'],
                'status': result['status'],
                'content_type': result['content_type']
            })

            if result['status'] == 200 and 'text/html' in result['content_type']:
                links = get_links(result['html'], result['url'])
                for link in links:
                    if link not in visited and len(visited) + len(queue) < max_urls:
                        queue.append(link)

            pbar.update(1)

    pbar.close()
    executor.shutdown()
    return resultados

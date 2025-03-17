import requests
from bs4 import BeautifulSoup
from shrub_scraper.events.model import Event
from typing import List


def __url_join(url, prefix_url):
    if url is not None:
        return url if url.startswith('http') else requests.compat.urljoin(prefix_url, url)
    else:
        return "No url"


def scrape_knvi_architecture_events() -> List[Event]:
    result = []
    # URL to scrape
    url = 'https://www.knvi.nl/agenda'

    urls = set([url])
    add_paginator_pages = True
    while len(urls) > 0:
        # Send a GET request to the URL
        items_url = urls.pop()
        response = requests.get(items_url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the page content using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the event container (you need to inspect the page to find the correct tags)
            events = soup.find_all('li', class_='mmt-ml-meeting')  # Example class name, adjust based on actual structure
            for event in events:
                # Extract event title, date, and description (adjust based on the actual structure)
                title = event.find('h3').text.strip() if event.find('h3') else 'No title'
                date_el =  event.find('span', class_="mmt-ml-date")
                if date_el is not None:
                    date_day = date_el.text.strip()
                else:
                    date_day = "No date"

                description = event.find('p').text.strip() if event.find('p') else 'No description'
                info_url = __url_join(event.find("a").attrs['href'], items_url)
                result.append(Event(source=items_url, title=title, date=f"{date_day}", decription=description, url=info_url))
            if add_paginator_pages:
                add_paginator_pages = False
                page_container = soup.find('div', class_='pbuic-pager-container')  # Example class name, adjust based on actual structure
                pages = page_container.find_all("li")
                for page in pages:
                    page_url = page.find("a").attrs['href'] if page.find("a") else None
                    if page_url is not None:
                        urls.add(page_url if page_url.startswith('http') else requests.compat.urljoin(response.url, page_url))
            print(f"Retrieved events from {items_url}")
        else:
            print(f"Failed to retrieve the page {url}. Status code: {response.status_code}")

    return result


def scrape_danw_architecture_events() -> List[Event]:
    result = []
    # URL to scrape
    url = 'https://www.danw.nl/events'

    urls = set([url])
    while len(urls) > 0:
        # Send a GET request to the URL
        items_url = urls.pop()
        response = requests.get(items_url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the page content using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the event container
            event_table = soup.find('table', class_='table act')
            if event_table is not None:
                events = event_table.find_all('tr')
                for event in events:
                    description = None
                    if 'class' in event.attrs and 'act-year' in event.attrs['class']:
                        year = event.find_all('th')[1].text.strip()
                    day_el = event.find('td', class_='act-date')
                    if day_el is not None:
                        day = day_el.text.strip()
                        month = event.find('span', class_='act-month').text.strip()
                        act_el = event.find('td', class_='act-name')
                        if act_el is not None:
                            info_url = __url_join(act_el.find("a").attrs['href'], items_url)
                            title = act_el.find("a").text.strip() if act_el.find("a") else "No title"
                            type_ = act_el.find("span").text.strip() if act_el.find("span") else "No type"
                        else:
                            info_url = "No url"
                            title = "No title"
                            type_ = "No type"
                        result.append(Event(source=url, title=title, date=f"{year} {month} {day}", decription=description, url=info_url, type_=type_))
            print(f"Retrieved events from {items_url}")
        else:
            print(f"Failed to retrieve the page {url}. Status code: {response.status_code}")

    return result


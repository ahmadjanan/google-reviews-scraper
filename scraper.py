import logging
import time

import pandas as pd
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver


class GoogleReviewsScraper:

    def __init__(self, start_url, xpaths, selectors, out_file=None):
        self.driver = webdriver.Chrome()
        self.start_url = start_url
        self.xpaths = xpaths
        self.selectors = selectors
        self.out_file = out_file

    def click_button_js(self, button):
        self.driver.execute_script('arguments[0].click()', button)

    def navigate_to_reviews_tab(self):
        review_tab_button = self.driver.find_element("xpath", self.xpaths['reviews_tab'])
        self.click_button_js(review_tab_button)

    def extract_hotels_name_from_html(self):
        response = BeautifulSoup(self.driver.page_source, 'html.parser')
        hotel_names = response.find_all('h2', {'class': 'BgYkof ogfYpf ykx2he'})[:5]
        hotel_names = [hotel_name.get_text() for hotel_name in hotel_names]

        return hotel_names

    def extract_reviews_from_html(self, hotel_name):
        response = BeautifulSoup(self.driver.page_source, 'html.parser')
        review_cards = response.find_all('div', {'class': 'Svr5cf bKhjM'})
        reviews = []
        for review_card in review_cards:
            name = review_card.select(self.selectors['name'])[0].get_text()
            rating = review_card.select(self.selectors['rating'])[0].get_text()
            review = (review_card.select(self.selectors['long_review']) or
                      review_card.select(self.selectors['short_review']))[0].get_text()

            reviews.append({
                'hotel_name': hotel_name,
                'name': name,
                'rating': rating,
                'review': review,
            })

        return reviews

    def extract_hotels_data(self):
        self.driver.get(self.start_url)
        self.driver.find_element("xpath", self.xpaths['view_all_hotels']).click()

        hotels = self.driver.find_elements("xpath", self.xpaths['search_results'])[:5]
        hotel_names = self.extract_hotels_name_from_html()

        hotels_data = []
        for hotel_name, hotel in zip(hotel_names, hotels):
            self.click_button_js(hotel)
            prev_tab = self.driver.current_window_handle
            next_tab = self.driver.window_handles[1]
            self.driver.switch_to.window(next_tab)
            self.navigate_to_reviews_tab()
            time.sleep(0.5)
            hotel_data = self.extract_reviews_from_html(hotel_name)
            hotels_data += hotel_data
            self.driver.close()
            self.driver.switch_to.window(prev_tab)

        return hotels_data


def export_to_csv(data):
    df = pd.DataFrame(data)
    df.to_csv('out_file.csv')


def main():
    start_url = 'https://www.google.com/search?q=best+hotels+pakistan'
    xpaths = {
        'view_all_hotels': '//span[@class="wUrVib OSrXXb"]',
        'search_results': '//a[@class="PVOOXe"]',
        'reviews_tab': '//*[@id="reviews"]/span',
        'see_more_buttons': '//div[@class="TJUuge"]'
    }
    selectors = {
        'name': 'span.k5TI0 a',
        'rating': 'div.GDWaad',
        'long_review': 'div.OlkcBc.eLNT1d span',
        'short_review': 'div.STQFb.eoY5cb span',
    }

    scraper = GoogleReviewsScraper(start_url, xpaths, selectors)
    hotels_data = scraper.extract_hotels_data()
    export_to_csv(hotels_data)
    scraper.driver.close()


if __name__ == '__main__':
    main()

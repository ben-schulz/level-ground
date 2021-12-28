import os
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select


class TaxBillPage:
    def __init__(self, name=None, number=None, url=None, year=None):
        self.name = name
        self.number = number
        self.url = url
        self.year = year

    def __repr__(self):
        return f"TaxBillPage(name={self.name}, number={self.number}, url={self.url})"

    def filename(self):
        fslash = "_fslash_"
        return f"{self.name.replace(' ', '_').replace('/', fslash)}--{self.number}--{self.year}.html"


def search_tax_bills(
    last_name_search_str, bill_type="Real Estate", dump_directory="./tax_bill_dump"
):

    initial_url = (
        "https://www.showmeboone.com/collector/disclaimer.asp?SEARCH=BillSearch"
    )

    driver = webdriver.Firefox()

    try:
        driver.get(initial_url)

        # click through the "agree to terms" page
        main_el = driver.find_element(by="css selector", value=".middle-content")
        entry_el = main_el.find_element(by="tag name", value="input")
        entry_el.click()

        # ensure the form is clear
        reset_button_el = driver.find_element(
            by="css selector", value='button[name="btn_reset"]'
        )
        reset_button_el.click()

        bill_type_el = driver.find_element(by="id", value="MailNameBillType")

        bill_type_selector = Select(bill_type_el)

        bill_type_selector.select_by_visible_text(bill_type)

        last_name_input_el = driver.find_element(by="id", value="mail-lastname")

        last_name_input_el.send_keys(last_name_search_str)

        search_button = driver.find_element(by="name", value="btn_search")

        search_button.click()

        result_page_el = driver.find_element(by="css selector", value=".pagination")

        page_count = int(result_page_el.text.strip().split(" ")[-1].replace(",", ""))

        bill_pages = list()
        page_num = 0
        while page_num < page_count:
            result_table_el = driver.find_element(
                by="css selector", value=".billsearch"
            )
            result_rows = result_table_el.find_elements(
                by="css selector", value="tr.odd, tr.even"
            )

            for row_el in result_rows:
                bill_link_el = row_el.find_element(by="tag name", value="a")
                bill_url = bill_link_el.get_attribute("href")

                bill_name = bill_link_el.text

                bill_number_el = row_el.find_element(
                    by="css selector", value='td[data-th="Bill Number"]'
                )
                bill_number = bill_number_el.text

                bill_year_el = row_el.find_element(
                    by="css selector", value='td[data-th="Bill Year"]'
                )
                bill_year = bill_year_el.text

                bill_pages.append(
                    TaxBillPage(
                        name=bill_name, number=bill_number, url=bill_url, year=bill_year
                    )
                )

            next_page_container_el = driver.find_element(
                by="css selector", value=".pagination"
            )
            next_page_el = next_page_container_el.find_element(
                by="css selector", value='ul li a[data-pagetype="btn_next"]'
            )
            next_page_el.click()
            page_num += 1

        if not os.path.exists(dump_directory):
            os.mkdir(dump_directory)

        record_count = 0
        for p in bill_pages:

            driver.get(p.url)

            bill_text = driver.find_element(by="id", value="content").text

            dest_path = os.path.join(dump_directory, p.filename())
            with open(dest_path, "w+") as f:
                f.write(bill_text)
            record_count += 1

    finally:
        driver.close()

    return record_count


search_strs = [str(x) for x in range(0, 10)] + [
    chr(x) for x in range(ord("a"), ord("z") + 1)
]

max_retries = 5

for search_str in search_strs:
    print(f"processing search '{search_str}'")
    attempts = 0
    delay = 1.0
    while attempts < max_retries:
        attempts += 1
        delay *= 2
        try:
            record_count = search_tax_bills(search_str)
            print(f"retrieved {record_count} records.")
            break
        except Exception as e:
            if attempts >= max_retries:
                raise
            print(e)
            print("retrying...")
            time.sleep(delay)

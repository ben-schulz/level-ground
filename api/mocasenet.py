import os
import time
import datetime
import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions

fixed_wait_seconds = 1.2
ceil_wait_seconds = 30.0


def is_eviction_proceeding_type(text):
    _text = text.lower()

    return "rent and possession" in _text or "unlawful detainer" in _text


def search_filings_week_of(date, case_type="Civil"):
    """
    search filings for a seven day period starting at this date,
    and return a list of case numbers, which can be used
    to directly retrieve the individual case files
    """

    fmt_str = "02"
    initial_url = f"https://www.courts.mo.gov/cnet/searchResult.do?countyCode=BNE&newSearch=Y&courtCode=CT13&startDate={format(date.month, fmt_str)}%2F{format(date.day, fmt_str)}%2F{format(date.year, fmt_str)}&caseStatus=A&caseType=Civil&locationCode="
    #    initial_url = "https://www.courts.mo.gov/cnet/filingDateSearch.do"

    driver = webdriver.Firefox()

    try:

        driver.get(initial_url)

        wait = WebDriverWait(driver, ceil_wait_seconds)
        # wait for the 'processing' banner to leave
        wait.until(
            expected_conditions.invisibility_of_element_located(
                (By.ID, "searchResult_processing")
            )
        )

        # the results appear to load asynchronously,
        # and so a wait is necessary to ensure the result rows are present
        wait.until(
            expected_conditions.presence_of_all_elements_located(
                (By.CSS_SELECTOR, ".odd, .even")
            )
        )
        result_table_el = driver.find_element(by="id", value="searchResult")

        time.sleep(fixed_wait_seconds)

        # the text here is, exactly: "Showing I to J of N entries"
        # where I, J, and N match the regex: [0-9,]+
        search_pos_el = driver.find_element(by="id", value="searchResult_info")
        pos_tokens = search_pos_el.text.split(" ")
        page_min_index = int(pos_tokens[1].replace(",", ""))
        page_max_index = int(pos_tokens[3].replace(",", ""))
        search_max_index = int(pos_tokens[5].replace(",", ""))

        prev_page_max_index = page_max_index

        results = list()

        if 0 == page_max_index:
            return results

        # the results appear to load asynchronously,
        # and so a wait is necessary to ensure the result rows are present
        wait = WebDriverWait(driver, 30)
        wait.until(
            expected_conditions.presence_of_element_located((By.ID, "searchResult"))
        )
        result_table_el = driver.find_element(by="id", value="searchResult")

        # for reasons unclear,
        # this seems to only work with a fixed delay
        time.sleep(fixed_wait_seconds)
        result_row_els = result_table_el.find_elements(
            by="css selector", value=".odd, .even"
        )

        more_pages = 0 < page_min_index
        while more_pages:

            next_button_el = driver.find_element(by="id", value="searchResult_next")
            more_pages = "disabled" not in next_button_el.get_attribute("class").split(
                " "
            )

            # the results appear to load asynchronously,
            # and so a wait is necessary to ensure the result rows are present
            wait.until(
                expected_conditions.presence_of_element_located((By.ID, "searchResult"))
            )
            result_table_el = driver.find_element(by="id", value="searchResult")

            # for reasons unclear,
            # this seems to only work with a fixed delay
            time.sleep(fixed_wait_seconds)
            result_row_els = result_table_el.find_elements(
                by="css selector", value=".odd, .even"
            )

            for row_el in result_row_els:
                cell_els = row_el.find_elements(by="tag name", value="td")
                case_number_cell = cell_els[2]
                case_type_cell = cell_els[4]

                if is_eviction_proceeding_type(case_type_cell.text):
                    results.append(case_number_cell.text)

            next_button_el = driver.find_element(by="id", value="searchResult_next")

            wait.until(
                expected_conditions.element_to_be_clickable(
                    (By.ID, "searchResult_next")
                )
            )
            next_button_el.click()

            time.sleep(fixed_wait_seconds)

            prev_page_max_index = page_max_index

            # the text here is, exactly: "Showing I to J of N entries"
            # where I, J, and N match the regex: [0-9,]+
            search_pos_el = driver.find_element(by="id", value="searchResult_info")
            pos_tokens = search_pos_el.text.split(" ")
            page_min_index = int(pos_tokens[1].replace(",", ""))
            page_max_index = int(pos_tokens[3].replace(",", ""))
            search_max_index = int(pos_tokens[5].replace(",", ""))

            if more_pages:
                assert (
                    page_min_index == prev_page_max_index + 1
                ), f"an error caused records between {page_min_index} and {prev_page_max_index} to be skipped"

    finally:
        driver.close()

    return results


def case_numbers_by_date(start_date, end_date, max_attempts=15, outfile="case_numbers.json"):

    results = list()
    search_date = start_date
    while search_date < end_date:
        print(f"searching week of {search_date.strftime('%Y/%m/%d')}")
        attempts = 0
        delay = 1.0
        while attempts < max_attempts:
            attempts += 1
            try:
                next_result = search_filings_week_of(search_date)
                results += next_result
                print(f"found {len(next_result)} records")
                break
            except Exception as e:
                if attempts >= max_attempts:
                    raise
                else:
                    print(e)
                    print("retrying...")
                    delay *= 2.0
                    time.sleep(delay)
        search_date = search_date + datetime.timedelta(days=7)

    with open(outfile, "w+") as f:
        json.dump(results, f)

    print(f"wrote {len(results)} records.")


class Roles:
    Plaintiff = "plaintiff"
    Defendant = "defendant"
    PlaintiffAttorney = "plaintiff_attorney"
    DefendantAttorney = "defendant_attorney"
    OtherAttorney = "other_attorney"
    Garnishee = "garnishee"
    Assignee = "assignee"
    Other = "other"


roles = [
    Roles.Plaintiff,
    Roles.Defendant,
    Roles.PlaintiffAttorney,
    Roles.DefendantAttorney,
    Roles.OtherAttorney,
    Roles.Garnishee,
    Roles.Assignee,
    Roles.Other,
]


def to_fieldname(x):
    return x.strip().lower().replace(" ", "_").replace("/", "_or_").strip(":")


def clean_text(x):
    return x.strip(" \t\n\r")


def get_role(party_str):

    lower_str = party_str.lower()

    if "attorney" in lower_str:
        if "plaintiff" in lower_str:
            return Roles.PlaintiffAttorney
        elif "defendant" in lower_str:
            return Roles.DefendantAttorney
        else:
            return Roles.OtherAttorney
    elif "plaintiff" in lower_str:
        return Roles.Plaintiff
    elif "defendant" in lower_str:
        return Roles.Defendant
    elif "garnishee" in lower_str:
        return Roles.Garnishee
    elif "assignee" in lower_str:
        return Roles.Assignee
    else:
        return Roles.Other



def case_by_number(case_number, courtId="CT13"):

    fixed_delay = 0.2

    try:

        initial_url = f"https://www.courts.mo.gov/casenet/cases/header.do?inputVO.caseNumber={case_number}&inputVO.courtId={courtId}"

        driver = webdriver.Firefox()

        driver.get(initial_url)

        #
        # header tab
        #
        table_el = driver.find_element(by="css selector", value=".detailRecordTable")

        row_els = table_el.find_elements(by="css selector", value="tr")

        now = datetime.datetime.now()
        result = {"case_number": case_number, "retrieved": now.strftime("%m/%d/%Y")}

        fields = [
            to_fieldname(el.text)
            for el in table_el.find_elements(by="css selector", value="td.detailLabels")
            if to_fieldname(el.text) != ""
        ]
        field_values = [
            el.text
            for el in table_el.find_elements(
                by="css selector", value="td.detailLabels + td.detailData"
            )
            if el.text.strip() != ""
        ]

        result.update(dict(zip(fields, field_values)))

        time.sleep(fixed_delay)

        #
        # parties tab
        #
        parties_tab = driver.find_element(
            by="css selector", value='img[name="parties"]'
        )
        parties_tab.click()

        time.sleep(fixed_delay)

        table_el = driver.find_element(by="css selector", value=".detailRecordTable")

        # this misspelling is in the original page text
        row_els = table_el.find_elements(
            by="css selector", value="tr td.detailSeperator"
        )

        role_information = list()
        for el in row_els:
            text = clean_text(el.text)
            if "represented by" == text:
                continue
            if text:
                role = get_role(text)

                name_end = text.rfind(",")
                role_information.append((role, clean_text(text[:name_end])))

        row_els = table_el.find_elements(by="css selector", value="tr td.detailData")

        detail_texts = list()
        for el in row_els:
            text = clean_text(el.text)
            if not text:
                continue
            party_infos = dict()
            subfield_names = [
                b_el.text for b_el in el.find_elements(by="css selector", value="b")
            ]
            subfield_ixs = [el.text.find(s) for s in subfield_names]

            subfield_locs = dict(zip(subfield_names, subfield_ixs))

            if subfield_locs:
                party_infos["address"] = clean_text(el.text[: min(subfield_ixs)])
                start_ix = min(subfield_ixs)
                for subfield_name in subfield_locs:
                    name_len = len(subfield_name)
                    field_start = subfield_locs[subfield_name]
                    field_end = el.text.find("\n", field_start) + 1

                    if field_end != 0:
                        s = el.text[field_start + name_len : field_end]
                    else:
                        s = el.text[field_start + name_len :]
                    party_infos[subfield_name] = clean_text(s)

            else:
                party_infos["address"] = clean_text(el.text)

            detail_texts.append(party_infos)

            party_information = dict()
            role_counts = {role: 0 for role, _ in role_information}

            for ((role, name), infos) in zip(role_information, detail_texts):
                role_counts[role] += 1
                role_str = f"{role}_{role_counts[role]}"

                party_information[role_str] = name
                for field, value in infos.items():
                    field_name = to_fieldname(f"{role_str}_{field}")
                    result[field_name] = clean_text(value)

            result.update(party_information)

        time.sleep(fixed_delay)

        #
        # docket tab
        #
        docket_tab = driver.find_element(by="css selector", value='img[name="docket"]')
        docket_tab.click()

        time.sleep(fixed_delay)

        table_el = driver.find_element(by="css selector", value=".detailRecordTable")

        result["docket_transcript"] = table_el.text

        time.sleep(fixed_delay)

        #
        # civil judgments tab
        #
        judgement_tab = driver.find_element(
            by="css selector", value='img[name="judgement"]'
        )
        judgement_tab.click()

        time.sleep(fixed_delay)

        if (
            "Civil judgment information is not available for the selected case."
            not in driver.page_source
        ):
            table_el = driver.find_element(
                by="css selector", value=".detailRecordTable"
            )
            result["judgement_text"] = table_el.text

        #
        # garnishment tab
        #
        garnishment_tab = driver.find_element(
            by="css selector", value='img[name="garnishment"]'
        )
        garnishment_tab.click()

        time.sleep(fixed_delay)

        if (
            "Garnishment information is not available for the selected case."
            not in driver.page_source
        ):
            table_el = driver.find_element(
                by="css selector", value=".detailRecordTable"
            )
            result["garnishment_text"] = table_el.text

    finally:
        driver.quit()

    return result


# -*- coding: utf-8 -*-
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
import random
from selenium.webdriver.common.keys import Keys
import datetime
from selenium.webdriver.firefox.options import Options
from fake_useragent import UserAgent
#-------------------------------------------
import json
import psycopg2
from contextlib import closing
from psycopg2.extras import DictCursor
from psycopg2 import sql
from sshtunnel import SSHTunnelForwarder
# from datas_row_names import *
#-------------------------------------------


def read_url_from_file(url_file):
    url = ''
    with open(url_file, encoding='utf8') as urlF:
        url = urlF.read()
    return url


def get_web_driver():
    options = webdriver.FirefoxOptions()
    # options.headless = True
    try:
        driver = webdriver.Firefox(options=options)
        return driver
    except Exception as exc:
        driver.save_screenshot("Driver error.png")
        return f'Driver error: {exc}'


def load_main_page(url_file):
    try:
        url = read_url_from_file(url_file)
        driver = get_web_driver()
        driver.get(url)
        driver.implicitly_wait(60)
        parentHandle = driver.window_handles[0]
        return {'driver': driver, 'handle': parentHandle}
    except Exception as exc:
        driver.save_screenshot("Load main page err.png")
        driver.close()
        return f'Load main page err: {exc}'


def get_links_from_main_page(driver, handle):
    try:
        nxtBtn = WebDriverWait(driver, 120).until(EC.visibility_of_element_located(
            (By.XPATH, '//*[@id="pager"]/tbody/tr/td[2]/table/tbody/tr/td[2]/span/span')))
        caseFirstLink = driver.find_elements_by_css_selector('.bgs-result > a')
        caseFirstLink[0].click()
        # окрываем первую ссылку
        time.sleep(2)
        return 'ok'
    except Exception as exc:
        driver.save_screenshot("Get links from main page error.png")
        driver.close()
        return f'Get links from main page error: {exc}'


def findRows(driver):
    #find all tabs by class name
    first_tab_datas = ["case_user_doc_number", "case_doc_kind", "case_doc_instance",
                       "g_case_user_category", "case_doc_subject_rf", "case_user_doc_court", "case_user_judge",
                       "case_links_inet"]
    second_tab_datas = ["case_user_doc_entry_date", "g_case_origin_date",
                        "case_user_doc_result_date", "case_user_doc_validity_date"]
    insert_datas = []
    insert_datas_dict = {
    "participants_role":"",
    "participants_value":"",
    "case_user_doc_number":"",
    "case_doc_kind":"",
    "case_common_judicial_uid":"",
    "case_doc_instance":"",
    "g_case_user_category":"",
    "case_doc_subject_rf":"",
    "case_user_doc_court":"",
    "case_user_doc_result":"",
    "case_user_doc_result_date":"",
    "case_links_inet":"",
    "case_user_judge":"",
    "case_user_doc_entry_date":"",
    "g_case_origin_date":"",
    "case_common_event_date":"",
    "case_common_event_time":"",
    "case_common_event_name":"",
    "case_common_event_result":"",
    "case_dock":""
    }
    #tabs = driver.find_elements_by_class_name('tab')
    tabs = WebDriverWait(driver, 180).until(EC.element_to_be_clickable((By.CLASS_NAME,'tabName')))
    tabs = driver.find_elements_by_css_selector('.tabBar > li')
    #find participants rows
    try:
        tabs[0].click()
    except:
        tabs[0].click()
        print('Tab switch error')
    #end find0

    time.sleep(0.15)
    for tab in tabs:
        try:
            tab.click()
        except Exception as exc:
            print('Tab switch error: ',exc)
        time.sleep(0.15)
        tab_rows = driver.find_elements(By.XPATH,'//*[@class="fieldsTable"]/tbody/tr')
        tab_label = tab.text
        #scrape first tabe
        if tab_label == 'Дело':
            print('Дело')
            participant_role = ''
            participant_value = ''
            if driver.find_element_by_xpath('//*[@data-name = "case_common_parts_m2_search"]').get_attribute('class') == 'one-field':
                participants =  driver.find_elements_by_xpath('//*[@data-name = "case_common_parts_m2_search"]/td[2]/div/div/div/table/tbody/tr')
                for participant in participants:
                    data_pos = (participant.get_attribute('data-pos'))
                    persons = driver.find_elements_by_xpath('//*[@data-name = "case_common_parts_m2_search"]/td[2]/div/div/div/table/tbody/tr[@data-pos = "' + data_pos + '"]/td')
                    for index, person in enumerate(persons):
                        sep = ''
                        if index == len(persons):
                            sep = ''
                        else:
                            sep = '|'
                        if index % 2 == 0:
                            participant_role = participant_role + person.text + sep
                        else:
                            participant_value = participant_value + person.text + sep
                insert_datas_dict["participants_role"] = participant_role
                insert_datas_dict["participants_value"] = participant_value
            #
            tr_value = ''
            tab_index = int(tab.get_attribute('data-index'))
            for tr in tab_rows:
                data_name = tr.get_attribute('data-name')
                tr_class = tr.get_attribute('class')
                if tr_class == 'one-field' and data_name in first_tab_datas:
                    tr_value = driver.find_element_by_xpath('//*[@data-name = "' + data_name + '"]/td[2]/div/div').text
                    if tr_value != '':
                        insert_datas.append([data_name,tr_value])
                        insert_datas_dict[data_name] = tr_value
        #end first tabe
        #scrape second tab
        if tab_label == 'Движение по делу':
            tab_rows = driver.find_elements(By.XPATH,'//*[@class="fieldsTable"]/tbody/tr')
            print('Движение по делу')
            tr_value = ''
            for tr in tab_rows:
                data_name = tr.get_attribute('data-name')
                tr_class = tr.get_attribute('class')
                if tr_class == 'one-field' and data_name in second_tab_datas:
                    tr_value = driver.find_element_by_xpath('//*[@data-name = "' + data_name + '"]/td[2]/div/div').text
                    insert_datas.append([data_name,tr_value])
                    insert_datas_dict[data_name] = tr_value
                #
            if driver.find_element_by_xpath('//*[@data-name = "case_common_event_m2"]').get_attribute('class') == 'one-field':
                case_common_events=  driver.find_elements_by_xpath('//*[@data-name = "case_common_event_m2"]/td[2]/div/div/div/table/tbody/tr')
                event_date = ''
                event_time = ''
                event_name = ''
                event_result = ''
                for case_common_event in case_common_events:
                    data_pos = case_common_event.get_attribute('data-pos')
                    case_events = driver.find_elements_by_xpath('//*[@data-name = "case_common_event_m2"]/td[2]/div/div/div/table/tbody/tr[@data-pos = "' + data_pos + '"]/td')
                    for index,case_event in enumerate(case_events):
                        sep = ''
                        if index == len(persons):
                            sep = ''
                        else:
                            sep = '|'
                        if index == 0:
                            event_date = event_date + case_event.text + sep
                        elif index == 1:
                            event_time = event_time + case_event.text + sep
                        elif index == 2:
                            event_name = event_name + case_event.text + sep
                        else:
                            event_result = event_result + case_event.text + sep
                insert_datas_dict["case_common_event_date"] = event_date
                insert_datas_dict["case_common_event_time"] = event_time
                insert_datas_dict["case_common_event_name"] = event_name
                insert_datas_dict["case_common_event_result"] = event_result
                    #end

        pageSource = ''
        if tab_label == 'Судебные акты':
            time.sleep(0.25)
            if len(driver.find_elements_by_tag_name("iframe")) !=0:
                try:
                    driver.switch_to.frame(driver.find_element_by_tag_name("iframe"))
                    print('Судебные акты')
                except:
                    print('Frame switch error')
                time.sleep(0.25)
                #p_tags = driver.find_elements_by_xpath('/html/body/p')
                dock = ''

                insert_datas.append(['case_dock','dock'])
                insert_datas_dict['case_dock'] = dock
                pageSource = driver.page_source #execute_script("return document.body.innerHTML;")
                #insert_datas.append(['case_dock','dock'])
                insert_datas_dict['case_dock'] = pageSource
            else:
                insert_datas_dict['case_dock'] = '0'
    return insert_datas_dict #insert_datas_dict
#end code


def get_attributes(driver, element) -> dict:
    return driver.execute_script(
        """
        let attr = arguments[0].attributes;
        let items = {};
        for (let i = 0; i < attr.length; i++) {
            items[attr[i].name] = attr[i].value;
        }
        return items;
        """,
        element
    )


def get_datas_from_page(driver, handle):
    try:
        data = findRows(driver)
        return data
    except Exception as exc:
        driver.save_screenshot("Get datas from page error.png")

        driver.close()
        return f'Get datas from page error: {exc}'


def next_case(driver, handle):
    try:
        driver.switch_to.window(handle)
        forward_btn = driver.find_element(By.XPATH,
                                          '/html/body/div[2]/div[1]/div[2]/div/div/div[2]/div[4]/div[1]/div/div/span[3]')
        forward_btn_attr = get_attributes(driver, forward_btn)
        forward_btn.click()
        return forward_btn_attr
    except Exception as exc:
        driver.save_screenshot("Next case error.png")
        driver.close()
        return f'Next case error: {exc}'


def back_to_list(driver, handle):
    try:
        driver.switch_to.window(handle)
        back_to_list_btn = WebDriverWait(driver, 180).until(EC.element_to_be_clickable((By.ID, 'backToListBtn')))
        back_to_list_btn.click()
        return 'ok'
    except Exception as exc:
        driver.save_screenshot("Back to list error.png")
        driver.close()
        return f'Back to list error: {exc}'


def next_main_page(driver, handle, page):
    try:
        next_page = WebDriverWait(driver, 180).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/'
                                                                                                 'div[1]/div[2]/div/div/'
                                                                                                 'div[2]/div[3]/ul[1]/'
                                                                                                 'li[7]/div[2]/table/ '
                                                                                                 'tbody/tr/td[2]/table/ '
                                                                                                 'tbody/tr/td[2]/input')))
        next_btn = WebDriverWait(driver, 180).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[1]/div[2]/div/div/div[2]/div[3]/ul[1]/li[7]/'
                                                  'div[2]/table/tbody/tr/td[2]/table/tbody/tr/td[2]/span/span')))
        next_page.send_keys(Keys.CONTROL, 'a')
        time.sleep(random.randint(1, 2))
        next_page.send_keys(str(page + 1))
        time.sleep(random.randint(1, 3))
        next_btn.click()
        return 'OK'
    except Exception as exc:
        driver.close()
        driver.save_screenshot("Next main page error.png")
        return f'Next main page error: {exc}'

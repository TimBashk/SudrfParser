# -*- coding: utf-8 -*-
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
#from seleniumwire import webdriver
from selenium.webdriver.common.by import By
import time
import random
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from fake_useragent import UserAgent
#-------------------------------------------
import json
import psycopg2
from contextlib import closing
from psycopg2.extras import DictCursor
from psycopg2 import sql
from sshtunnel import SSHTunnelForwarder
#-------------------------------------------
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

def findRows(driver):

    #find all tabs by class name
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

#main code
#prepare datas
first_tab_datas = ["case_user_doc_number", "case_doc_kind","case_doc_instance",
"g_case_user_category","case_doc_subject_rf", "case_user_doc_court", "case_user_judge","case_links_inet"]
second_tab_datas = ["case_user_doc_entry_date","g_case_origin_date",
"case_user_doc_result_date","case_user_doc_validity_date"]
#end

options = webdriver.FirefoxOptions()
#options.headless = True
'''proxy = "138.128.91.165:8000"
firefox_capabilities = webdriver.DesiredCapabilities.FIREFOX
#firefox_capabilities["marionette"] = True

firefox_capabilities["proxy"] = {
    "proxyType":"MANUAL",
    "httpProxy":proxy,
    "ftpProxy":proxy,
    "sslProxy":proxy
}'''
p = 1
try:
    driver = webdriver.Firefox(options = options)
except Exception as exc:
    print('Driver error:', exc)

try:
   main_url = ''
   with open('main_url.txt','r',encoding="utf-8") as mainUrlF:
       main_url = mainUrlF.read()
   with open('current_url.txt','r',encoding="utf-8") as currUrlF:
       current_url = currUrlF.read()
   with open('current_page.txt','r',encoding="utf-8") as currPageF:
       current_page = int(currPageF.read())
   if current_url =='':
       try:
           driver.get(main_url)
           driver.implicitly_wait(60)
           parentHandle = driver.window_handles[0]
           nxtBtn = WebDriverWait(driver, 360).until(EC.visibility_of_element_located((By.XPATH,'//*[@id="pager"]/tbody/tr/td[2]/table/tbody/tr/td[2]/span/span')))
           caseFirstLink = driver.find_elements_by_css_selector('.bgs-result > a')
           caseFirstLink[0].click()
           #окрываем первую ссылку
           time.sleep(2)
           p = 1
       except Exception as exc:
           print('Error Msg:',' Web page is not available!')
   else:
        driver.get(current_url)
        driver.implicitly_wait(60)
        p = current_page
        parentHandle = driver.window_handles[0]
except Exception as exc:
   print(exc)
print('Страница загружается ... \n')
count = 0
#driver.get(url)
cases_n = p
captcha = 0
start_time = time.time()
while p < 11743:
    try:
        driver.switch_to.window(parentHandle)
        time.sleep(1.5)
        wait = driver.find_element_by_tag_name('body').get_attribute('class')
        w = 0
        while 'globalWait' in wait:
            time.sleep(0.5)
            wait = driver.find_element_by_tag_name('body').get_attribute('class')
            print('.',end = ' ')
            w = w + 1
            if w>100:
                """capcha = driver.find_element_by_id('capchaDialog')
                print(capcha.get_attribute('title'))"""
                time.sleep(20)
                driver.refresh()
                time.sleep(15)
                driver.back()
                p = p - 1
                wait = 'ok'
    except Exception as exc:
        print('Ошибка: ', exc)
        driver.save_screenshot("error_screenshot_1.png")
    try:
        logo = WebDriverWait(driver, 240).until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[2]/div[1]/div[1]/a/img')))
    except Exception as exc:
            print('Ошибка: ', exc)
            driver.save_screenshot("error_screenshot_2.png")
    try:
        forward_btn = WebDriverWait(driver, 300).until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[2]/div[1]/div[2]/div/div/div[2]/div[4]/div[1]/div/div/span[3]')))
        driver.save_screenshot("logo_finded.png")
        #print('The logo finded')
    except Exception as exc:
        print('Ошибка: ', exc)
        driver.save_screenshot("error_screenshot_3.png")
    try:
        driver.switch_to.window(parentHandle)
        forward_btn = driver.find_element(By.XPATH,'/html/body/div[2]/div[1]/div[2]/div/div/div[2]/div[4]/div[1]/div/div/span[3]')
        forward_btn_attr = get_attributes(driver,forward_btn)
        while 'disabled' in forward_btn_attr:
            #forward_btn = driver.find_element(By.XPATH,'/html/body/div[2]/div[1]/div[2]/div/div/div[2]/div[4]/div[1]/div/div/span[3]') #новое 04.07
            time.sleep(0.15)
            print('Пожалуйста подождите . . .')
            forward_btn_attr = get_attributes(driver,forward_btn)
            driver.save_screenshot("button_stat.png")
            forward_btn = driver.find_element(By.XPATH,'/html/body/div[2]/div[1]/div[2]/div/div/div[2]/div[4]/div[1]/div/div/span[3]')

        if 'disabled' not in forward_btn_attr:
            datas = findRows(driver)
            if datas != None:
                keys = datas.keys()
                sql = "INSERT INTO sudrf_cases (" + ", ".join(datas.keys()) + ") VALUES (" + ", ".join(["%("+c+")s" for c in datas]) + ")"
                try:
                    with SSHTunnelForwarder(
                         ('194.61.3.79', 22),
                         #ssh_private_key="</path/to/private/ssh/key>",
                         ### in my case, I used a password instead of a private key
                         ssh_username="administrator",
                         ssh_password="ou93HQYAJLGl",
                         remote_bind_address=('localhost', 5432)) as server:

                         server.start()
                         #print("server connected")

                         params = {
                             'database': 'postgres',
                             'user': 'postgres',
                             'password': 'Asd123321ASD',
                             'host': 'localhost',
                             'port': server.local_bind_port
                             }

                         conn = psycopg2.connect(**params)
                         cursor = conn.cursor()
                         #print("Database connected")
                         cursor.execute(sql, datas)
                         conn.commit()
                         print('Порядковый номер карточки: ', str(p))
                         print('Категория: ', datas['g_case_user_category'] + '\n')
                         print('ЗАПИСАНО ' + ' Время: ' + str(round(time.time() - start_time)) + ' сек.')
                         print('\n ++++++++++++++++++ \n')
                except (Exception, psycopg2.DatabaseError) as error:
                    print(error)
            time.sleep(0.1)
            #print('The button finded')
            print('Следующий . . .')
            p = p + 1
            driver.switch_to.window(parentHandle)
            with open('current_url.txt','w') as curUrlF:
                if driver.current_url != 'https://bsr.sudrf.ru/bigs/portal.html':
                    curUrlF.write(driver.current_url)
            with open('current_page.txt','w') as currPageF:
                currPageF.write(str(p))
            with open('elapsed_time.txt','w') as elTime:
                elTime.write(str(round(time.time() - start_time)))
            time.sleep(0.5)
            forward_btn = driver.find_element(By.XPATH,'/html/body/div[2]/div[1]/div[2]/div/div/div[2]/div[4]/div[1]/div/div/span[3]')
            forward_btn.click()
        """while 'disabled' in forward_btn_class:
            forward_btn = driver.find_element(By.XPATH,'/html/body/div[2]/div[1]/div[2]/div/div/div[2]/div[4]/div[1]/div/div/span[3]')
            forward_btn_class = forward_btn.get_attribute('class')
            time.sleep(0.2)"""
        """capcha = driver.find_element_by_id('capchaDialog')
        print(capcha.get_attribute('title'))"""
    except Exception as exc:
        print('Ошибка: ', exc)
        driver.save_screenshot("err_screenshot_4.png")
cursor.close()
conn.close()

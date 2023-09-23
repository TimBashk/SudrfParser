import parser_functions

main_page = parser_functions.load_main_page('main_url.txt')
driver = main_page['driver']
win_handle = main_page['handle']

for j in range(1, 100):
    parser_functions.get_links_from_main_page(driver, win_handle)
    for i in range(10):
        print(f'++++++++++++++++ case № {(i+1)*j} ++++++++++++++++')
        print(parser_functions.get_datas_from_page(driver, win_handle))
        if i != 9:
            print(parser_functions.next_case(driver, win_handle))
        else:
            parser_functions.back_to_list(driver, win_handle)
            parser_functions.next_main_page(driver, win_handle, j)
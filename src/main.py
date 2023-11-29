import sys
sys.path.append('../')
import selenium.webdriver.chrome.webdriver
from selenium import webdriver
from selenium import common
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from json_handler import HandlerJson
from define import *
from gmail_python.src.main import GmailHandler
from token_gmail import TOKEN_GMAIL
import argparse
import datetime
import pickle
import time


def print_color(color: BColores, msg: str, bold: bool = False, underline: bool = False) -> None:
    bold_cmd = ''
    if bold:
        bold_cmd = BColores.BOLD
    underline_cmd = ''
    if underline:
        underline_cmd = BColores.UNDERLINE
    print(f'{color}{bold_cmd}{underline_cmd}{msg}{BColores.ENDC}')


def print_ok(msg: str, bold: bool = False, underline: bool = False) -> None:
    print_color(BColores.GREEN, msg=msg, bold=bold, underline=underline)


def print_warning(msg: str, bold: bool = False, underline: bool = False) -> None:
    print_color(BColores.YELLOW, msg=msg, bold=bold, underline=underline)


def print_fail(msg: str, bold: bool = False, underline: bool = False) -> None:
    print_color(BColores.RED, msg=msg, bold=bold, underline=underline)


def format_price(value: float) -> str:
    return f'R$ {value:,.2f}'.replace('.', ',')


def format_html_space(value: str) -> str:
    return value.replace(' ', '&nbsp;')


def get_timestamp() -> str:
    return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')


def get_price(price_label: str, attr_data_price: str) -> tuple:
    currency_symbol = 'R$'
    if price_label.lower().find("infinity") >= 0:
        return 0.0, f'{currency_symbol} -', True
    else:
        try:
            price = float(attr_data_price)
        except:
            price = 0.0
        price_fmt = f'{currency_symbol} {price:,.2f}'.replace('.', ',')
        return price, price_fmt, False


def find_game_info(id: str, games: list) -> dict:
    for game in games:
        if 'id' in game:
            if id.lower() == game['id'].lower():
                return game


def handle_html_page() -> tuple:
    serv = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=serv)

    driver.get('https://www.amazon.com.br/hz/wishlist/ls/2BEBH8MZBN7RJ/ref=nav_wishlist_lists_2')
    time.sleep(2)

    driver_end_page(driver)
    # time.sleep(3)

    try:
        _ = driver.find_element(By.XPATH, '//*[@id="g-items"]')
    except common.exceptions.NoSuchElementException:
        print_warning('id g-items not found, sleeping 20...')
        time.sleep(20)
        _ = driver.find_element(By.XPATH, '//*[@id="g-items"]')
        driver_end_page(driver)

    all_games = []
    all_games_dict = []
    for item in driver.find_elements(By.TAG_NAME, 'li'):
        if item.get_attribute('data-itemid') is not None:
            all_games.append(item)
            # print(item)
            #
            attr_data_itemid = item.get_attribute('data-itemid')
            # print(f'data-itemid [{attr_data_itemid}]')
            attr_data_price = item.get_attribute('data-price')
            # print(f'attr_data_price [{attr_data_price}]')
            price, price_fmt, out_of_stock = get_price(attr_data_price, attr_data_price)

            name_tag = item.find_element(By.XPATH, f'//*[@id="itemName_{attr_data_itemid}"]')
            game_title = name_tag.get_attribute('title')
            # print(f'jogo [{game_title}] preço [{price_fmt}]')
            #
            dict_game = {
                'id': attr_data_itemid,
                'name': game_title,
                'price': price,
                'price_fmt': price_fmt,
                'in_stock': not out_of_stock
            }
            all_games_dict.append(dict_game)
            # print(dict_game)

    return all_games, all_games_dict


def driver_end_page(driver) -> None:
    for i in range(5):
        html = driver.find_element(By.TAG_NAME, 'html')
        html.send_keys(Keys.END)
        time.sleep(2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--exit', action='store_true', help='Exit')
    parser.add_argument('-r', '--reset', action='store_true', help='Reset arquivo JSON')
    args = parser.parse_args()

    print('main')

    j = HandlerJson()
    if args.reset:
        print('reset json file...')
        j.reset_json()
    j.dump_json()

    if args.exit:
        sys.exit()

    all_games, all_games_dict = handle_html_page()
    # with open("all_games_dict.pickle", "wb") as f:
    #     pickle.dump(all_games_dict, f)
    # with open("all_games_dict.pickle", "rb") as f:
    #     all_games_dict = pickle.load(f)

    # get last run info
    last_run_info = j.get_last_run()
    games_with_discount = []
    if last_run_info is not None:
        # print(last_run_info)
        # compare prices
        for old_game in last_run_info['games']:
            # print(f'\n\n=========================================================================')
            # print(old_game)
            current_game = find_game_info(old_game['id'], all_games_dict)
            if current_game is None:  # game não existe mais na lista
                continue
            name = old_game['name']
            old_price = old_game['price']
            current_price = current_game['price']
            # print(f'game [{name}] preco old [{old_price}] preco novo [{current_price}]')
            if current_price < old_price:  # preco baixou
                price_diff = round(old_price - current_price, 2)
                price_diff_pct = 100.0 - ((current_price / old_price) * 100)
                price_diff_pct_fmt = f'{price_diff_pct:,.2f}%'.replace('.', ',')
                print(f'\n### game [{name}]\npreco old [{old_price}] preco novo [{current_price}] diff [{price_diff}] [{price_diff_pct_fmt}]')
                print_ok('preço baixou!!!')
                games_with_discount.append({
                    'name': name,
                    'old_price': old_price,
                    'new_price': current_price,
                    'diff_price': price_diff,
                    # 'diff_price_fmt': f'R$ {price_diff:,.2f}'.replace('.', ','),
                    'diff_price_fmt': format_price(price_diff),
                    'pct_diff_price': round(price_diff_pct, 2),
                    'pct_diff_price_fmt': price_diff_pct_fmt,
                    # 'status_price': 'down',
                })
            elif current_price > old_price:  # preco aumentou
                price_diff = round(current_price - old_price, 2)
                price_diff_pct = 100.0 - ((old_price / current_price) * 100)
                price_diff_pct_fmt = f'{price_diff_pct:,.2f}%'.replace('.', ',')
                print(f'\n### game [{name}]\npreco old [{old_price}] preco novo [{current_price}] diff [{price_diff}] [{price_diff_pct_fmt}]')
                print_fail('preço aumentou...')
            # else:
            #     pass

    print('\n\n')
    body_email = ''
    if len(games_with_discount) > 0:
        games_with_discount = sorted(games_with_discount, key=lambda k: k['diff_price'], reverse=True)
        for g in games_with_discount:
            # print(g)
            if g.get('pct_diff_price', 0.0) > j.get_min_discount_pct():
                body_email += f'<span style="color: red;"><b>{g.get("name")}</b></span>' + '<br>'
                body_email += f'Preço antigo: {format_price(g.get("old_price", 0.0))}' + '<br>'
                body_email += f'Preço novo  : {format_price(g.get("new_price", 0.0))}' + '<br>'
                body_email += f'Diferença: {g.get("diff_price_fmt")} - {g.get("pct_diff_price_fmt")}' + '<br>'
                body_email += '<br>'
    body_email += '<br>' + '<b>Gerado em:</b>' + '<br>' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    body_email = format_html_space(body_email)

    gmail = GmailHandler(email_owner='fernandobalcantara@gmail.com', password=TOKEN_GMAIL, flag_send=False)
    now = datetime.datetime.now()
    gmail.set_subject(f'teste email desconto amazon lista jogos - {now.strftime("%Y-%m-%d")}')
    gmail.set_to(same_as_owner=True)
    gmail.set_body(body_email)
    gmail.send(debug=False)

    # write to json file
    # j.write_run(timestamp=get_timestamp(), total=len(all_games), infos=all_games_dict)

    # while True:
    #     pass
    # time.sleep(3)
    # driver.close()

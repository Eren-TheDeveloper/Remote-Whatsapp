import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from selenium.common.exceptions import TimeoutException

from config import create_driver, data_path, xpath_literal

def get_data():
    group_names = []
    names = []
    taken_numbers = []
    driver = create_driver()
    try:
        driver.maximize_window()
        driver.get("https://web.whatsapp.com/")
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.ID, "pane-side"))
        )
        return collect_data(driver, group_names, names, taken_numbers)
    finally:
        driver.quit()


def collect_data(driver, group_names, names, taken_numbers):
    for index in range(1, 50):
        XPATH = f"//*[@id='pane-side']/div[1]/div/div/div[{index}]/div/div/div/div[2]/div[1]/div[1]/span[2]"
        try:
            group_name = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.XPATH, XPATH))
            )    
            group_names.append(group_name.text)
            print(group_name.text)
        except TimeoutException:
            pass

    for index in range(1, 50):
        XPATH_NO_SPAN = f'//*[@id="pane-side"]/div[1]/div/div/div[{index}]/div/div/div/div[2]/div[1]/div[1]/span'
        try:
            group_name_no_span = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.XPATH, XPATH_NO_SPAN))
            )
            group_names.append(group_name_no_span.text)
            print(group_name_no_span.text)
        except TimeoutException:
            pass

    for index in range(1, 50):
        XPATH = f'//*[@id="pane-side"]/div[1]/div/div/div[{index}]/div/div/div/div[2]/div[1]/div[1]/div/div/span'
        try:
            wp_name = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.XPATH, XPATH))
            )
            names.append(wp_name.text)
            print(wp_name.text)
        except TimeoutException:
            pass

    for name in names:
        XPATH = f'//*[@id="pane-side"]//span[@title={xpath_literal(name)}]'
        try:
            contact_names = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, XPATH))
            )
            time.sleep(1)
            contact_names.click()
            time.sleep(1)
            contact_number = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="main"]/header/div[1]/div[2]/div[1]/div'))
            )
            time.sleep(1)
            contact_number.click()
            time.sleep(1)
            number = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="app"]/div/div/div[3]/div/div[6]/span/div/span/div/div/div/section/div[1]/div[2]/div[2]/span/div/span'))
            )
            time.sleep(1)
            taken_numbers.append(number.text)
            print(number.text)
        except TimeoutException:
            taken_numbers.append(None)
            print(f"Phone number unavailable: {name}")
        
    data = {
        "group_names": list(dict.fromkeys(group_names)),
        "names": names,
        "taken_numbers": taken_numbers,
    }
    output = data_path()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=4, ensure_ascii=False)
    temporary.replace(output)
    return data


if __name__ == "__main__":
    get_data()

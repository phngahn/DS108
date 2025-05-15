from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import time

### Lấy đường dẫn chung của sản phẩm
driver = webdriver.Chrome()
url = "https://www.thegioididong.com/may-doi-tra/dtdd?pi=15"
driver.get(url)
time.sleep(15)

elements = driver.find_elements(By.XPATH, "//div[@class = 'prdItem']//a")
url_item = []

for element in elements:
    href_value = element.get_attribute("href")
    url_item.append(href_value)


driver.quit()

df = pd.DataFrame(url_item, columns=["URL"])
df.to_csv("urls.csv", index=False)

### Lấy đường dẫn riêng của từng sản phẩm bên trong đường dẫn chung
driver = webdriver.Chrome()
df = pd.read_csv("urls.csv")

urls = df['URL'].tolist()
final_url = []
i = 0

for url in urls:
    i = i + 1
    print(i , "/", len(urls))

    driver.get(url + "&p=25")
    
    time.sleep(10)
    elements = driver.find_elements(By.XPATH, "//div[@class = 'prdItem']//a")

    for element in elements:
        href_value = element.get_attribute("href")
        final_url.append(href_value)

driver.quit()

df = pd.DataFrame(final_url)
df.to_csv('final_url.csv', index = False)
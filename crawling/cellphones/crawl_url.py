from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import pandas as pd

driver = webdriver.Chrome()
url = "https://cellphones.com.vn/hang-cu/dien-thoai.html"
driver.get(url)

time.sleep(10)

elements = driver.find_elements(By.XPATH, "//div[@class = 'product-info']//a")
url_item = []
i = 0

for element in elements:
    i += 1
    print(i, "/", len(elements))
    href_value = element.get_attribute("href")
    url_item.append(href_value)
    
driver.quit()

df = pd.DataFrame(url_item, columns = ["URL"])
df.to_csv("urls.csv", index=False)

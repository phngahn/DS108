from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import re

df = pd.read_csv('final_url.csv')
urls = df["URL"].tolist()

def get_price(driver):
    new_price = None
    old_price = None
    
    try:
        # Tìm phần tử div có class "mPrice"
        price_element = driver.find_element(By.CSS_SELECTOR, "div.mPrice")

        # Giá cũ của sản phẩm nằm trong thẻ strong
        strong_element = price_element.find_element(By.CSS_SELECTOR, "strong")
        old_price = strong_element.text

        # Giá mới của sản phẩm nằm trong thẻ span
        span_element = price_element.find_element(By.CSS_SELECTOR, "span")
        new_price = span_element.text
    except:
        return old_price, new_price

    return old_price, new_price

def get_warranty(driver):
    warranty = None

    try:
        # Tìm tất cả các phần tử li có chữ 'Bảo hành'
        li_element = driver.find_element(By.XPATH, "//li[contains(., 'Bảo hành')]")
        warranty_element = li_element.find_element(By.CSS_SELECTOR, "strong")
        warranty = warranty_element.text
    except:
        return warranty

    return warranty

def get_condition(driver):
    condition = None

    try:
        # Tìm tất cả các phần tử li có chữ 'Tình trạng sản phẩm'
        li_element = driver.find_element(By.XPATH, "//li[contains(., 'Tình trạng sản phẩm')]")
        condition_element = li_element.find_element(By.CSS_SELECTOR, "strong")
        condition = condition_element.text
    except:
        return condition

    return condition

def get_color(driver):
    color = None

    try:
        # Tìm tất cả phần tử div có class là 'infocl'
        color_element = driver.find_element(By.XPATH, "//div[@class = 'infocl']/span[1]")
        color = color_element.text
    except:
        return color

    return color

def get_name(driver):
    name = None
    
    try:
        # Tìm tất cả các phần tử div với class "titleName"
        name_element = driver.find_element(By.CSS_SELECTOR, "div.titleName")
        name = name_element.text
    except:
        return name
        
    return name

def get_image(driver):
    image = None

    try:
        image_element = driver.find_element(By.XPATH, "//div[@class = 'img-wrapper swiper-slide swiper-slide-active']/img")
        image = image_element.get_attribute("src")
    except:
        return image

    return image

def scrape_data(driver):
    CPU = None
    GPU = None
    RAM = None
    capacity = None
    Time = None
    battery = None
    os = None
    display_technology = None
    screen_resolution = None
    screen_size = None
    refresh_rate = None
    SIM = None
    size = None
    weight = None
    bluetooth = None
    brand = None
    
    try:
        wait = WebDriverWait(driver, 4)
        
        button = wait.until(EC.visibility_of_element_located((By.XPATH, "//button[@class = 'btnViewFullSpec']")))
        # Scroll tới button
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)

        # Click vào button
        driver.execute_script("arguments[0].click();", button)

        cpu_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'speciTable speciFull')]//div[contains(text(), 'Cấu hình & Bộ nhớ')]/following-sibling::table//span[contains(text(), 'Chip xử lý')]/parent::td/following-sibling::td/span/span")
        if not cpu_elements:
            cpu_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'speciTable speciFull')]//div[contains(text(), 'Cấu hình & Bộ nhớ')]/following-sibling::table//span[contains(text(), 'Chip xử lý')]/parent::td/following-sibling::td/span/a")
        gpu_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'speciTable speciFull')]//div[contains(text(), 'Cấu hình & Bộ nhớ')]/following-sibling::table//span[contains(text(), 'GPU')]/parent::td/following-sibling::td/span/a")
        os_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'speciTable speciFull')]//div[contains(text(), 'Cấu hình & Bộ nhớ')]/following-sibling::table//a[contains(text(), 'Hệ điều hành')]/parent::td/following-sibling::td/span/span")
        ram_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'speciTable speciFull')]//div[contains(text(), 'Cấu hình & Bộ nhớ')]/following-sibling::table//a[contains(text(), 'RAM')]/parent::td/following-sibling::td/span/span")
        capacity_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'speciTable speciFull')]//div[contains(text(), 'Cấu hình & Bộ nhớ')]/following-sibling::table//span[contains(text(), 'Dung lượng lưu trữ')]/parent::td/following-sibling::td/span/span")
        battery_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'speciTable speciFull')]//div[contains(text(), 'Pin & Sạc')]/following-sibling::table//span[contains(text(), 'Dung lượng pin')]/parent::td/following-sibling::td/span/span")
        display_technology_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'speciTable speciFull')]//div[contains(text(), 'Camera & Màn hình')]/following-sibling::table//span[contains(text(), 'Công nghệ màn hình')]/parent::td/following-sibling::td/span/a")
        screen_resolution_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'speciTable speciFull')]//div[contains(text(), 'Camera & Màn hình')]/following-sibling::table//a[contains(text(), 'Độ phân giải màn hình')]/parent::td/following-sibling::td/span/span")
        screen_size_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'speciTable speciFull')]//div[contains(text(), 'Camera & Màn hình')]/following-sibling::table//span[contains(text(), 'Màn hình rộng')]/parent::td/following-sibling::td/span/span")
        refresh_rate_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'speciTable speciFull')]//div[contains(text(), 'Camera & Màn hình')]/following-sibling::table//span[contains(text(), 'Màn hình rộng')]/parent::td/following-sibling::td/span/span/a")
        SIM_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'speciTable speciFull')]//div[contains(text(), 'Kết nối')]/following-sibling::table//span[contains(text(), 'SIM')]/parent::td/following-sibling::td/span/a")
        bluetooth_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'speciTable speciFull')]//div[contains(text(), 'Kết nối')]/following-sibling::table//a[contains(text(), 'Bluetooth')]/parent::td/following-sibling::td/span/span")
        time_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'speciTable speciFull')]//div[contains(text(), 'Thiết kế & Chất liệu')]/following-sibling::table//span[contains(text(), 'Thời điểm ra mắt')]/parent::td/following-sibling::td/span/span")
        brand_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'speciTable speciFull')]//div[contains(text(), 'Thiết kế & Chất liệu')]/following-sibling::table//span[contains(text(), 'Hãng')]/parent::td/following-sibling::td/span")
        size_weight_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'speciTable speciFull')]//div[contains(text(), 'Thiết kế & Chất liệu')]/following-sibling::table//span[contains(text(), 'Kích thước, khối lượng')]/parent::td/following-sibling::td/span/span")
        
        # Lấy thông tin từ các thẻ
        CPU = cpu_elements[0].text if cpu_elements else None
        GPU = gpu_elements[0].text if gpu_elements else None
        os = os_elements[0].text if os_elements else None
        RAM = ram_elements[0].text if ram_elements else None
        capacity = capacity_elements[0].text if capacity_elements else None
        Time = time_elements[0].text if time_elements else None
        battery = battery_elements[0].text if battery_elements else None
        display_technology = display_technology_elements[0].text if display_technology_elements else None
        screen_resolution = screen_resolution_elements[0].text if screen_resolution_elements else None
        screen_size = screen_size_elements[0].text.split('-')[0].strip() if screen_size_elements else None
        refresh_rate = refresh_rate_elements[0].text if refresh_rate_elements else None
        SIM = SIM_elements[0].text if SIM_elements else None
        brand = brand_elements[0].text if brand_elements else None
        size = re.findall(r"[\d.]+", size_weight_elements[0].text)[:3] if size_weight_elements else None
        weight = re.search(r"Nặng ([\d.]+) g", size_weight_elements[0].text).group(1) if size_weight_elements and re.search(r"Nặng ([\d.]+) g", size_weight_elements[0].text) else None
        bluetooth = bluetooth_elements[0].text if bluetooth_elements else None


    
    except:
        return CPU, GPU, os, RAM, capacity, Time, battery, display_technology, screen_resolution, screen_size, refresh_rate, SIM, brand, size, weight, bluetooth
   
    return CPU, GPU, os, RAM, capacity, Time, battery, display_technology, screen_resolution, screen_size, refresh_rate, SIM, brand, size, weight, bluetooth

driver = webdriver.Chrome()

data = []
i = 0

for url in urls:
    i += 1
    print(i, "/", len(urls))
    driver.get(url)

    name = get_name(driver)
    color = get_color(driver)
    price_old, price_new = get_price(driver)
    image = get_image(driver)
    warranty = get_warranty(driver)
    condition = get_condition(driver)
    CPU, GPU, operating_system, RAM, capacity, Time, battery, display_technology, screen_resolution, screen_size, refresh_rate, SIM, brand, size, weight, bluetooth = scrape_data(driver)
    
    data.append({
        'name': name,
        'brand': brand,
        'color': color,
        'condition': condition,
        'price_old': price_old,
        'price_new': price_new,
        'image': image,
        'warranty': warranty,
        'CPU': CPU,
        'RAM': RAM,
        'capacity': capacity,
        'time': Time,
        'battery': battery,
        'screen_size': screen_size,
        'operating_system' : operating_system,
        'display_technology' : display_technology,
        'screen_resolution' : screen_resolution,
        'SIM' : SIM,
        'size' : size,
        'weight' : weight,
        'bluetooth' : bluetooth,
        'refresh_rate' : refresh_rate,
        'GPU' : GPU
    })

driver.quit()

# Xuất file CSV
df = pd.DataFrame(data)
df.to_csv('raw_data.csv', index=False, encoding='utf-8-sig')



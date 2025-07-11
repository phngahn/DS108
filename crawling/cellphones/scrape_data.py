from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import re
import time

df = pd.read_csv("urls.csv")
urls = df["URL"].tolist()

def get_title(driver):
    title = None
    
    try:
        title_element = driver.find_element(By.XPATH, "//div[@class = 'box-product-name']//h1")
        title = title_element.text
    except:
        return title

    return title.split('-')

def get_brand(driver):
    brand = None

    try:
        title = get_title(driver)
        brand = title[0].strip().split()[0] if title else None
    except:
            return brand

    return brand.strip()


def get_name(driver):
    name = None

    try:
        title = get_title(driver)
        name = title[0]
    except:
        return name
        
    return name.strip()

def get_condition(driver):
    condition = None

    try:
        title = get_title(driver)
        condition = title[1]
    except:
        return condition
        
    return condition.strip()

def get_price(driver):
    price_old = None
    price_new = None

    try:
        price_element = driver.find_element(By.XPATH, "//div[contains(@class, 'tpt-box has')]")
        price_old_element = price_element.find_element(By.CLASS_NAME, "tpt---sale-price")
        price_new_element = price_element.find_element(By.CLASS_NAME, "tpt---price")

        price_old = price_old_element.text
        price_new = price_new_element.text
    except:
        return price_old, price_new

    return price_old, price_new

def get_color(driver):
    color = None

    try:
        color_elements = driver.find_elements(By.XPATH, "//strong[@class = 'item-variant-name']")
        if color_elements:
            color = []
            for color_element in color_elements:
                color.append(color_element.text)
    except:
        return color

    return color

def get_image(driver):
    image = None

    try:
        image_elements = driver.find_elements(By.XPATH, "//li[contains(@class, 'item-variant')]/a")
        image = [element.get_attribute("href") for element in image_elements]
    except:
        return image

    return image     

def get_warranty(driver):
    warranty = None

    try:
        warranty_elements = driver.find_elements(By.XPATH, "//div[@class = 'item-warranty-info']//div[@class = 'description']")
        warranty_description = warranty_elements[1].text
        warranty = re.search(r"\d+\s*tháng", warranty_description).group()
    except:
        return warranty

    return warranty

def scroll_to_button(driver, button_class_name):
    for _ in range(20):
        try:
            button = driver.find_element(By.CLASS_NAME, button_class_name)
            
            # Kiểm tra xem nút có trong viewport không
            is_displayed = driver.execute_script(
                "var rect = arguments[0].getBoundingClientRect(); return rect.top >= 0 && rect.bottom <= window.innerHeight;", button
            )

            if is_displayed:
                return button
            else:
                driver.execute_script("window.scrollBy(0, 200);")
                time.sleep(0.5)
        except:
            driver.execute_script("window.scrollBy(0, 200);")
            time.sleep(0.5)
    
    return None  # Trả về None nếu không tìm thấy nút

def scrape_data(driver):
    wait = WebDriverWait(driver, 5)

    info_order = ["CPU", "RAM", "capacity", "Time", "battery", "screen size", "os", "display technology", "screen resolution", "SIM", "size", "weight", "bluetooth", "refresh rate", "GPU"]
    info_labels = {
        "CPU": "Chip",
        "RAM": "Dung lượng RAM",
        "capacity": "Bộ nhớ trong",
        "Time": "Thời điểm ra mắt",
        "battery": "Pin",
        "screen size": "Kích thước màn hình",
        "os": "Hệ điều hành",
        "display technology": "Công nghệ màn hình",
        "screen resolution": "Độ phân giải màn hình",
        "SIM": "Thẻ SIM",
        "size": "Kích thước",
        "weight": "Trọng lượng",
        "bluetooth": "Bluetooth",
        "refresh rate": "Tần số quét",
        "GPU": "GPU"
    }

    # Ánh xạ từng trường với loại xpath khác nhau
    xpath_type_map = {
        "default": ["CPU", "RAM", "capacity", "Time", "battery", "screen size", "os", "display technology", "screen resolution"],
        "text_equals": ["SIM", "size"],
        "a_contains": ["weight", "bluetooth", "refresh rate", "GPU"]
    }

    result = [None] * len(info_order)

    try:
        # Tắt quảng cáo nếu có
        try:
            close_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "cancel-button-top")))
            close_button.click()
        except:
            pass

        # Mở thông số kỹ thuật
        button = scroll_to_button(driver, "button__show-modal-technical")
        if button:
            driver.execute_script("arguments[0].click();", button)
            time.sleep(2)
        else:
            print("Không tìm thấy nút mở thông số!")

        # Duyệt qua từng trường để lấy dữ liệu
        for idx, key in enumerate(info_order):
            label = info_labels[key]

            if key in xpath_type_map["default"]:
                xpath = f"//div[@class='block-content-product-right']//p[contains(text(), '{label}')]/following-sibling::div"
            elif key in xpath_type_map["text_equals"]:
                xpath = f"//div[@class='block-content-product-right']//p[text()='{label}']/following-sibling::div"
            elif key in xpath_type_map["a_contains"]:
                xpath = f"//div[@class='block-content-product-right']//a[contains(text(), '{label}')]/parent::p/following-sibling::div"
            else:
                continue  # Bỏ qua nếu không khớp loại

            try:
                element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                result[idx] = driver.execute_script("return arguments[0].textContent;", element).strip()
            except:
                pass

    except Exception as e:
        print("Lỗi trong quá trình scrape:", str(e))
        return result

    return result

driver = webdriver.Chrome()

data = []
i = 0

for url in urls:
    i += 1
    print(i, "/", len(urls))
    driver.get(url)

    name = get_name(driver)
    brand = get_brand(driver)
    color = get_color(driver)
    condition = get_condition(driver)
    price_old, price_new = get_price(driver)
    image = get_image(driver)
    warranty = get_warranty(driver)
    CPU, RAM, capacity, Time, battery, screen_size, operating_system, display_technology, screen_resolution, SIM, size, weight, bluetooth, refresh_rate, GPU = scrape_data(driver)

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

df = pd.DataFrame(data)
df.to_csv('raw_data.csv', index=False, encoding='utf-8-sig')
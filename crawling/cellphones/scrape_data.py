from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

df = pd.read_csv("urls.csv")
urls = df["URL"].tolist

def get_title(driver):
    title = None
    
    try:
        title_element = driver.find_element(By.XPATH, "//div[@class = 'box-product-name']//h1")
        title = title_element.text
    except:
        return title

    return title.split('-')

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
        image_element = driver.find_element(By.XPATH, "//div[@class ='box-gallery' ]//div[@class = 'swiper-slide swiper-slide-active']/img")
        image = image_element.get_attribute("src")
    except:
        return image

    return image     

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
    wait = WebDriverWait(driver, 15)

    # Thứ tự các thuộc tính cần lấy
    info_order = ["CPU", "RAM", "capacity", "Time", "battery", "screen size", "os", "display technology", "screen resolution", "SIM", "size", "weight", "bluetooth", "refresh rate"]
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
        "refresh rate": "Tần số quét"
    }

    # Khởi tạo danh sách kết quả với None
    result = [None] * len(info_order)

    try:
        # Tắt quảng cáo nếu có
        try:
            close_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "cancel-button-top")))
            close_button.click()
        except:
            pass

        # Click vào nút xem thông số kỹ thuật
        button = scroll_to_button(driver, "button__show-modal-technical")
        if button:
            driver.execute_script("arguments[0].click();", button)
            time.sleep(2)
        else:
            print("Không tìm thấy nút mở thông số!")

        # Lấy thông tin từng trường
        for idx in range(len(info_order) - 3):  
            key = info_order[idx]
            label = info_labels[key]
            xpath = f"//div[@class='block-content-product-right']//p[contains(text(), '{label}')]/following-sibling::div"
    
            try:
                element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                result[idx] = driver.execute_script("return arguments[0].textContent;", element)
            except:
                pass

        
        for idx in range(len(info_order) - 3, len(info_order) - 2): 
            key = info_order[idx]
            label = info_labels[key]
            xpath = f"//div[@class='block-content-product-right']//p[text()='{label}']/following-sibling::div"
        
            try:
                element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                result[idx] = driver.execute_script("return arguments[0].textContent;", element)
            except:
                pass
                
        for idx in range(len(info_order) - 2, len(info_order)): 
            key = info_order[idx]
            label = info_labels[key]
            xpath = f"//div[@class='block-content-product-right']//a[contains(text(), '{label}')]/parent::p/following-sibling::div"
        
            try:
                element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                result[idx] = driver.execute_script("return arguments[0].textContent;", element)
            except:
                pass
                           
    except:
        return result

    return result
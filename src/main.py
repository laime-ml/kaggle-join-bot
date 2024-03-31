import time

from selenium import webdriver
from selenium.webdriver.common.by import By

# driver = webdriver.Chrome('C:/200_Python/140_Webブラウザー操作(Selenium)/chrome') 
driver = webdriver.Chrome()
driver.get('https://www.yahoo.co.jp/')
time.sleep(2)
element = driver.find_element(By.LINK_TEXT, "ファイナンス")
element.click()
time.sleep(5)
driver.quit()

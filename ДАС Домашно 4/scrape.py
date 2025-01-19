#!/usr/bin/env python
# coding: utf-8

# In[69]:


from datetime import datetime, timedelta
from types import NoneType

from app import scrape
from scrape_functions import get_codes, is_scraped, clean_nulls
import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
import os
from dateutil.relativedelta import relativedelta
import time
from selenium.webdriver.common.by import By


# In[70]:


filtered_codes = get_codes()


# In[71]:


base_url = "https://www.mse.mk/mk/stats/symbolhistory/"


# In[72]:


driver = webdriver.Chrome()

for code in filtered_codes:

    url = base_url + code
    driver.get(url)
    
    if is_scraped(code):
        dataframe = pd.read_csv("static/tables/" + code + ".csv")
        scrape_to_date = datetime.strptime(dataframe["Datum"].iloc[0],"%d.%m.%Y")
        scrape_to_date = scrape_to_date + timedelta(days=1)

    else:
        scrape_to_date = datetime.today() - relativedelta(years=10)
    
    if scrape_to_date >= datetime.today():
       continue
    
    dates = []
    last_transactions = []
    maximums = []
    minimums = []
    averages = []
    changes = []
    amounts = []
    totals = []
    
    date = datetime.now()
    
    while date > scrape_to_date:
        
        from_date = driver.find_element(By.ID, "FromDate")
        to_date = driver.find_element(By.ID, "ToDate")
        submit_button = driver.find_element(By.CLASS_NAME, "btn-primary-sm")
        
        from_date.clear()
        to_date.clear()
        
        
        formatted_date = f"{date.day}.{date.month}.{date.year}"
        if is_scraped(code):
            formatted_new_date = f"{scrape_to_date.day}.{scrape_to_date.month}.{scrape_to_date.year}"
            date = date - relativedelta(days=365)
        else:
            date = date - relativedelta(days=365)
            formatted_new_date = f"{date.day}.{date.month}.{date.year}"
        
        to_date.send_keys(formatted_date)
        from_date.send_keys(formatted_new_date)
        
        submit_button.click()
        
        time.sleep(1)
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find("tbody")
        if table is None:
            break
        rows = table.find_all("tr")
        for row in rows:
            columns = row.find_all('td')
            if len(columns) >= 5:
                dates.append(columns[0].get_text(strip=True))
                last_transactions.append(columns[1].get_text(strip=True))
                maximums.append(columns[2].get_text(strip=True))
                minimums.append(columns[3].get_text(strip=True))
                averages.append(columns[4].get_text(strip=True))
                changes.append(columns[5].get_text(strip=True))
                amounts.append(columns[6].get_text(strip=True))
                totals.append(columns[8].get_text(strip=True))
        
        
    data = {
        "Datum": dates,
        "Last Transaction": last_transactions,
        "Maximum": maximums,
        "Minimum": minimums,
        "Average": averages,
        "Change": changes,
        "Amount": amounts,
        "Total": totals
    }
    
    scraped_data = pd.DataFrame(data)

    scraped_data = clean_nulls(scraped_data)

    if is_scraped(code):
        old_data = pd.read_csv("static/tables/" + code + ".csv")
        final_data = pd.concat([scraped_data, old_data])
        os.remove("static/tables/" + code + ".csv")
        final_data.to_csv("static/tables/" + code + ".csv", index=False)
    else:
        scraped_data.to_csv("static/tables/" + code + ".csv", index=False)
        

        
    
    

    


# In[ ]:





# In[ ]:





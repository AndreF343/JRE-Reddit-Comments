#!/usr/bin/env python
# coding: utf-8

# **Import the drivers and open the chrome window**

# In[16]:


import os
import re
import csv
import sys
import time
import demoji
import logger
import sqlite3
import validators
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException


# In[6]:


# from selenium import webdriver
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


# In[7]:


# load_dotenv()

# username = os.getenv(r"USERNAME")
# password = os.getenv(r"PASSWORD")
# ip = 'gate.smartproxy.com'
# port = '10001'
# # proxy = f"http://{username}:{password}@gate.smartproxy.com:10001"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"

options = webdriver.ChromeOptions()
options.add_argument(f"user-agent={user_agent}")
# options.add_argument("--proxy-server=http://spl3s7ltvy:395ruqJ_rhbC8XwmcA@gate.smartproxy.com:10001")
options.add_argument("--disable-features=OptimizationGuideModelDownloading,OptimizationHintsFetching,OptimizationTargetPrediction,OptimizationHints")
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-extensions')
prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)

# selenium_options = {
#     'proxy': {
#         'http': f"http://{username}:{password}@{ip}:{port}",
#         'https': f"https://{username}:{password}@{ip}:{port}",
#         'no_proxy': 'localhost,127.0.0.1'
#     }
# }

#chrome_options.add_extension(proxies_extension)
#chrome_options.add_extension(user_agent="")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)#, seleniumwire_options=selenium_options)
driver.maximize_window()


# **Open the url for the reddit link of a Joe Rogan episode and get reddit title, upload date, number of upvotes, upvote ratio, and episode title. Save to jr_episodes.csv**

# In[8]:


input_file = 'jr_reddit_episode_list.csv'#'deleted_reddit_url.csv'
df = pd.read_csv(input_file)


# In[9]:


# df=df.drop(index=0)


# In[10]:


df.columns


# In[11]:


def savePosttoDB(episode_data):
    conn = sqlite3.connect(r"C:\Users\andre\OneDrive\Desktop\JRReader\datadump\joerogan.db")
    cursor = conn.cursor()
    
    insert_statement = 'INSERT INTO reddit_posts (reddit_post_id, post_title, num_comments, post_author, episode_number, episode_guest, post_upvotes, post_upvote_ratio, post_upload_date, reddit_url, episode_link) VALUES (?,?,?,?,?,?,?,?,?,?,?)'
    try:
        cursor.execute(insert_statement, (episode_data['reddit_post_id'], episode_data['post_title'], episode_data['num_comments'], episode_data['post_author'], episode_data['episode_number'], episode_data['episode_guest'], episode_data['post_upvotes'], episode_data['post_upvote_ratio'], episode_data['post_upload_date'], episode_data['reddit_url'], episode_data['episode_link']))
        conn.commit()
    except sqlite3.IntegrityError:
        raise sqlite3.IntegrityError("sqlite integrity error")
    conn.close()


# In[12]:


def deEmojify(text):
    regrex_pattern = re.compile(pattern = "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags = re.UNICODE)
    return regrex_pattern.sub(r'',text)


# In[13]:


def extractPostInfo_A(post_title, num_comments, post_author, reddit_url, episode_link):
    driver.get(reddit_url)
    time.sleep(3)
    
    if post_title == '':
        post_title = driver.title
        post_title = post_title[:post_title.find(":")-1]

    if post_title.find('- ') == -1:
        episode_guest = post_title.replace("The ", "") #Include space to not replace instances of Theology, Theo Von.
        episode_guest = episode_guest.replace("Joe Rogan Experience", "")
        episode_guest = episode_guest.replace("JRE", "")
        episode_guest = episode_guest.replace("#", "")
        episode_guest = episode_guest.replace("with", "")
        episode_guest = episode_guest.replace("MMA Show", "")
        episode_guest = re.sub(r"\d+", "", episode_guest)
        
        # Remove any extra whitespace left after removal
        episode_guest = re.sub(r'\s+', ' ', episode_guest).strip()
    else:
        episode_guest = post_title[post_title.find('- ')+2:]
    
    reddit_post_id = reddit_url[43:50]
    if reddit_post_id[-1] == "/": #catching 6 character long reddit post ids
        reddit_post_id = reddit_post_id[0:-1]

    post_upload_date = driver.find_element(By.CLASS_NAME, "date")
    post_upload_date = post_upload_date.text[-11:]
    
    post_score = driver.find_element(By.CLASS_NAME, "score")
    post_upvotes = re.search(r'\d+', post_score.text).group()#post_score.text[:-21]
    #post_upvotes = int(post_upvotes.replace(',', ''))

    post_upvote_ratio = int(post_score.text[-12:-10])/100 #strong candidate for improvement

    try:
        episode_number = int(re.search(r'\d+', post_title).group())
    except:
        episode_number = ''
        
    site_table = driver.find_element(By.CLASS_NAME, "sitetable")

    post_meta = site_table.find_elements(By.TAG_NAME, "a")
    for m in post_meta:
        if 'comments' in m.text:
            num_comments = re.search(r'\d+', m.text).group()

    if post_author == '':
        tagline = site_table.find_element(By.CLASS_NAME, 'tagline').text
        post_author = tagline[tagline.find('by ')+3:]

    if episode_link == '':
        site_table_embed = driver.find_element(By.XPATH, '//*[@id="siteTable"]/div[1]')
        episode_link = site_table_embed.get_attribute('data-url')

    episode_data = {'reddit_post_id': reddit_post_id,
        'post_title': post_title,
        'num_comments': num_comments,
        'post_author': post_author,
        'episode_link': episode_link,
        'episode_number': episode_number,
        'episode_guest': episode_guest,
        'post_upvotes': post_upvotes,
        'post_upvote_ratio': post_upvote_ratio,
        'post_upload_date': post_upload_date,
        'reddit_url': reddit_url
        }

    # Append to database table
    savePosttoDB(episode_data)
    
    # Expand all comment sections and all collapsed negatives comments
    has_more_comments = True
    has_more_negative_comments = True
    
    while has_more_comments or has_more_negative_comments:
        
        lmc_list = driver.find_elements(By.CSS_SELECTOR,'[data-type="morechildren"]')
        lmc_length = len(lmc_list)
        cnc_list = driver.find_elements(By.LINK_TEXT, "[+]")
        cnc_length = len(cnc_list)
        lmc_count = 0
        cnc_count = 0

        if len(lmc_list) == 0 and len(cnc_list) == 0:
            break
        
        if len(lmc_list) == 0:
            pass#has_more_comments = False
        else:
            for lmc in lmc_list:
                lmc_count += 1
                try: #sometimes element is renamed on load? so just continue to next cycle and get new name of element.
                    load_more_button_id = "more_" + lmc.get_attribute("data-fullname")
                except:
                    continue
                message = "data-fullname: " + lmc.get_attribute("data-fullname")
                print(message)
                logger.log_message(message)
                sleep_time =  max(1, np.random.normal(3,2.5))
                message = f"Waiting for {sleep_time} seconds in lmc: {lmc_count}/{lmc_length} and cnc: {cnc_count}/{cnc_length}"
                print(message)
                logger.log_message(message)
                time.sleep(sleep_time)
                try:
                    driver.find_element(By.ID, load_more_button_id).click()
                except:
                    message = "behind a cnc"
                    print(message)
                    logger.log_message(message)
    
        if len(cnc_list) == 0:
            pass#has_more_negative_comments = False
        else:
            for cnc in cnc_list:
                cnc_count += 1
                sleep_time = max(1, np.random.normal(3,2.5))
                message = f"Waiting for {sleep_time} seconds in lmc: {lmc_count}/{lmc_length} and cnc: {cnc_count}/{cnc_length}"
                print(message)
                logger.log_message(message)
                time.sleep(sleep_time)
                try:
                    cnc.click()
                except:
                    message = "behind an lmc"
                    print(message)
                    logger.log_message(message)
                    
    # EXTRACT COMMENTS
    comments = driver.find_elements(By.CSS_SELECTOR,'[data-type="comment"]')
    # Append episode data to CSV file
    episode_title_csv = f"jre_#{episode_number}.csv"
    
    with open('episode_comments/' + episode_title_csv, 'a+', newline='', encoding='utf-8') as episode_csv:
            fieldnames = ['reddit_post_id', 'episode_number', 'comment_id', 'comment_author', 'comment_upvotes', 'comment_text', 'comment_parent']
            writer = csv.DictWriter(episode_csv, fieldnames=fieldnames)
            writer.writeheader()
    
    comment_num = len(comments)
    comment_count = 0
    for comment in comments:
        comment_count += 1
        message = f"getting comment {comment_count} of {comment_num}"
        print(message)
        logger.log_message(message)
        comment_id = comment.get_attribute('data-fullname')
        print(comment_id)
        logger.log_message(comment_id)
        comment_author = comment.get_attribute('data-author')
        if comment_author == 'AutoModerator':
            continue
    
        upvote_path = '//*[@id="thing_' + comment_id + '"]/div[2]/p'
        upvote_element = comment.find_element(By.XPATH, upvote_path)
        
        stickied_tagline = upvote_element.find_elements(By.CLASS_NAME, "stickied-tagline") #not counting moderator/stickied comments
        if stickied_tagline:
            continue
        
        comment_upvotes_text = upvote_element.find_element(By.XPATH, './/*[@class="score unvoted"]').text
        comment_upvotes = int(comment_upvotes_text[:comment_upvotes_text.find(" ")])
            
        
        comment_text_path = '//*[@id="thing_' + comment_id + '"]/div[2]/*/div/div'
        try:
            comment_text = driver.find_element(By.XPATH, comment_text_path).text.replace("\n", " ")
            comment_text = demoji.replace(comment_text, "")
        except:
            print("no comment text")
            comment_text = ""
        
        parent_location = '//*[@id="thing_' + comment_id + '"]/div[2]/ul/li[4]/a'
        try:
            comment_parent = driver.find_element(By.XPATH, parent_location)
            if comment_parent.text == 'void(0)' or comment_parent.text == 'report':
                comment_parent = ''
                #reply_depth = 0
            else:
                comment_parent = comment_parent.get_property("href")[-7:]
                #reply_depth = comment_parent + '+1'
        except:
            comment_parent = ''
    
        comment_data = [
            {'reddit_post_id': reddit_post_id,
            'episode_number': episode_number,
            'comment_id': comment_id,
            'comment_author': comment_author,
            'comment_upvotes': comment_upvotes,
            'comment_text': comment_text,
            'comment_parent': comment_parent
            }]

        print(comment_data)
        logger.log_message(comment_data)
    
        with open('episode_comments/' + episode_title_csv, 'a+', newline='', encoding='utf-8') as episode_csv:
            fieldnames = ['reddit_post_id', 'episode_number', 'comment_id', 'comment_author', 'comment_upvotes', 'comment_text', 'comment_parent']
            writer = csv.DictWriter(episode_csv, fieldnames=fieldnames)
            writer.writerows(comment_data)

    end = time.time()
    length = end - start
    message = f"JRE #{episode_number} took {length} seconds."
    print(message)
    logger.log_message(message)

    # Read and separate the header and data rows
    with open(input_file, 'r') as file:
        reader = csv.reader(file)
        header = next(reader)  # Read and store the header
        rows = list(reader)  # Read the remaining rows
    
    # Remove the first data row
    rows = rows[1:]
    
    # Write the header and remaining data back to the file
    with open(input_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)  # Write the header back
        writer.writerows(rows)  # Write the remaining rows


# In[ ]:


for index, row in df.iterrows():
    print(row.post_title, row.reddit_url)
    start = time.time()
    
    post_title = row.post_title
    num_comments = row.num_comments
    post_author = row.author
    reddit_url = row.reddit_url+'?sort=old'
    episode_link = row.episode_link

    extractPostInfo_A(post_title, num_comments, post_author, reddit_url, episode_link)


# In[ ]:


# def extractPostInfo_B(episode_number, reddit_url, post_upload_date):
#     if validators.url(reddit_url):
#         driver.get(reddit_url)
        
#         post_title = driver.title
#         post_title = post_title[:post_title.find(":")-1]

#         if post_title.find('- ') == -1:
#             episode_guest = post_title.replace("The", "")
#             episode_guest = episode_guest.replace("Joe Rogan Experience", "")
#             episode_guest = episode_guest.replace("JRE", "")
#             episode_guest = episode_guest.replace("#", "")
            
#             episode_guest = re.sub(r"d+", "", episode_guest)
            
#             # Remove any extra whitespace left after removal
#             episode_guest = re.sub(r'\s+', ' ', episode_guest).strip()
#         else:
#             episode_guest = post_title[post_title.find('- ')+2:]
            
#         reddit_post_id = reddit_url[43:49]
#         message = "reddit url: " + reddit_url 
#         print(message)
#         logger.log_message(message)
#         message = "reddit post id: " + reddit_post_id
#         print(message)
#         logger.log_message(message)
    
#         if post_upload_date == '':
#             post_upload_date = driver.find_element(By.CLASS_NAME, "date")
#             post_upload_date = post_upload_date.text[-11:]
    
#         post_score = driver.find_element(By.CLASS_NAME, "score")
    
#         post_upvotes = post_score.text[:-21]
#         post_upvotes = int(post_upvotes.replace(',', ''))
    
#         post_upvote_ratio = int(post_score.text[-12:-10])/100
    
#         # try:
#         #     episode_number = int(re.search(r'\d+', post_title).group())
#         # except:
#         #     episode_number = ''
    
#         site_table = driver.find_element(By.CLASS_NAME, "sitetable")
    
#         post_meta = site_table.find_elements(By.TAG_NAME, "a")
#         for m in post_meta:
#             if 'comments' in m.text:
#                 num_comments = re.search(r'\d+', m.text).group()
    
#         tagline = site_table.find_element(By.CLASS_NAME, 'tagline').text
#         post_author = tagline[tagline.find('by ')+3:]
    
#         site_table_embed = driver.find_element(By.XPATH, '//*[@id="siteTable"]/div[1]')
#         episode_link = site_table_embed.get_attribute('data-url')
    
#         episode_data = {'reddit_post_id': reddit_post_id,
#             'post_title': post_title,
#             'num_comments': num_comments,
#             'post_author': post_author,
#             'episode_link': episode_link,
#             'episode_number': episode_number,
#             'episode_guest': episode_guest,
#             'post_upvotes': post_upvotes,
#             'post_upvote_ratio': post_upvote_ratio,
#             'post_upload_date': post_upload_date,
#             'reddit_url': reddit_url
#             }
        
#         # Expand all comment sections and all collapsed negatives comments
#         has_more_comments = True
#         has_more_negative_comments = True
#     else:
#         # No url, no comments
#         has_more_comments = False
#         has_more_negative_comments = False
        
#         episode_data = {'reddit_post_id': None,
#             'post_title': None,
#             'num_comments': None,
#             'post_author': None,
#             'episode_link': None,
#             'episode_number': episode_number,
#             'episode_guest': reddit_url,
#             'post_upvotes': None,
#             'post_upvote_ratio': None,
#             'post_upload_date': post_upload_date,
#             'reddit_url': None
#             }
        

#     # Append to database table
#     savePosttoDB(episode_data)
    
#     while has_more_comments or has_more_negative_comments:
        
#         lmc_list = driver.find_elements(By.CSS_SELECTOR,'[data-type="morechildren"]')
#         cnc_list = driver.find_elements(By.LINK_TEXT, "[+]")
#         lmc_length = len(lmc_list)
#         cnc_length = len(cnc_list)
#         lmc_count = 0
#         cnc_count = 0
        
#         if len(lmc_list) == 0:
#             has_more_comments = False
#         else:
#             for lmc in lmc_list:
#                 lmc_count += 1
#                 load_more_button_id = "more_" + lmc.get_attribute("data-fullname")
#                 print("data-fullname: " + lmc.get_attribute("data-fullname"))
#                 sleep_time = abs(np.random.normal(7.5,2.5))
#                 print(f"Waiting for {sleep_time} seconds in lmc: {lmc_count}/{lmc_length} and cnc: {cnc_count}/{cnc_length}")
#                 time.sleep(sleep_time)
#                 try:
#                     driver.find_element(By.ID, load_more_button_id).click()
#                 except:
#                     print("behind a cnc")
    
#         if len(cnc_list) == 0:
#             has_more_negative_comments = False
#         else:
#             for cnc in cnc_list:
#                 cnc_count += 1
#                 sleep_time = abs(np.random.normal(7.5,2.5))
#                 print(f"Waiting for {sleep_time} seconds in lmc: {lmc_count}/{lmc_length} and cnc: {cnc_count}/{cnc_length}")
#                 time.sleep(sleep_time)
#                 try:
#                     cnc.click()
#                 except:
#                     print("behind an lmc")

#     if validators.url(reddit_url):
                    
#         # EXTRACT COMMENTS
#         comments = driver.find_elements(By.CSS_SELECTOR,'[data-type="comment"]')
#         # Append episode data to CSV file
#         episode_title_csv = f"jre_#{episode_number}.csv"
        
#         with open('episode_comments/' + episode_title_csv, 'a+', newline='', encoding='utf-8') as episode_csv:
#                 fieldnames = ['reddit_post_id', 'episode_number', 'comment_id', 'comment_author', 'comment_upvotes', 'comment_text', 'comment_parent']
#                 writer = csv.DictWriter(episode_csv, fieldnames=fieldnames)
#                 writer.writeheader()
        
#         comment_num = len(comments)
#         comment_count = 0
#         for comment in comments:            
#             comment_count += 1
#             print(f"getting comment {comment_count} of {comment_num}")
#             comment_id = comment.get_attribute('data-fullname')
#             print(comment_id)
#             comment_author = comment.get_attribute('data-author')
#             if comment_author == 'AutoModerator':
#                 continue
        
#             upvote_path = '//*[@id="thing_' + comment_id + '"]/div[2]/p'
#             upvote_element = comment.find_element(By.XPATH, upvote_path)
#             comment_upvotes_text = upvote_element.find_element(By.XPATH, './/*[@class="score unvoted"]').text
#             comment_upvotes = int(comment_upvotes_text[:comment_upvotes_text.find(" ")]) 
            
#             comment_text_path = '//*[@id="thing_' + comment_id + '"]/div[2]/*/div/div'
#             comment_text = driver.find_element(By.XPATH, comment_text_path).text.replace("\n", " ")
#             comment_text = demoji.replace(comment_text, "")
    
#             try:
#                 parent_location = '//*[@id="thing_' + comment_id + '"]/div[2]/ul/li[4]/a'
#                 comment_parent = driver.find_element(By.XPATH, parent_location)
#                 if comment_parent.text == 'void(0)' or comment_parent.text == 'report':
#                     comment_parent = ''
#                 else:
#                     comment_parent = comment_parent.get_property("href")[-7:]
#             except NoSuchElementException:
#                 comment_parent = ''
        
#             comment_data = [
#                 {'reddit_post_id': reddit_post_id,
#                 'episode_number': episode_number,
#                 'comment_id': comment_id,
#                 'comment_author': comment_author,
#                 'comment_upvotes': comment_upvotes,
#                 'comment_text': comment_text,
#                 'comment_parent': comment_parent
#                 }]
    
#             print(comment_data)
#             logger.log_message(comment_data)
        
#             with open('episode_comments/' + episode_title_csv, 'a+', newline='', encoding='utf-8') as episode_csv:
#                 fieldnames = ['reddit_post_id', 'episode_number', 'comment_id', 'comment_author', 'comment_upvotes', 'comment_text', 'comment_parent']
#                 writer = csv.DictWriter(episode_csv, fieldnames=fieldnames)
#                 writer.writerows(comment_data)

#     df = pd.read_csv('deleted_reddit_url.csv')
#     df = df.drop(df.index[1])
#     df.to_csv('deleted_reddit_url.csv', index=False)

#     end = time.time()
#     length = end - start
#     message = f"JRE #{episode_number} took {length} seconds."
#     print(message)
#     logger.log_message(message)
#     # input("Ready for next?")


# In[ ]:


# for index, row in df.iterrows():
#     message = row.episode_number, row.reddit_url
#     print(message)
#     logger.log_message(message)
#     start = time.time()
    
#     reddit_url = row.reddit_url
#     episode_number = row.episode_number
#     release_date = row.release_date

#     extractPostInfo_B(episode_number, reddit_url, release_date)


# In[ ]:





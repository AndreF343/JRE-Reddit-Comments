#!/usr/bin/env python
# coding: utf-8

# In[34]:


import os
import re
import nltk
import shutil
import sqlite3
import pandas as pd
from textblob import TextBlob

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.sentiment import SentimentIntensityAnalyzer


# In[35]:


#logger.setup_logger()


# In[36]:


# nltk.download("stopwords", 'vader_lexicon', "punkt", "wordnet", "punkt_tab")
stop_words = stopwords.words("english")
lemmatizer = WordNetLemmatizer()
sia = SentimentIntensityAnalyzer()


# In[45]:


def tokenize(text):
    # Todo: normalize case and remove punctuation
    text = re.sub(r"[^a-zA-Z0-9]", " ", text.lower())
    text = re.sub(r'http\S+|www\.\S+', '', text)

    tokens = word_tokenize(text)

    # Todo: lemmatize and remove stop words
    tokens = [lemmatizer.lemmatize(t) for t in tokens if t not in stop_words]
    
    return str(tokens)


# In[46]:


directory = r"C:\Users\andre\OneDrive\Desktop\JRReader\episode_comments\\"
for filename in os.listdir(directory):
    
    print(filename)
    source_file = directory+filename
    comments_df = pd.read_csv(source_file)

    
    if len(comments_df.episode_number) == 0:
        message = "no post data"
        print(message)
        continue
    episode_number = comments_df.episode_number[0]
    print(episode_number)
    
    comments_df['comment_id'] = comments_df['comment_id'].str[3:]

    comments_df['comment_depth'] = 0
    
    # Function to calculate reply depth
    def calculate_comment_depth(row):
        if row['comment_parent'] == 0:
            return 0
        else:
            parent_depth = comments_df.loc[comments_df['comment_id'] == row['comment_parent'], 'comment_depth']
            return parent_depth.values[0] + 1 if not parent_depth.empty else 0
    
    # Iterate through the DataFrame to update comment_depth in place
    for index, row in comments_df.iterrows():
        comments_df.at[index, 'comment_depth'] = calculate_comment_depth(row)

    comments_df['sentiment'] = comments_df['comment_text'].apply(lambda x: sia.polarity_scores(str(x))['compound'])
    comments_df['tokens'] = comments_df['comment_text'].apply(lambda x: tokenize(str(x)))
    # comments_df['tokens_joined'] = comments_df['tokens_list'].apply(lambda x: ' '.join(x))

    # comments_df.tokens_list = comments_df.tokens_list.astype(str) #convert to string to store list data

    db_table_name = f"JRE_{episode_number}_Processed"
    
    conn = sqlite3.connect(r"C:\Users\andre\OneDrive\Desktop\JRReader\datadump\joerogan.db")
    comments_df.to_sql(db_table_name, conn, method='multi', if_exists='fail', index=False)
    
    conn.close()

    destination_folder = r"C:\Users\andre\OneDrive\Desktop\JRReader\episode_processed\\"
    
    # Move the file
    try:
        shutil.move(source_file, destination_folder)
        print(f"File moved to {destination_folder}")
    except FileNotFoundError:
        print("Source file or destination folder not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


    # with open('nightly_transformed_comments/' + db_table_name + '_transformed', 'a+', newline='', encoding='utf-8') as transformed_csv:
    #             fieldnames = ['reddit_post_id', 'episode_number', 'comment_id', 'comment_author', 'comment_upvotes', 'comment_text', 'comment_parent', 'reply_depth', 'sentiment', 'tokens_list', 'tokens_joined']
    #             writer = csv.DictWriter(transformed_csv, fieldnames=fieldnames)
    #             writer.writeheader()


# In[ ]:





# In[ ]:





# In[ ]:





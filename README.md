# Joe Rogan Experience Comment Sentiment Analysis Project
![image](https://github.com/user-attachments/assets/61fd3dfc-532a-4cc6-8401-18831a30bdd1) 
Check it out at http://54.169.204.212:8050/

## Table of Contents

1. [Introduction](#introduction)
2. [Process](#process)
3. [Features](#features)
4. [Demo](#demo)
5. [Conclusion](#conclusion)
6. [Challenges/To-Do](#challenges/to-do)

## Introduction
I love listening to podcasts, and for the better part of the last decade, I enjoyed the Joe Rogan Experience (JRE). At its best, the podcast was funny, insightful, and featured fascinating guests. However, over time, my enthusiasm has waned—in my opinion, Joe seems less curious and humble. This led me to wonder if others felt the same way, sparking my interest in this project: analyzing comments from the Joe Rogan subreddit to better understand how others perceive the evolution of the podcast.

Over the last several weeks, I've developed a set of scripts to scrape Reddit comments related to JRE episodes, and it's been quite a journey. Along the way, I practiced and expanded on many useful skills in scraping data, deploying scripts, analyzing text, and building visualizations. Below is an overview of the process, features, and some of the challenges I faced.

## Process
1. **Get URLs**: Developed custom scripts to find relevant posts on the r/joerogan subreddit that pertain specifically to JRE episodes.
2. **EC2 Deployment**: The entire pipeline runs on an Amazon EC2 instance, with automation that allows the process to run without manual intervention.
3. **Scrape into Landing Zone**: I used Selenium to bypass strong bot-detection defenses and to simulate human behavior to scrape data into a landing zone for further processing.
4. **Nightly Transform & Backups**: Data scraped from Reddit is backed up nightly, ensuring data consistency and minimizing risk of loss.
5. **Proxy Service**: Because Reddit immediately blocked AWS IPs, I routed my requests through a proxy service (SmartProxy), enabling access while maintaining anonymity.

![image](https://github.com/user-attachments/assets/7a21b8a5-29ad-48fd-b9aa-c069b174b50a)

## Features
- **NLP Analysis**: Implemented VADER sentiment analysis to gauge the general sentiment of comments related to JRE episodes.
- **AWS Infrastructure**: Utilized Amazon's EC2 for cloud computing, deploying scripts that automate data collection and ensure robust error handling.
- **Dockerized Environment**: Dockerized the entire application, making it easy to deploy and run anywhere without additional setup.
- **OpenAI Summarization**: Integrated an API connection to OpenAI to summarize Reddit posts, providing concise insights into lengthy comment threads.

![image](https://github.com/user-attachments/assets/7baed749-4825-4d44-a81b-aa0105b6b1e4)

## Demo

To build and deploy the Dockerized dashboard, follow these steps:

1. Download the repository.
2. Navigate to the project folder.
3. Build the Docker image: `docker build -t my_dash_app .`
4. Run the container: `docker run -p 8050:8050 my_dash_app`

## Conclusion
Pending addtional data points.

## Challenges/To-Do
- **Complexity of Scraping**: Dealing with Reddit's bot-detection and AWS blocking access required significant effort to bypass restrictions, involving Selenium, proxies, and delay strategies.
- **Rate Limits and Server Blocks**: Managing Reddit’s rate limits and working around server blocks were challenging and time-consuming.
- **Analysis Incomplete**: Due to the time investment in setting up infrastructure and data collection, I didn't have the opportunity to fully analyze the scraped data. Future iterations could involve clustering comments to identify common themes, diving deeper into sentiment trends over time, and exploring which guests receive the most positive or negative feedback.
- **Dashboarding**: Although I learned how to build a dashboard to visualize my results, there’s room for further enhancement to make it more visually appealing and interactive.


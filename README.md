# Joe Rogan Experience Comment Sentiment Analysis Project
![image](https://github.com/user-attachments/assets/61fd3dfc-532a-4cc6-8401-18831a30bdd1) 
Check it out at http://54.169.204.212:8050/

## Table of Contents

1. [Introduction](#introduction)
2. [Process](#process)
3. [Features](#features)
4. [Demo](#demo)
5. [Conclusion](#conclusion)
6. [To-Do](#to-do)

## Introduction
I love listening to podcasts, and for the better part of the last decade, I enjoyed the Joe Rogan Experience (JRE). At its best, the podcast was funny, silly, and featured fascinating guests. However, over time, my enthusiasm has waned—in my opinion, Joe has become less curious and humble. This led me to wonder if others felt the same way, sparking my interest in this project: analyzing comment sentiment from the Joe Rogan subreddit to better understand how others perceive the evolution of the podcast over time.

Over the last several weeks, I've developed a set of scripts to scrape Reddit comments related to JRE episodes. I have deployed them on an AWS EC2 instance with a local SQLite database and a Dash-by-Plotly dashboard to represent the data that is refreshed nightly with the latest batch of data points.

This repository contains a dockerized demo of the dashboard that displays some basic stats on the reddit posts and comments. Instructions on how to deploy the dashboard can be found in the Demo section. I have also included some sample scripts that I used to scraping data and automating certain tasks (nightly backups, transforms, etc.), however they are just for show and have not been configured to be runnable.

## Process
1. **Get Reddit URLs**: Developed custom scripts to find relevant posts on the r/joerogan subreddit that pertain specifically to JRE episodes.
2. **EC2 Deployment**: The entire pipeline runs on an Amazon EC2 instance, with automation that allows the process to run without manual intervention, and alerts for errors and cpu overutilization.
3. **Proxy Service**: Because Reddit immediately blocked AWS IPs, I routed my requests through a proxy service (SmartProxy).
4. **Nightly Transform & Backups**: Data scraped from Reddit is backed up nightly in various formats, ensuring data consistency and minimizing risk of loss.
5. **Display Data**: Data is read from SQLiteDB and displayed on a public dashboard.

![image](https://github.com/user-attachments/assets/7a21b8a5-29ad-48fd-b9aa-c069b174b50a)

## Features
- **NLP Analysis**: Implemented VADER sentiment analysis to gauge the general sentiment of comments related to JRE episodes.
- **AWS Infrastructure**: Utilized Amazon's EC2 for cloud computing, deploying scripts that automate data collection and ensure robust error handling.
- **Dockerized Environment**: Dockerized the entire application, making it easy to deploy and run anywhere without additional setup.
- **OpenAI Summarization**: Integrated an API connection to OpenAI to summarize Reddit posts, providing concise insights into lengthy comment threads.

![image](https://github.com/user-attachments/assets/7baed749-4825-4d44-a81b-aa0105b6b1e4)

## Demo

If Docker is not installed. Install it for your OS [here](https://docs.docker.com/engine/install/).
To build and deploy the Dockerized dashboard, follow these steps:

1. Download the repository.
2. Navigate to the project folder.
3. Build the Docker image: `docker build -t my_dash_app .`
4. Run the container: `docker run -p 8050:8050 my_dash_app`

## Conclusion
_Pending addtional data points._

## To-Do
_coming soon_


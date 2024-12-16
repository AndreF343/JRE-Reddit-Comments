<div align="center"><h1>Joe Rogan Experience Comment Sentiment Analysis Project</h1></div>

![image](https://github.com/user-attachments/assets/61fd3dfc-532a-4cc6-8401-18831a30bdd1)

<div align="center">
  <a href="https://jrdashboard.com/">jrdashboard.com</a>
</div>

<div align="center">
<h1>Table of Contents</h1>
</div>

1. [Introduction](#introduction)
2. [Process](#process)
3. [Features](#notable-features--challenges)
4. [Demo](#demo)
5. [Conclusion](#conclusion)
6. [To-Do](#would-do)
7. [Project Wrap-Up](#project-wrap-up)

<div align="center">
<h1>Introduction</h1>
</div>
I used to love listening to the Joe Rogan Experience (JRE) podcast but over time I find Joe to become less curious, less humble, and more like the people he used to make fun of. I wanted to find out if other people felt the same way, so I decided to collect and analyze the sentiment of comment data on reddit posts pertaining to his podcast episodes.

To achieve this goal I wrote scripts to:
- pull the comment data from these posts.
- transform and store this data in a SQL database.
- display the data on a dashboard.

Initially this was supposed to be a data analysis project, but due to the challenges in data collection (specifically a lack of useable API), more and more of my time was spent in engineering the scraping scripts and remote deployment processes.

This repository contains a sample dataset and a dockerized demo of the dashboard that displays some basic stats on the reddit posts and comments. Instructions on how to deploy the dashboard can be found in the Demo section. I have also included some sample scripts that I used to scraping data and automating certain tasks (nightly backups, transforms, etc.).

<div align="center">
<h1>Process</h1>
</div>
<p align="center">
  <img src="https://github.com/user-attachments/assets/501e4893-8567-45d7-8696-9115b8952306" alt="app_component_diagram_updated">
</p>


1. **Get Reddit URLs**: Developed custom scripts to find relevant posts on the r/joerogan subreddit that pertain specifically to JRE episodes. Pulled data such as post [author, score, data, title] and comment [author, score, comment text]

2. **EC2 Deployment**: The entire pipeline runs on an Amazon EC2 instance, with automation that allows the process to run without manual intervention, and alerts for errors and cpu overutilization.

3. **Nightly Transform & Backups**: Data scraped from Reddit is backed up nightly, ensuring data consistency and minimizing risk of loss. After raw data and database backups, cleanings and transformations are performed to engineer features such as comment [sentiment, comment_depth, tokens]

4. **Display Data**: Nightly, new data is read from DB and displayed on a publicly accessible dashboard.

![image](https://github.com/user-attachments/assets/7a21b8a5-29ad-48fd-b9aa-c069b174b50a)

<div align="center">
<h1>Notable Features & Challenges</h1>
</div>

- **AWS IP Ban**: Because Reddit immediately blocked AWS IPs, I routed my requests through a residential proxy using [SmartProxy](https://smartproxy.com/).
  
- **Reddit Anti-Bot Measures**: Multiple layers of randomization needed to be added to rate-limiting algorithm in order to get passed Reddit's anti-bot defenses. In short, randomization needed to appear 'normal' over time, and not 'uniform'. This significantly reduced the rate at which data was able to be collected.
  
- **AWS Infrastructure**: Utilized Amazon's EC2 for cloud computing, deploying scripts that automate data collection and ensure robust error handling.
  
- **Dockerized Environment**: Dockerized the entire application, making it easy to deploy and run anywhere without additional setup.
  
- **OpenAI Summarization**: Integrated an API connection to OpenAI to summarize Reddit posts, providing concise insights into lengthy comment threads.
  
- **Deleted/Missing Post Data**: Over time some users have deleted their posts or accounts, and sometimes the episodes were themselves removed for various reasons. Additionally, the first ~300 episodes are missing from the JRE catalog. When a user deletes a post or the source is removed, that does not remove the post from existence. It just removes them from search results. Scripts were developed to find these posts through google searches. But strict bot detection from google made this approach very time-consuming.
  
- **Dynamic Wordcloud**: The worldcloud displayed on the homepage is updated nightly taking into account the latest batch of post data.

![image](https://github.com/user-attachments/assets/7baed749-4825-4d44-a81b-aa0105b6b1e4)

<div align="center">
<h1>Demo</h1>
</div>

If Docker is not installed. Install it for your OS [here](https://docs.docker.com/engine/install/).
To build and deploy the Dockerized dashboard, follow these steps:

1. Download the repository.
2. Navigate to the project folder.
3. Build the Docker image: `docker build -t my_dash_app .`
4. Run the container: `docker run -p 8050:8050 my_dash_app`

<div align="center">
<h1>Conclusion</h1>
</div>
Initially I'd wanted to perform more complex analysis on the data, but collecting the data became so time consuming that I think there are diminishing returns on continuing work on this particular hobby project. The scraper ran for about 1 month and was able to analyze over 1000+ posts.

The average sentiment score of JRE reddit posts was `0.13` in February 2013. This fell to `0.07` in May of 2024. On a scale of 1 (positive):-1 (negative), this is a negligible amount that doesn't demonstrate much change in sentiment.

The model used to calculated the sentiment score was VADER which while trained on twitter data, failed to perform well on reddit comment data, often missing sarcasm and other internet-isms.

To see other notable data points, do visit the [dashboard](https://jrdashboard.com/).

<div align="center">
<h1>Would-Do</h1>
</div>

- If you were paying me to work on this, I'd look into analyzing the topic-specific sentiment of comments. In other words, determine the average sentiment score of specific topics discussed in the comments. For example, since Trump is a frequently mentioned topic on the JRE, the sentiment score specific to Trump could be calculated.

- There are over 500 missing posts that were deleted for one reason or another. I think some of the most interesting questions could be posed against deleted/missing posts. Which guest was the most censored/removed from JRE history? Were there specific fields that had more post deletions than others (example. eye-tests indicated that posts related to politics were being removed at a higher rate than others)?

<div align="center">
<h1>Project Wrap-Up</h1>
</div>
As of 16<sup>th</sup> December 2024 I'm most likely done developing this project. The last thing I did was secure the dashboard with cloudflare so that traffic to and from my dashboard is properly encrypted and people aren't immediately scared to continue. It's the first project in my portfolio as I look for a new job in data and I'm very proud of it. It demonstrates my capacity:


- to use Python, SQL and Databases, Docker and cloud based tools as found in AWS.
- to create an automated ETL pipeline.
- to use AI tools by integration with OpenAI.
- to go out and get data where it might not be readily available and to overcome challenges as they arise (lack of api, ip blocking, bot detectors).
- to follow-through on a goal and deliver a viable product.

I'll be starting my next project focused on training a computer-vision based model that can identify and count actions difficult for a humans to perceive. Links to come shortly!

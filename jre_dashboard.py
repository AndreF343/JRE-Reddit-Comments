#!/usr/bin/env python
# coding: utf-8

# In[6]:


import os
import re
import ast
import dash
import base64
import sqlite3
import requests
import wordcloud
import pandas as pd
from dash import html
import seaborn as sns
from io import BytesIO
from openai import OpenAI
from dash import dcc, html
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output


# In[73]:


# Set OpenAI API key
oai_client = OpenAI(
    api_key = ''
    # api_key=os.environ.get("OPENAI_API_KEY"),  # This is the default and can be omitted
)


# In[8]:


conn = sqlite3.connect(r"joerogan.db")

post_df = pd.read_sql("SELECT * FROM reddit_posts", conn)

df_list = []

cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%Processed%';")
tables = cursor.fetchall()

posts_scanned = 0
for table_name in tables:
    table_name = str(table_name[0])
    if table_name != 'reddit_posts':
        # if posts_scanned > 10:
        #     break
        # print(table_name)
        posts_scanned += 1
        table = pd.read_sql_query("SELECT * from %s" % table_name, conn)
        df_list.append(table)

final_df = pd.concat(df_list)
conn.close()


# In[9]:


# Clean column names by stripping whitespace and converting to lowercase
final_df.columns = final_df.columns.str.strip().str.lower()
post_df.columns = post_df.columns.str.strip().str.lower()

# Ensure episode_number is of the same type in both DataFrames
final_df = final_df[pd.to_numeric(final_df['episode_number'], errors='coerce').notna()] #converts non-numeric entries to NaN
final_df.loc[:, 'episode_number'] = final_df['episode_number'].astype(int)

post_df['episode_number'] = post_df['episode_number'].astype(int)

# Merge selected columns from post_df to final_df based on episode_number
df_merged = final_df.merge(post_df[['episode_number', 'episode_guest', 'post_upload_date', 'post_upvotes', 'post_upvote_ratio', 'post_title']], 
                            on='episode_number', how='left')


# In[10]:


df_merged = df_merged[~df_merged.index.duplicated(keep='first')]

df_merged.comment_upvotes = df_merged.comment_upvotes.astype(int)
df_merged.episode_number = df_merged.episode_number.astype(int)

# Ensure 'post_upload_date' is in datetime format
try:
    df_merged['post_upload_date'] = pd.to_datetime(df_merged['post_upload_date'], format='%d/%m/%Y', errors='raise')
except:
    df_merged['post_upload_date'] = pd.to_datetime(df_merged['post_upload_date'], format='%d %b %Y', dayfirst=True, errors='raise')


# In[11]:


df_merged.info()


# In[12]:


# Calculate Metrics
highest_upvoted_post = post_df.loc[post_df['post_upvotes'].idxmax()]
lowest_upvoted_post = post_df.loc[post_df['post_upvotes'].idxmin()]

# Refactored to only include posts with 100 or more upvotes and more than 100 comments
lowest_upvote_ratio_post = post_df.loc[post_df[(post_df['post_upvotes'] >= 100) & (post_df['num_comments'] > 100)]['post_upvote_ratio'].idxmin()]

highest_voted_comment = df_merged.loc[df_merged['comment_upvotes'].idxmax()]
lowest_voted_comment = df_merged.loc[df_merged['comment_upvotes'].idxmin()]

most_frequent_guests = post_df['episode_guest'].value_counts().head(3)

highest_sentiment_guest = df_merged.groupby('episode_guest')['sentiment'].mean().idxmax()
lowest_sentiment_guest = df_merged.groupby('episode_guest')['sentiment'].mean().idxmin()
highest_sentiment_score = df_merged.groupby('episode_guest')['sentiment'].mean().max()
lowest_sentiment_score = df_merged.groupby('episode_guest')['sentiment'].mean().min()


# In[13]:


# Precompute values to improve performance
current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
unique_posts_count = len(df_merged['reddit_post_id'].unique())
total_comments_count = len(df_merged)


# In[26]:


# Sentiment Plot Function
def create_sentiment_plot():
    df_sentiment_per_post = df_merged.groupby('reddit_post_id')['sentiment'].mean().reset_index()
    df_sentiment_with_date = df_merged[['reddit_post_id', 'post_upload_date', 'post_title']].drop_duplicates()
    df_sentiment_per_post = df_sentiment_per_post.merge(df_sentiment_with_date, on='reddit_post_id', how='left')
    df_sentiment_per_post = df_sentiment_per_post.sort_values(by='post_upload_date')
    df_sentiment_per_post['rolling_avg_sentiment'] = df_sentiment_per_post['sentiment'].rolling(window=60, center=True).mean()
    
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df_sentiment_per_post['post_upload_date'], y=df_sentiment_per_post['sentiment'],
                             fill='tozeroy', mode='lines', name='Average Sentiment per Post',
                             text=df_sentiment_per_post['post_title'], hovertemplate='Post Title: %{text}<br>Average Sentiment: %{y:.2f}<extra></extra>'))
    
    # Add running average sentiment as a line chart
    fig.add_trace(go.Scatter(x=df_sentiment_per_post['post_upload_date'], y=df_sentiment_per_post['rolling_avg_sentiment'],
                             mode='lines', name='Rolling Average Sentiment', line=dict(color='red')))
    fig.update_layout(title='Rolling Average Sentiment Per Post Over Time',
                      xaxis_title='Post Upload Date',
                      yaxis_title='Average Sentiment',
                      template='plotly_dark',
                      xaxis_rangeslider_visible=True)
    return fig

# Word Cloud Function
def create_word_cloud():
    # text = ' '.join(df_merged['comment_text'].dropna().values)
    # text = re.sub(r'\bs\b', '', text) # Remove all instances of the word "s" (standalone)
    text = ' '.join(
        ' '.join(ast.literal_eval(tokens)) for tokens in df_merged['tokens'].dropna().values
    )
    wc = wordcloud.WordCloud(width=800, height=400, background_color='black', colormap='Set2').generate(text)
    img = BytesIO()
    wc.to_image().save(img, format='PNG')
    encoded_image = base64.b64encode(img.getvalue()).decode()
    return 'data:image/png;base64,{}'.format(encoded_image)

# Load Images
with open(r"joeroganbackground.jpg", "rb") as image_file:
    joe_background_image = base64.b64encode(image_file.read()).decode()

# Function to search Wikipidia for guest images
def get_guest_images(guests):
    guest_images = {}

    for guest in guests:
        try:
            # Step 1: Search Wikipedia for the guest
            search_url = f"https://en.wikipedia.org/wiki/{quote(guest)}"
            response = requests.get(search_url)
            response.raise_for_status()
            
            # Step 2: Parse the page with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Step 3: Find the main infobox image
            infobox = soup.find('table', {'class': 'infobox'})
            if infobox:
                image_tag = infobox.find('img')
                if image_tag:
                    image_url = f"https:{image_tag['src']}"
                    guest_images[guest] = image_url
                else:
                    guest_images[guest] = ''  # No image found
            else:
                guest_images[guest] = ''  # No infobox found
        
        except requests.exceptions.RequestException:
            # Handle any request errors (e.g., guest page not found)
            guest_images[guest] = ''

    return guest_images

# # Get images for most frequent guests
most_frequent_guest_images = get_guest_images(most_frequent_guests.index)

# Sentiment Bubble Chart Function
def create_bubble_chart():
    post_metrics = df_merged.groupby('reddit_post_id').agg({
        'post_upload_date': 'first',
        'post_upvotes': 'first',
        'sentiment': 'mean',
        'comment_id': 'count',
        'post_title': 'first'        
    }).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=post_metrics['post_upload_date'],
        y=post_metrics['post_upvotes'],
        mode='markers',
        marker=dict(
            size=post_metrics['comment_id']/100,
            color=post_metrics['sentiment'],
            colorscale='RdYlGn',
            showscale=True,
            opacity=0.9
        ),
        text=post_metrics['post_title'],
        hoverinfo='text'
    ))
    fig.update_layout(
        title='Post Upvotes Over Time',
        xaxis_title='Post Upload Date',
        yaxis_title='Post Upvotes',
        template='plotly_dark',
        annotations=[
            dict(
                xref='paper',
                yref='paper',
                x=1.05,
                y=1.05,
                showarrow=False,
                text='Bubble size represents the number of comments. Color represents the sentiment.',
                font=dict(size=10, color='white'),
                align='left'
            )
        ]
    )
    return fig

def create_card(title, content, outline=True, class_name="mb-4 shadow-lg rounded", style={"border": "1px solid #ddd", "padding": "1rem"}):
    return dbc.Card(
        dbc.CardBody(content),
        outline=outline,
        className=class_name,
        style=style
    )

# Ensure that the app stops running when the script is interrupted
def release_port(port=8050):
    try:
        os.system(f"fuser -k {port}/tcp")
    except Exception as e:
        print(f"Error releasing port {port}: {e}")


# In[69]:


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
app.title = "JRE Reddit Post Dashboard"

app.layout = dbc.Container([
    # Header Section
    dbc.Container(
        [
            html.H1("JRE Reddit Post Dashboard", style={'textAlign': 'center', 'color': 'mustard', 'fontWeight': 'bold'}),
            html.P(f"{current_datetime} - {unique_posts_count} posts scanned, {total_comments_count} comments scraped", style={'fontSize': '12px', 'textAlign': 'center', 'fontStyle': 'italic', 'color': 'lightgray'})
        ],
        fluid=True,  # Makes the header full-width
        style={'padding-top': '20px'}
    ),
    
    # Dropdown Section
    dbc.Container(
        [
            dbc.Row(
                html.P(
                    "Please select a post from the dropdown below to view more details. Press backspace in the dropdown to return to home",
                    className="text-muted",
                    style={"fontSize": "1rem", "margin-bottom": "10px"}
                ),
            ),
            dcc.Dropdown(
                id='post-dropdown',
                options=[{'label': title, 'value': title} for title in post_df['post_title']],
                placeholder="Select a Post",
                style={'margin-bottom': '20px'}
            )
        ],
        fluid=True
    ),
    
    # Home Content Section
    dbc.Container(
        html.Div(id='home-content', children=[
            dbc.Row([
                dbc.Col(
                    dcc.Graph(id='sentiment-plot', figure=create_sentiment_plot()),
                    width=8
                ),
                dbc.Col([
                    html.Div([
                        html.Img(id='word-cloud', src=create_word_cloud(), style={'width': '100%', 'object-fit': 'contain', 'flex-grow': '1', 'margin-bottom': '10px', 'flex': '1'}),
                        html.Img(id='joe-background', src='data:image/jpeg;base64,{}'.format(joe_background_image), style={'width': '100%', 'object-fit': 'contain', 'flex-grow': '1', 'flex': '1'})
                    ], style={'height': '100%', 'display': 'flex', 'flex-direction': 'column', 'justify-content': 'space-between'})

                ], width=4, style={'display': 'flex', 'flex-direction': 'column', 'height': '100%'})
            ], className="mb-4"),
            
            # Restoring the removed rows and cards
            dbc.Row([
                dbc.Col(
                    create_card(
                        "Highest Upvoted Post",
                        [
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        html.H5("Highest Upvoted Post", className="text-success", style={'textAlign': 'center'}),
                                        html.P(
                                            f"{highest_upvoted_post['post_title']}",
                                            className="card-text font-weight-bold",
                                            style={'textAlign': 'center'}
                                        ),
                                        html.Div(
                                            [
                                                html.Span(
                                                    [html.Strong("Upvotes: "),
                                                     html.Span(f" {highest_upvoted_post['post_upvotes']}"),
                                                     html.Span(" ", style={'margin-right': '20px'})],
                                                    className="d-inline-flex align-items-center"
                                                )
                                            ],
                                            style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}
                                        )
                                    ], className="mb-3")
                                ], width=6),
                                dbc.Col([
                                    html.Div([
                                        html.H5([html.Span("Lowest "), html.Span("Ratio", style={'text-decoration': 'underline', 'font-weight': 'bold'}), html.Span(" Post")], className="text-danger", style={'textAlign': 'center'}),
                                        html.P(
                                            f"{lowest_upvote_ratio_post['post_title']}",
                                            className="card-text font-weight-bold",
                                            style={'textAlign': 'center'}
                                        ),
                                        html.Div(
                                            [
                                                html.Span(
                                                    [html.Strong("Upvotes: "),
                                                     html.Span(f" {lowest_upvote_ratio_post['post_upvotes']}"),
                                                     html.Span(" ", style={'margin-right': '20px'})],
                                                    className="d-inline-flex align-items-center"
                                                ),
                                                html.Span(
                                                    [html.Strong("Ratio:"),
                                                     html.Span(f" {lowest_upvote_ratio_post['post_upvote_ratio']*100:.2f}%")],
                                                    className="d-inline-flex align-items-center"
                                                )
                                            ],
                                            style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}
                                        )
                                    ])
                                ], width=6),
                            ])
                        ]
                    ),
                    width=6
                ),
                
                dbc.Col(
                    create_card(
                        "Highest Voted Comment",
                        [
                            html.Div([
                                html.H5("Highest Voted Comment", className="text-success", style={'textAlign': 'center'}),
                                html.P(
                                    f"“{highest_voted_comment['comment_text']}”",
                                    className="card-text font-weight-bold",
                                    style={"fontStyle": "italic", "marginLeft": "20px", 'textAlign': 'center'}
                                ),
                                html.Div(
                                    [
                                        html.Span(
                                            [html.Strong("Upvotes: "),
                                             html.Span(f" {highest_voted_comment['comment_upvotes']}"),
                                             html.Span(" ", style={'margin-right': '20px'})],
                                            className="d-inline-flex align-items-center"
                                        ),
                                        html.Span(
                                            [html.Strong("Post: "),    
                                             html.Span(f" {highest_voted_comment['post_title']}")],
                                            className="d-inline-flex align-items-center"
                                        )
                                    ],
                                    style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}
                                )
                            ], className="mb-3"),
                            html.Div([
                                html.H5("Lowest Voted Comment", className="text-danger", style={'textAlign': 'center'}),
                                html.P(
                                    f"“{lowest_voted_comment['comment_text']}”",
                                    className="card-text font-weight-bold",
                                    style={"fontStyle": "italic", "marginLeft": "20px", 'textAlign': 'center'}
                                ),
                                html.Div(
                                    [
                                        html.Span(
                                            [html.Strong("Upvotes: "),
                                             html.Span(f" {lowest_voted_comment['comment_upvotes']}"),
                                             html.Span(" ", style={'margin-right': '20px'})],
                                            className="d-inline-flex align-items-center"
                                        ),
                                        html.Span(
                                            [html.Strong("Post: "),
                                             html.Span(f" {lowest_voted_comment['post_title']}")],
                                            className="d-inline-flex align-items-center"
                                        )
                                    ],
                                    style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}
                                )
                            ])
                        ]
                    ),
                    width=6
                ),
            ], className="mb-4"),

            dbc.Row([
                dbc.Col(
                    create_card(
                        "Most Frequent Guests",
                        [
                            html.H5("Most Frequent Guests", className="card-title text-primary", style={'textAlign': 'center'}),
                            html.Hr(),
                            html.Div(  # Wrapper div for centering the whole list
                                html.Ul(
                                    [
                                        html.Li(
                                            html.Div(
                                                [
                                                    html.Span(
                                                        f"{index + 1}",
                                                        style={
                                                            'fontSize': '24px',
                                                            'fontWeight': 'bold',
                                                            'marginRight': '10px'
                                                        }
                                                    ),
                                                    html.Img(
                                                        src=most_frequent_guest_images.get(guest, ''),
                                                        style={'height': '50px', 'margin-right': '10px', 'display': 'inline-block'}
                                                    ) if most_frequent_guest_images.get(guest, '') else html.Div(style={'width': '50px', 'height': '50px', 'margin-right': '10px'}),
                                                    html.Span(f" {guest} ({most_frequent_guests[guest]} appearances)")
                                                ],
                                                style={'display': 'flex', 'align-items': 'center', 'textAlign': 'left', 'margin-bottom': '10px'}
                                            ),
                                            style={'list-style-type': 'none', 'margin-bottom': '10px'}
                                        )
                                        for index, guest in enumerate(most_frequent_guests.index)
                                    ],
                                    style={'padding': '0', 'margin': '0'}  # Removed 'textAlign': 'center' here
                                ),
                                style={'display': 'flex', 'justify-content': 'center'}  # Centers the entire list
                            )
                        ]
                    )
                , width=6),

                
                dbc.Col(
                    create_card(
                        "Highest Sentiment Guest",
                        [
                            html.Div([
                                html.H5("Highest Sentiment Guest", className="text-success", style={'textAlign': 'center'}),
                                html.Div(
                                    [
                                        html.Img(
                                            src=get_guest_images([highest_sentiment_guest]).get(highest_sentiment_guest, ''),
                                            style={'height': '50px', 'margin-right': '10px', 'display': 'inline-block'}
                                        ) if get_guest_images([highest_sentiment_guest]).get(highest_sentiment_guest, '') else html.Div(style={'width': '50px', 'height': '50px', 'margin-right': '10px'}),
                                        html.Div(
                                            [
                                                html.Span(
                                                    f" {highest_sentiment_guest}",
                                                    className="card-text font-weight-bold",
                                                    style={'margin-right': '10px'}
                                                ),
                                                html.Span(
                                                    [html.Strong("Sentiment: "),    
                                                     html.Span(f" {highest_sentiment_score:.2f}")],
                                                    className="d-inline-flex align-items-center"
                                                )
                                            ],
                                            style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}
                                        )
                                    ],
                                    style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}
                                )
                            ], className="mb-3"),
                            html.Div([
                                html.H5("Lowest Sentiment Guest", className="text-danger", style={'textAlign': 'center'}),
                                html.Div(
                                    [
                                        html.Img(
                                            src=get_guest_images([lowest_sentiment_guest]).get(lowest_sentiment_guest, ''),
                                            style={'height': '50px', 'margin-right': '10px', 'display': 'inline-block'}
                                        ) if get_guest_images([lowest_sentiment_guest]).get(lowest_sentiment_guest, '') else html.Div(style={'width': '50px', 'height': '50px', 'margin-right': '10px'}),
                                        html.Div(
                                            [
                                                html.Span(
                                                    f" {lowest_sentiment_guest}",
                                                    className="card-text font-weight-bold",
                                                    style={'margin-right': '10px'}
                                                ),
                                                html.Span(
                                                    [html.Strong("Sentiment: "),
                                                     html.Span(f" {lowest_sentiment_score:.2f}")],
                                                    className="d-inline-flex align-items-center"
                                                )
                                            ],
                                            style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}
                                        )
                                    ],
                                    style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}
                                )
                            ])
                        ]
                    )
                , width=6),
            ], className="mb-4"),

            dbc.Row([
                dbc.Col([dcc.Graph(id='bubble-chart', figure=create_bubble_chart())])], className="mb-4", style={'justify-content': 'center', 'width': '100%'}),
        ]),
        fluid=True,  # Makes the home-content section full-width
        style={'backgroundColor': '#1b1f38'}
    ),
    
    # Post-Specific Content Section
    dbc.Container(
        html.Div(id='post-specific-content', style={'display': 'none'}),
        fluid=True
    )
], fluid=True, style={'backgroundColor': '#1b1f38', 'overflowX': 'hidden'})  # Top-level container to make the whole app fluid


# In[70]:


@app.callback(
    [Output('home-content', 'style'),
     Output('post-specific-content', 'style'),
     Output('post-specific-content', 'children')],
    [Input('post-dropdown', 'value')]
)
def update_post_specific_content(selected_post_title):
    if not selected_post_title:
        return {'display': 'block'}, {'display': 'none'}, []

    # Filter the DataFrame for the selected post title
    selected_post_df = df_merged[df_merged['post_title'] == selected_post_title]

    # Get highest and lowest upvoted comments
    highest_voted_comment = selected_post_df.loc[selected_post_df['comment_upvotes'].idxmax()]
    lowest_voted_comment = selected_post_df.loc[selected_post_df['comment_upvotes'].idxmin()]

    # Get highest and lowest sentiment comments
    highest_sentiment_comment = selected_post_df.loc[selected_post_df['sentiment'].idxmax()]
    lowest_sentiment_comment = selected_post_df.loc[selected_post_df['sentiment'].idxmin()]

    # Summarize comments using OpenAI API
    comments_text = ' '.join(
        selected_post_df[selected_post_df['comment_depth'] == 0]
        .sort_values(by='comment_upvotes', ascending=False)
        .head(10)['tokens']
        .tolist())
    try:
        response = oai_client.chat.completions.create(
            messages = [
                {
                    "role": "user",
                    "content": f"Summarize the following comments: {comments_text}",  # Limiting to first 3000 characters
                    "max_completion_tokens": "50"
                }
            ],
            model="gpt-4o-mini"
        )
        # comments_summary = response.choices[0].text.strip()
        comments_summary = response.choices[0].message.content
    except Exception as e:
        comments_summary = f"Error summarizing comments: {e}"

    # Create comment statistics cards
    comment_stats_cards = dbc.Row([
        dbc.Col([dbc.Card([
            dbc.CardBody([
                html.H4("Highest Upvoted Post", className="card-title", style={'color': 'green', 'textAlign': 'center'}),
                html.P(f"{highest_voted_comment['post_title']}", className="card-text", style={'textAlign': 'center'}),
                html.P(f"“{highest_voted_comment['comment_text']}”", className="card-text", style={"fontStyle": "italic", "marginLeft": "20px", 'textAlign': 'center'}),
                html.P(f"Upvotes: {highest_voted_comment['comment_upvotes']}", className="card-text", style={'font-weight': 'bold', 'textAlign': 'center'}),
                html.H4("Lowest Upvoted Post", className="card-title", style={'color': 'red', 'textAlign': 'center'}),
                html.P(f"{lowest_voted_comment['post_title']}", className="card-text", style={'textAlign': 'center'}),
                html.P(f"“{highest_voted_comment['comment_text']}”", className="card-text", style={"fontStyle": "italic", "marginLeft": "20px", 'textAlign': 'center'}),
                html.P(f"Upvotes: {lowest_voted_comment['comment_upvotes']}", className="card-text", style={'font-weight': 'bold', 'textAlign': 'center'}),
            ])
        ], outline=True, className="mb-4 shadow-lg rounded", style={"border": "1px solid #ddd", "padding": "1rem"}, id='card-a')], width=6),
        
        dbc.Col([dbc.Card([
            dbc.CardBody([
                html.H4("Highest Voted Comment", className="card-title", style={'color': 'green', 'textAlign': 'center'}),
                html.P(f"“{highest_sentiment_comment['comment_text']}”", className="card-text", style={"fontStyle": "italic", "marginLeft": "20px", 'textAlign': 'center'}),
                # html.P(f"{highest_sentiment_comment['comment_text']}", className="card-text"),
                html.P(f"Upvotes: {highest_sentiment_comment['comment_upvotes']} | Post: {highest_sentiment_comment['post_title']}", className="card-text", style={'font-weight': 'bold', 'textAlign': 'center'}),
                html.H4("Lowest Voted Comment", className="card-title", style={'color': 'red', 'textAlign': 'center'}),
                html.P(f"“{lowest_sentiment_comment['comment_text']}”", className="card-text", style={"fontStyle": "italic", "marginLeft": "20px", 'textAlign': 'center'}),
                # html.P(f"{lowest_sentiment_comment['comment_text']}", className="card-text"),
                html.P(f"Upvotes: {lowest_sentiment_comment['comment_upvotes']} | Post: {lowest_sentiment_comment['post_title']}", className="card-text", style={'font-weight': 'bold', 'textAlign': 'center'}),
            ])
        ], outline=True, className="mb-4 shadow-lg rounded", style={"border": "1px solid #ddd", "padding": "1rem"}, id='card-b')], width=6)
    ])

    post_summary = dbc.Row([
        dbc.Col([
            dbc.Card(
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.H5("Summary of Comments", className="card-title text-primary", style={'textAlign': 'center'}),
                                html.Hr(),
                                html.P(comments_summary, className="card-text font-weight-bold")
                            ], className="mb-3")
                        ])
                    ])
                ]),
                outline=True,
                className="mb-4 shadow-lg rounded",
                style={"border": "1px solid #ddd", "padding": "1rem"}
            )
        ], width=12)
    ])

    # Create comment upvotes vs sentiment plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=selected_post_df.reset_index(drop=True).index,
        y=selected_post_df['comment_upvotes'],
        mode='markers',
        marker=dict(
            size=10,
            color=selected_post_df['sentiment'],
            colorscale='RdYlGn',
            showscale=True
        ),
        text=selected_post_df['comment_text'],
        hoverinfo='text+y+name'
    ))
    fig.update_layout(title='Comment Upvotes vs Sentiment',
                      xaxis_title='# Comments (oldest-newest)',
                      yaxis_title='Comment Upvotes',
                      template='plotly_dark')
    comment_upvotes_vs_sentiment_graph = dbc.Row([
        dbc.Col([dcc.Graph(figure=fig)], width=12, className="mb-4")
    ])

    return {'display': 'none'}, {'display': 'block'}, [post_summary, comment_upvotes_vs_sentiment_graph, comment_stats_cards]


# In[71]:


if __name__ == '__main__':
    release_port()  # Release the port before starting the server
    app.run(host='0.0.0.0', port=8050)


# In[ ]:





# In[ ]:





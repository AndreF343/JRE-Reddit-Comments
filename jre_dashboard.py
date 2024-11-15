#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import dash
import base64
import sqlite3
import requests
import wordcloud
import pandas as pd
from dash import html
from io import BytesIO
from openai import OpenAI
from dash import dcc, html
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output


# In[2]:


# Set OpenAI API key
oai_client = OpenAI(
    # api_key = ''
    api_key=os.environ.get("OPENAI_API_KEY")
)


# In[3]:


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


# In[4]:


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


# In[5]:


df_merged = df_merged[~df_merged.index.duplicated(keep='first')]

df_merged.comment_upvotes = df_merged.comment_upvotes.astype(int)
df_merged.episode_number = df_merged.episode_number.astype(int)

# Ensure 'post_upload_date' is in datetime format
try:
    df_merged['post_upload_date'] = pd.to_datetime(df_merged['post_upload_date'], format='%d/%m/%Y', errors='raise')
except:
    df_merged['post_upload_date'] = pd.to_datetime(df_merged['post_upload_date'], format='%d %b %Y', dayfirst=True, errors='raise')


# In[6]:


df_merged.info()


# In[7]:


# Calculate Metrics
highest_upvoted_post = post_df.loc[post_df['post_upvotes'].idxmax()]
lowest_upvoted_post = post_df.loc[post_df['post_upvotes'].idxmin()]
lowest_upvote_ratio_post = post_df.loc[post_df['post_upvote_ratio'].idxmin()]

highest_voted_comment = df_merged.loc[df_merged['comment_upvotes'].idxmax()]
lowest_voted_comment = df_merged.loc[df_merged['comment_upvotes'].idxmin()]

most_frequent_guests = post_df['episode_guest'].value_counts().head(3)

highest_sentiment_guest = df_merged.groupby('episode_guest')['sentiment'].mean().idxmax()
lowest_sentiment_guest = df_merged.groupby('episode_guest')['sentiment'].mean().idxmin()
highest_sentiment_score = df_merged.groupby('episode_guest')['sentiment'].mean().max()
lowest_sentiment_score = df_merged.groupby('episode_guest')['sentiment'].mean().min()


# In[8]:


# Sentiment Plot Function
def create_sentiment_plot():
    df_sentiment_per_post = df_merged.groupby('reddit_post_id')['sentiment'].mean().reset_index()
    df_sentiment_with_date = df_merged[['reddit_post_id', 'post_upload_date', 'post_title']].drop_duplicates()
    df_sentiment_per_post = df_sentiment_per_post.merge(df_sentiment_with_date, on='reddit_post_id', how='left')
    df_sentiment_per_post = df_sentiment_per_post.sort_values(by='post_upload_date')
    df_sentiment_per_post['running_avg_sentiment'] = df_sentiment_per_post['sentiment'].expanding().mean()
    
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df_sentiment_per_post['post_upload_date'], y=df_sentiment_per_post['sentiment'],
                             fill='tozeroy', mode='lines', line_shape='spline', name='Average Sentiment per Post',
                             text=df_sentiment_per_post['post_title'], hovertemplate='Post Title: %{text}<br>Average Sentiment: %{y:.2f}<extra></extra>'))
    
    # Add running average sentiment as a line chart
    fig.add_trace(go.Scatter(x=df_sentiment_per_post['post_upload_date'], y=df_sentiment_per_post['running_avg_sentiment'],
                             mode='lines', name='Running Average Sentiment', line=dict(color='red')))
    fig.update_layout(title='Running Average Sentiment Per Post Over Time',
                      xaxis_title='Post Upload Date',
                      yaxis_title='Average Sentiment',
                      template='plotly_dark',
                      xaxis_rangeslider_visible=True)
    return fig

# Word Cloud Function
def create_word_cloud():
    text = ' '.join(df_merged['comment_text'].dropna().values)
    wc = wordcloud.WordCloud(width=800, height=400, background_color='black', colormap='Set2').generate(text)
    img = BytesIO()
    wc.to_image().save(img, format='PNG')
    encoded_image = base64.b64encode(img.getvalue()).decode()
    return 'data:image/png;base64,{}'.format(encoded_image)

# Load Images
with open(r"joeroganbackground.jpg", "rb") as image_file:
    joe_background_image = base64.b64encode(image_file.read()).decode()

# Function to search Bing for guest images
def get_guest_images(guests):
    guest_images = {}
    subscription_key = "3de6d7a146e148cfa7d2623afce9a2d0"  # Replace with your Bing Search API key
    search_url = "https://api.bing.microsoft.com/v7.0/images/search"
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    for guest in guests:
        params = {"q": f"{guest}", "license": "public", "imageType": "photo"}
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        search_results = response.json()
        if "value" in search_results and len(search_results["value"]) > 0:
            guest_images[guest] = search_results["value"][0]["contentUrl"]
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


# In[13]:


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
app.title = "JRE Reddit Post Dashboard"

app.layout = dbc.Container([
    # Header Section
    dbc.Container(
        [
            html.H1("JRE Reddit Post Dashboard", style={'textAlign': 'center', 'color': 'mustard', 'fontWeight': 'bold'}),
            html.H6(f"{len(df_merged['reddit_post_id'].unique())} posts scanned, {len(df_merged)} comments scraped", style={'textAlign': 'center', 'fontStyle': 'italic', 'color': 'lightgray'})
        ],
        fluid=True,  # Makes the header full-width
        style={'padding-top': '20px'}
    ),
    
    # Dropdown Section
    dbc.Container(
        dcc.Dropdown(
            id='post-dropdown',
            options=[{'label': title, 'value': title} for title in post_df['post_title']],
            placeholder="Select a Post",
            style={'margin-bottom': '20px'}
        ),
        fluid=True
    ),
    
    # Home Content Section
    dbc.Container(
        html.Div(id='home-content', children=[
            dbc.Row([
                dbc.Col([dcc.Graph(id='sentiment-plot', figure=create_sentiment_plot())], width=8, style={'display': 'flex', 'flex-direction': 'column', 'justify-content': 'stretch'}),
                dbc.Col([
                    html.Div([
                        html.Img(id='word-cloud', src=create_word_cloud(), style={'width': '100%', 'height': 'auto', 'flex': '1 1 50%'}),
                        html.Img(id='joe-background', src='data:image/jpeg;base64,{}'.format(joe_background_image), style={'width': '100%', 'margin-top': '20px', 'height': 'auto', 'flex': '1 1 50%'})
                    ], style={'display': 'flex', 'flex-direction': 'column', 'height': '100%'})
                ], width=4, style={'display': 'flex', 'flex-direction': 'column', 'justify-content': 'stretch'})
            ], className="mb-4", style={'display': 'flex', 'flex-direction': 'row', 'height': '100%'}),

            dbc.Row([
                dbc.Col([dbc.Card([
                    html.H4("Most Upvoted Post and Lowest Upvote Ratio", className="card-title"),
                    html.P(f"Highest: {highest_upvoted_post['post_title']} (Upvotes: {highest_upvoted_post['post_upvotes']})", className="card-text"),
                    html.P(f"Lowest: {lowest_upvote_ratio_post['post_title']} (Upvotes: {lowest_upvote_ratio_post['post_upvotes']}, Ratio: {lowest_upvote_ratio_post['post_upvote_ratio']})", className="card-text"),
                ], outline=True, className="mb-4")], width=3),
                
                dbc.Col([dbc.Card([
                    html.H4("Highest and Lowest Voted Comments", className="card-title"),
                    html.P(f"Highest: {highest_voted_comment['comment_text']} (Upvotes: {highest_voted_comment['comment_upvotes']}, Post: {highest_voted_comment['post_title']})", className="card-text"),
                    html.P(f"Lowest: {lowest_voted_comment['comment_text']} (Upvotes: {lowest_voted_comment['comment_upvotes']}, Post: {lowest_voted_comment['post_title']})", className="card-text"),
                ], outline=True, className="mb-4")], width=3),
                
                dbc.Col([dbc.Card([
                    html.H4("Most Frequent Guests", className="card-title"),
                    html.Ol(
                        [
                            html.Li(
                                [
                                    f"{guest} ({most_frequent_guests[guest]} appearances)",
                                    html.Img(
                                        src=most_frequent_guest_images.get(guest, ''),
                                        style={'height': '50px', 'margin-left': '10px'}
                                    )
                                ]
                            )
                            for guest in most_frequent_guests.index
                        ]
                    )
                    # html.Ul([html.Li([f"{guest} ({most_frequent_guests[guest]} appearances)", html.Img(src=most_frequent_guest_images.get(guest, ''), style={'height': '50px', 'margin-left': '10px'})]) for guest in most_frequent_guests.index]),
                ], outline=True, className="mb-4")], width=3),
                
                dbc.Col([dbc.Card([
                    html.H4("Highest and Lowest Sentiment Guests", className="card-title"),
                    html.P(f"Highest: {highest_sentiment_guest} (Sentiment: {highest_sentiment_score:.2f})", className="card-text"),
                    html.P(f"Lowest: {lowest_sentiment_guest} (Sentiment: {lowest_sentiment_score:.2f})", className="card-text"),
                ], outline=True, className="mb-4")], width=3),
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
        .head(20)['tokens']
        .tolist())
    try:
        response = oai_client.chat.completions.create(
            messages = [
                {
                    "role": "user",
                    "content": f"Summarize the following comments: {comments_text}",  # Limiting to first 3000 characters
                    # max_tokens=150
                }
            ],
            model="gpt-3.5-turbo"
        )
        # comments_summary = response.choices[0].text.strip()
        comments_summary = response.choices[0].message.content
    except Exception as e:
        comments_summary = f"Error summarizing comments: {e}"

    # Create comment statistics cards
    comment_stats_cards = dbc.Row([
        dbc.Col([dbc.Card([
            html.H4("Highest and Lowest Upvoted Comments", className="card-title"),
            html.P(f"Highest: {highest_voted_comment['comment_text']} (Upvotes: {highest_voted_comment['comment_upvotes']})", className="card-text"),
            html.P(f"Lowest: {lowest_voted_comment['comment_text']} (Upvotes: {lowest_voted_comment['comment_upvotes']})", className="card-text"),
        ], outline=True, className="mb-4", id='card-a')], width=6, id='col-a', style={'position': 'relative'}),
        
        dbc.Col([dbc.Card([
            html.H4("Highest and Lowest Sentiment Comments", className="card-title"),
            html.P(f"Highest: {highest_sentiment_comment['comment_text']} (Sentiment: {highest_sentiment_comment['sentiment']:.2f})", className="card-text"),
            html.P(f"Lowest: {lowest_sentiment_comment['comment_text']} (Sentiment: {lowest_sentiment_comment['sentiment']:.2f})", className="card-text"),
        ], outline=True, className="mb-4", id='card-b')], width=6, id='col-b', style={'position': 'relative'})
    ])

    # Adding Card C to both columns A and B
    card_c_a = html.Div(
        dbc.Card(
            html.Div(
                html.Img(
                    src=app.get_asset_url('jrh.png'),
                    style={
                        'max-width': '100%',
                        'max-height': '100%',
                        'width': '100%',
                        'height': '100%',
                        'object-fit': 'contain',
                        'display': 'block',
                    }
                ),
                style={
                    'width': '100%',
                    'height': '100%',
                    'display': 'flex',
                    'align-items': 'center',
                    'justify-content': 'center',
                }
            ),
            id='card-c-a',
            style={
                'background-color': 'transparent',
                'overflow': 'hidden',
                'width': '100%',
                'height': '100%',
            }
        ),
        id='card-c-container-a',
        style={
            'display': 'none',
            'position': 'absolute',
            'width': 'auto',
            'height': 'auto',
        }
    )

    card_c_b = html.Div(
        dbc.Card(
            html.Div(
                html.Img(
                    src=app.get_asset_url('jrh.png'),
                    style={
                        'max-width': '100%',
                        'max-height': '100%',
                        'width': '100%',
                        'height': '100%',
                        'object-fit': 'contain',
                        'display': 'block',
                    }
                ),
                style={
                    'width': '100%',
                    'height': '100%',
                    'display': 'flex',
                    'align-items': 'center',
                    'justify-content': 'center',
                }
            ),
            id='card-c-b',
            style={
                'background-color': 'transparent',
                'overflow': 'hidden',
                'width': '100%',
                'height': '100%',
            }
        ),
        id='card-c-container-b',
        style={
            'display': 'none',
            'position': 'absolute',
            'width': 'auto',
            'height': 'auto',
        }
    )

    # Add Card C to Columns A and B
    comment_stats_cards.children[0].children.append(card_c_a)
    comment_stats_cards.children[1].children.append(card_c_b)

    post_summary = dbc.Row([
        dbc.Col([dbc.Card([
            html.H4("Summary of Comments", className="card-title"),
            html.P(comments_summary, className="card-text")
            ], outline=True, className="mb-4", style={'height': 'fit-content'})], width=12)
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
        dbc.Col([dcc.Graph(figure=fig)], width=12)
    ])

    return {'display': 'none'}, {'display': 'block'}, [post_summary, comment_upvotes_vs_sentiment_graph, comment_stats_cards]

# Ensure that the app stops running when the script is interrupted
def release_port(port=8050):
    try:
        os.system(f"fuser -k {port}/tcp")
    except Exception as e:
        print(f"Error releasing port {port}: {e}")


# In[14]:


if __name__ == '__main__':
    release_port()  # Release the port before starting the server
    app.run(host='0.0.0.0', port=8050, debug=False)


# In[ ]:





# In[ ]:





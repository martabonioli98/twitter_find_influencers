
import networkx as nx
import tweepy
import pandas as pd
import numpy as np
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
from datetime import datetime
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import twitter
from tweepy import Cursor
from datetime import datetime, date, time, timedelta
from collections import Counter
import sys
import ssl
import csv
ssl._create_default_https_context = ssl._create_unverified_context
import re
import plotly.express as px






class Network_influencer():

    def __init__(self, myApi, sApi, at, sAt, account):
        self.tweepy = tweepy
        self.auth = tweepy.OAuthHandler(myApi, sApi)
        self.auth.set_access_token(at, sAt)
        self.api = tweepy.API(self.auth, wait_on_rate_limit=True)
        self.account = account
        self.graph = nx.DiGraph()
        bearer_token = twitter.oauth2_dance(consumer_key = myApi, consumer_secret = sApi )
        self.twitter_api = twitter_api = twitter.Twitter(auth=twitter.OAuth2(bearer_token = bearer_token))




    #non-ascii characters can cause problems for you in various file types
    def strip_non_ascii(self, string):
        ''' Returns the string without non ASCII characters'''
        stripped = (c for c in string if 0 < ord(c) < 127)
        return ''.join(stripped)

    #search last max 100 tweets contain #keyword
    def keyword_search2(self, keyword):
        df_tweet = pd.DataFrame(columns=['tweet_id', 'tweet_text', 'date'])
        #tweets = tweepy.Cursor(self.api.search, q=keyword, tweet_mode='extended',since="2021-01-01",count=100).items()
        print('rilevati i tweeet di '+ str(keyword))
        tweets = self.api.search(q=keyword, rpp=1000, count=1000, show_user=True,since="2021-01-01", tweet_mode='extended')
        for tweet in tweets:
            df_tweet.loc[len(df_tweet)] = [tweet.id_str, self.strip_non_ascii(tweet.full_text),tweet.created_at.strftime('%m/%d/%Y')]
        # Instantiate new SentimentIntensityAnalyzer
        sid = SentimentIntensityAnalyzer()
        print(df_tweet['date'].unique())
        # Generate sentiment scores
        sentiment_scores = df_tweet['tweet_text'].apply(sid.polarity_scores)
        sentiment = sentiment_scores.apply(lambda x: x['compound'])
        df_tweet['sentiment_scores'] = sentiment
        mean = df_tweet['sentiment_scores'].mean()
        num_tweet = len(df_tweet)
        return mean, num_tweet




    def create_piechart(self, df):
        px.pie(df, values='count', names='name', color_discrete_sequence=px.colors.sequential.RdBu)


    #search tweets by keyword
    def keyword_search(self, keyword):
        csv_prefix = '{}_tweets'.format(keyword)
        API_results = self.api.search(q=keyword, rpp=1000, count=1000, show_user=True, tweet_mode='extended')

        with open(f'{csv_prefix}.csv', 'w', newline='') as csvfile:
            fieldnames = ['tweet_id', 'tweet_text', 'date', 'user_id', 'follower_count',
                          'retweet_count', 'user_mentions']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for tweet in API_results:
                text = self.strip_non_ascii(tweet.full_text)
                date = tweet.created_at.strftime('%m/%d/%Y')
                writer.writerow({
                    'tweet_id': tweet.id_str,
                    'tweet_text': text,
                    'date': date,
                    'user_id': tweet.user.id_str,
                    'follower_count': tweet.user.followers_count,
                    'retweet_count': tweet.retweet_count,
                    'user_mentions': tweet.entities['user_mentions']
                })

    #search tweet that have mention an account
    def user_search(self):
        import csv
        csv_prefix = '{}_tweets'.format(self.account)
        user = self.account
        API_results = self.tweepy.Cursor(self.api.user_timeline, id=user, tweet_mode='extended').items()

        with open(f'{csv_prefix}.csv', 'w', newline='') as csvfile:
            fieldnames = ['tweet_id', 'tweet_text', 'date', 'user_id', 'user_mentions', 'retweet_count']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            #df_result = pd.DataFrame(columns=fieldnames)

            for tweet in API_results:
                text = self.strip_non_ascii(tweet.full_text)
                date = tweet.created_at.strftime('%m/%d/%Y')
                writer.writerow({
                    'tweet_id': tweet.id_str,
                    'tweet_text': text,
                    'date': date,
                    'user_id': tweet.user.id_str,
                    'user_mentions': tweet.entities['user_mentions'],
                    'retweet_count': tweet.retweet_count
                })




    def read_tweet(self):
        return pd.read_csv('{}_tweets.csv'.format(self.account))

    def create_graph(self, read_tweet):
        import ast
        edge_list = []
        for idx, row in read_tweet.iterrows():
            # len(row[4]) :column associated with user mentions
            # Sometimes it’s empty of all characters, sometimes it has just [] listed and other times it has [[ ]] listed

            if len(row[4]) > 5:
                user_account = self.account
                weight = np.log(row[5] + 1)  # row[5] is the retweet_count
                # add weight on edge to discern highly active non-influential users from the influencers
                # use log because we don’t want this effect to be overpowering

                for idx_1, item in enumerate(ast.literal_eval(row[4])):
                    edge_list.append((user_account, item['screen_name'], weight))

                    for idx_2 in range(idx_1 + 1, len(ast.literal_eval(row[4]))):
                        name_a = ast.literal_eval(row[4])[idx_1]['screen_name']
                        name_b = ast.literal_eval(row[4])[idx_2]['screen_name']

                        edge_list.append((name_a, name_b, weight))



        self.graph.add_weighted_edges_from(edge_list)
        return self.graph

    def eigen_centrality(self):
        return nx.eigenvector_centrality(self.graph, weight='weights', max_iter=1000)

    def frequently_words(self, tweet_texts):
        from PIL import Image
        #mask = np.array(Image.open('images/twitter.png'))
        comment_words = ' '  # We will be appending the words to this var
        stopwords = set(STOPWORDS)  # Finds all stop words in the set of tweets.
        for val in tweet_texts:
            val = str(val)  # convert all tweet content into strings
            tokens = val.split()  # Split all strings into individual components
            for i in range(len(tokens)):
                tokens[i] = tokens[i].lower()  # Converts all the individual strings to lower case.
        for words in tokens:
            comment_words = comment_words + words + ' '
        wordcloud = WordCloud(width=1000, height=1000, background_color='#BBE6EE', stopwords=stopwords,
                              min_font_size=1, max_words=300).generate(comment_words)  # All of this is a single line
        plt.figure(figsize=(5, 5), facecolor=None)
        plt.imshow(wordcloud)
        plt.axis("off")
        plt.tight_layout(pad=0)
        plt.show()
        plt.savefig('images/wordcloud.png')



    def sentiment_tweets_analisy(self, df):
        df['date'] = df.apply(lambda x: datetime.strptime(x['date'], "%m/%d/%Y"), axis=1)
        # Instantiate new SentimentIntensityAnalyzer
        sid = SentimentIntensityAnalyzer()
        # Generate sentiment scores
        sentiment_scores = df['tweet_text'].apply(sid.polarity_scores)
        sentiment = sentiment_scores.apply(lambda x: x['compound'])
        df['sentiment_scores'] = sentiment
        sentiment_time_series = df.groupby(df['date'].map(lambda x: x.year))['sentiment_scores'].mean()
        Y = []
        for score in sentiment_time_series:
            Y.append(score)
        X = list(sentiment_time_series.keys())
        df = pd.DataFrame({
            'Date': X,
            'Sentiment': Y
        })

        df = df.set_index('Date')

        return df





    #profile details
    def profile_details(self):
        item = self.api.get_user(self.account)
        details = {
            "name": item.name,
            "screen_name": item.screen_name,
            "description": item.description,
            "statuses_count": item.statuses_count,
            "friends_count": item.friends_count,
            "followers_count": item.followers_count
        }

        # calculate the age of the account
        # how many Tweets that account has published (statuses_count)
        # calculate the average Tweets per day rate of that account
        tweets = item.statuses_count
        account_created_date = item.created_at
        delta = datetime.utcnow() - account_created_date
        account_age_days = delta.days
        # print("Account age (in days): " + str(account_age_days))
        details["age"] = account_age_days
        if account_age_days > 0:
            # print("Average tweets per day: " + "%.2f" % (float(tweets) / float(account_age_days)))
            details["tweets_per_day"] = "%.2f" % (float(tweets) / float(account_age_days))

        # collect lists of all hashtags and mentions seen in Tweets
        hashtags = []
        df_hashtags = pd.DataFrame(columns=['name', 'count','num_tweet','sentiment'])
        mentions = []
        df_mentions = pd.DataFrame(columns=['name', 'count'])
        tweet_count = 0
        end_date = datetime.utcnow() - timedelta(days=360)
        for status in Cursor(self.api.user_timeline, id=self.account).items():
            tweet_count += 1
            if hasattr(status, "entities"):
                entities = status.entities
                if "hashtags" in entities:
                    for ent in entities["hashtags"]:
                        if ent is not None:
                            if "text" in ent:
                                hashtag = ent["text"]
                                if hashtag is not None:
                                    hashtags.append(hashtag)
                if "user_mentions" in entities:
                    for ent in entities["user_mentions"]:
                        if ent is not None:
                            if "screen_name" in ent:
                                name = ent["screen_name"]
                                if name is not None:
                                    mentions.append(name)
            if status.created_at < end_date:
                break

        #print("Most used hashtags:")
        for item, count in Counter(hashtags).most_common(5):
          print(item + "\t" + str(count))
          mean, num_tweet = self.keyword_search2(item)
          item = '#'+item
          df_hashtags.loc[len(df_hashtags)] = [item,count,num_tweet,mean]
        tweet_processed = str(tweet_count)
        chart_hashtags = px.pie(df_hashtags, values='num_tweet', names='name', color_discrete_sequence=px.colors.sequential.RdBu)
        return details, df_mentions, df_hashtags, chart_hashtags, tweet_processed










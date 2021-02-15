import streamlit as st
import network_influencer
import networkx as nx
from PIL import Image


st.title('Twitter Analyzer')
user_input = st.text_input("Insert Twitter account", '')

if user_input is not None:
    st.write('I am analyzing  ', user_input, ' profile... Have patient please, it is not so easy;) ')

    #Setting the authentication credentials + Instantiating the API
    consumer_key = "aZQxSXaItLednaywvimyzJObu"
    consumer_secret = "dh1ps8q9Ab4ylTIZ75B3yGbd2mAxDRWYsKN2Uo30AvSW2lUIfZ"
    access_token = "1235494563730595840-qmcedLeJB2pOLeaj2Pnl0oJoaj25Mi"
    access_token_secret = "UM7BnO4GdiYro2B0gLsVCLrSi8poSLblyGs0eN1PPTVpH"

    #create Network influencer object using the account insert as input
    influencer_network = network_influencer.Network_influencer(consumer_key, consumer_secret, access_token,
                                                     access_token_secret, user_input)

    #search last user-mentions tweets
    influencer_network.user_search()
    tweets = influencer_network.read_tweet()
    tweets_texts = tweets['tweet_text']

    #create directed graph
    graph = influencer_network.create_graph(tweets)
    centrality = influencer_network.eigen_centrality()

    #some details

    details, df_mentions, df_hashtag, chart_hashtags, tweets_processed = influencer_network.profile_details()
    st.write(details)
    st.subheader('')
    st.subheader('Most used hashtags # ')
    for i in range(0,5):
        string = ''+ str(i+1)+ '. '+ df_hashtag['name'].loc[i]
        st.write(string)
    #st.plotly_chart(chart_hashtags)

    st.title('Podium of your influencers')
    image1 = Image.open('images/1.jpg')
    image2 = Image.open('images/2.jpg')
    image3 = Image.open('images/3.jpg')
    title_container1 = st.beta_container()
    col1, col2, col3, col4, col5, col6 = st.beta_columns([1.3,10,1.3,10,1.3,10])
    with title_container1:
            with col1:
                st.image(image1, width=30)
            with col2:
                st.markdown(list(centrality.keys())[1],unsafe_allow_html=True)
            with col3:
                st.image(image2, width=30)
            with col4:
                st.markdown(list(centrality.keys())[2], unsafe_allow_html=True)
            with col5:
                st.image(image3, width=30)
            with col6:
                st.markdown(list(centrality.keys())[3], unsafe_allow_html=True)

    st.subheader('Sorted full list of Influencer: ')
    st.write(list(centrality.keys())[4:])
    #most common word used
    influencer_network.frequently_words(tweets_texts)
    st.title(' WordCloud ')
    wordcloud_image = Image.open('images/wordcloud.png')
    st.image(wordcloud_image, width=400)

    #sentiment tweet analysis
    sentiment_time_series = influencer_network.sentiment_tweets_analisy(tweets)
    st.title(' Time Series Sentiment of tweets by years ')
    st.write(' x : years ')
    st.write(' y : average sentiment of tweets')
    st.line_chart(sentiment_time_series)


else:
    st.write('Insert twitter user')


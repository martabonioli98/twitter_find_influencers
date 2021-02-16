import streamlit as st
import pandas as pd
import json

st.title('MASI TWITTER NETWORK')
st.header('**Discover your potential influencers**')
st.header('')

f = open('MasiWines/MasiWines_details.json')
account_details = json.load(f)
print(account_details['name'])
user_input = account_details['name']

congrats = 'CONGRATS '+ user_input + ' FOR YOURS ' + str(account_details['followers_count']) + ' FOLLOWERS!'
st.subheader(congrats)
st.subheader('')
st.header('TOP 10 Influencer')
st.dataframe(pd.read_json('MasiWines/MasiWines_top10_influencer.json'))
st.subheader('Are this twitter users interests for you ?')
st.write('If you want to understand more about one of this try the web app TWITTER ANALYZER !')



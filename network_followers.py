from tweepy import OAuthHandler
from tweepy import API
from datetime import datetime, date, time, timedelta
import sys
import os
import io
import re
import time
import networkx as nx
import json
from random import shuffle
from googletrans import Translator
import pandas as pd
from collections import Counter
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import nltk
nltk.download('stopwords')






class Network_followers():

    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret,monkey_token, account):
        auth = OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.auth_api = API(auth, wait_on_rate_limit=True)
        self.account = account
        self.id_account = self.auth_api.get_user(screen_name=account).id_str
        self.MONKEYLEARN_TOKEN = monkey_token
        self.MONKEYLEARN_CLASSIFIER_BASE_URL = 'https://api.monkeylearn.com/api/v3/categorizer/'
        self.MONKEYLEARN_EXTRACTOR_BASE_URL = 'https://api.monkeylearn.com/api/v3/extraction/'
        # This classifier is used to detect the tweet/bio's language
        self.MONKEYLEARN_LANG_CLASSIFIER_ID = 'cl_hDDngsX8'
        # This classifier is used to detect the tweet/bio's topics
        self.MONKEYLEARN_TOPIC_CLASSIFIER_ID = 'cl_o46qggZq'
        # This extractor is used to extract keywords from tweets and bios
        self.MONKEYLEARN_EXTRACTOR_ID = 'ex_YCya9nrn'


    # create a new direct graph from
    def get_direct_graph(self):
        DG = nx.DiGraph()
        DG.add_node(self.id_account)
        # Get a list of Twitter ids for followers of target account and save it and and in the graph
        filename = self.id_account + "_follower_ids.json"
        follower_ids = self.try_load_or_process(filename, self.get_follower_ids, self.id_account)
        number_followers = len(follower_ids)
        print(str(number_followers) + " followers")
        # add list in the graph followers_net
        followers_net = self.add_followers(self.followers_net, self.id_account, follower_ids)
        # for each follower load his follower and add in the graph
        followers_net = self.calculate_list_followers2(follower_ids, followers_net)
        return DG

    #save gexf file
    def get_gexf(self):
        return self.write_gexf(self, "network.gexf")

    # add followers / edge for an account
    def add_followers(self,followers_net, list_follower):
        id_node = self.id_account
        followers_net.add_nodes_from(list_follower)
        for id in list_follower:
            followers_net.add_edge(id_node, id)
        return followers_net

    # Helper functions to load and save intermediate steps
    def save_json(self,variable, filename):
        with io.open(filename, "w", encoding="utf-8") as f:
            f.write(str(json.dumps(variable, indent=4, ensure_ascii=False)))
    def load_json(self,filename):
        ret = None
        if os.path.exists(filename):
            try:
                with io.open(filename, "r", encoding="utf-8") as f:
                    ret = json.load(f)
            except:
                pass
        return ret
    def try_load_or_process(self,filename, processor_fn, function_arg):
        load_fn = None
        save_fn = None
        if filename.endswith("json"):
            load_fn = self.load_json
            save_fn = self.save_json
        else:
            print('error')
        if os.path.exists(filename):
            print("Loading " + filename)
            return load_fn(filename)
        else:
            ret = processor_fn(function_arg)
            print("Saving " + filename)
            save_fn(ret, filename)
            return ret

    # Some helper functions to convert between different time formats and perform date calculations
    def twitter_time_to_object(self,time_string):
        twitter_format = "%a %b %d %H:%M:%S %Y"
        match_expression = "^(.+)\s(\+[0-9][0-9][0-9][0-9])\s([0-9][0-9][0-9][0-9])$"
        match = re.search(match_expression, time_string)
        if match is not None:
            first_bit = match.group(1)
            second_bit = match.group(2)
            last_bit = match.group(3)
            new_string = first_bit + " " + last_bit
            date_object = datetime.strptime(new_string, twitter_format)
            return date_object
    def time_object_to_unix(self,time_object):
        return int(time_object.strftime("%s"))
    def twitter_time_to_unix(self,time_string):
        return self.time_object_to_unix(self.twitter_time_to_object(time_string))
    def seconds_since_twitter_time(self,time_string):
        input_time_unix = int(self.twitter_time_to_unix(time_string))
        current_time_unix = int(self.get_utc_unix_time())
        return current_time_unix - input_time_unix
    def get_utc_unix_time(self):
        dts = datetime.utcnow()
        return time.mktime(dts.timetuple())



    # Get a list of follower ids for the target account
    def get_follower_ids(self,target):
        try:
            return self.auth_api.followers_ids(target)
        except:
            pass
            print("Failed to run the command on that user, Skipping...")


    # Twitter API allows us to batch query 100 accounts at a time
    # So we'll create batches of 100 follower ids and gather Twitter User objects for each batch
    def get_follower_ids_fromid(self,id):
        try:
            return self.auth_api.followers_ids(user_id=id)
        except:
            pass
            print("Failed to run the command on that user, Skipping... return 0")
            return []



    def get_user_objects(self,follower_ids):
        batch_len = 100
        num_batches = len(follower_ids) / 100
        batches = (follower_ids[i:i + batch_len] for i in range(0, len(follower_ids), batch_len))
        all_data = []
        for batch_count, batch in enumerate(batches):
            sys.stdout.write("\r")
            sys.stdout.flush()
            sys.stdout.write("Fetching batch: " + str(batch_count) + "/" + str(num_batches))
            sys.stdout.flush()
            users_list = self.auth_api.lookup_users(user_ids=batch)
            users_json = (map(lambda t: t._json, users_list))
            all_data += users_json
        return all_data


    def calculate_list_followers2(self, follower_ids, followers_net):
        c = 1
        list_followers = []
        for id in follower_ids:
            print("processing % " + str(c / len(follower_ids) * 100) + " id: " + str(id))
            list_followers = self.get_follower_ids_fromid(id)
            # add list in the graph followers_net
            if len(list_followers) != 0:
                followers_net = self.add_followers(followers_net, id, list_followers)
            c = c + 1
        return followers_net


    # Creates one week length ranges and finds items that fit into those range boundaries
    def make_ranges(self,user_data, num_ranges=5000):
        range_max = 604800 * num_ranges
        range_step = range_max / num_ranges
        # create ranges and labels first and then iterate these when going through the whole list
        # of user data, to speed things up
        ranges = {}
        labels = {}
        for x in range(num_ranges):
            start_range = x * range_step
            end_range = x * range_step + range_step
            label = "%02d" % x + " - " + "%02d" % (x + 1) + " weeks"
            labels[label] = []
            ranges[label] = {}
            ranges[label]["start"] = start_range
            ranges[label]["end"] = end_range
        for user in user_data:
            if "created_at" in user:
                account_age = self.seconds_since_twitter_time(user["created_at"])
                for label, timestamps in ranges.items():
                    if account_age > timestamps["start"] and account_age < timestamps["end"]:
                        entry = {}
                        id_str = user["id_str"]
                        entry[id_str] = {}
                        fields = ["screen_name", "name", "created_at", "friends_count", "followers_count",
                                  "favourites_count", "statuses_count"]
                        for f in fields:
                            if f in user:
                                entry[id_str][f] = user[f]
                        labels[label].append(entry)
        return labels

    #Record a few details about each account that falls between specified age ranges
    def print_summary(self):
        # Fetch Twitter User objects from each Twitter id found and save the data
        filename = self.account + "_followers.json"
        follower_ids = self.account + "_followers_ids.json"
        user_objects = self.try_load_or_process(filename, self.get_user_objects, follower_ids)
        total_objects = len(user_objects)
        df = pd.DataFrame(columns=['age_ranges','num_new_follower'])
        # Record a few details about each account that falls between specified age ranges
        ranges = self.make_ranges(user_objects)
        print(len(ranges))
        filename = self.id_account + "_ranges.json"
        self.save_json(ranges, filename)
        print("\t\tFollower age ranges")
        total = 0
        following_counter = Counter()
        for label, entries in sorted(ranges.items()):
            print("\t\t" + str(len(entries)) + " accounts were created within " + label)
            df.loc[len(df)] = [len(entries), label]
            total += len(entries)
            for entry in entries:
                for id_str, values in entry.items():
                    if "friends_count" in values:
                        following_counter[values["friends_count"]] += 1
        return df

    #find details of account target
    def profile_details(self):
        item = self.auth_api.get_user(self.account)
        details = {
            "name": item.name,
            "screen_name": item.screen_name,
            "description": item.description,
            "statuses_count": item.statuses_count,
            "friends_count": item.friends_count,
            "followers_count": item.followers_count
        }
        # calculate the age of the account
        tweets = item.statuses_count
        account_created_date = item.created_at
        delta = datetime.utcnow() - account_created_date
        account_age_days = delta.days
        # print("Account age (in days): " + str(account_age_days))
        details["age"] = account_age_days
        if account_age_days > 0:
            # print("Average tweets per day: " + "%.2f" % (float(tweets) / float(account_age_days)))
            details["tweets_per_day"] = "%.2f" % (float(tweets) / float(account_age_days))

        self.save_json(details, 'MasiWines/MasiWines_details.json')
        return details

    #find top 10 hub of your network
    def centrality_dataframe(self):
        g = nx.read_gexf('network_{}.gexf'.format(self.account))
        in_degree_centrality = self.find_hub(dict(g.in_degree()))
        #out_degree_centrality = self.find_hub(dict(g.out_degree()))
        pr_centrality = self.find_hub(dict(nx.pagerank(g)))
        print('pr_centrality')
        katz_centrality = self.find_hub(nx.katz_centrality(g))
        print('katz_centrality')
        eigenvector_centrality = self.find_hub(nx.eigenvector_centrality(g))
        print('eigenvector_centrality')
        closeness_centrality = self.find_hub(nx.closeness_centrality(g))
        print('closeness_centrality')
        #betweenness_centrality = self.find_hub(nx.betweenness_centrality(g))
        #print('betweenness_centrality')
        df_hubs = pd.DataFrame({'In-degree': in_degree_centrality,
                                #'Betweenness': betweenness_centrality,
                                'Closeness': closeness_centrality,
                                'Eigenvector': eigenvector_centrality,
                                'Kartz': katz_centrality,
                                'PageRank': pr_centrality})
        print('dataframe creato')
        df_hubs.to_json('{}_top10_influencer.json'.format(self.account))
        print('dataframe salvato')
        return df_hubs


    def find_hub(self, centrality_measure):
        hubs = sorted(centrality_measure.items(), key=lambda x: x[1], reverse=True)[0:10]
        values = []
        for i in hubs:
            values.append(self.account_name(i[0]))
        return values

    def account_name(self,id):
        return self.auth_api.get_user(id=id).screen_name





    #understand interests of a user
    #Requirement: Monkeylearn
    #no ended code
    def understand_users(self, user):

        # Get the descriptions of the people that twitter_user is following.
        descriptions = self.get_friends_descriptions(user, max_users=300)
        # Get first 200 tweets of twitter_user
        print('start get_tweets')
        tweets = []
        tweets.extend(self.get_tweets(user, 'timeline', 1000))  # 400 = 2 requests (out of 15 in the window).
        tweets.extend(self.get_tweets(user, 'favorites', 400))  # 1000 = 5 requests (out of 180 in the window).
        tweets = (list(map(lambda t: t[0], sorted(tweets, key=lambda t: t[1], reverse=True))))[:500]
        print(len(tweets))
        return descriptions, tweets


    #return the bios of friends of users
    def get_friends_descriptions(self, user, max_users=100):
        print('get_friends_descriptions')
        twitter_account = user
        api =self.auth_api
        user_ids = self.auth_api.friends_ids(twitter_account)
        shuffle(user_ids)

        following = []
        for start in range(0, min(max_users, len(user_ids)), 100):
            end = start + 100
            following.extend(api.lookup_users(user_ids[start:end]))

        descriptions = []
        for user in following:
            print(user)
            description = re.sub(r'(https?://\S+)', '', user.description)

            # Only descriptions with at least ten words.
            if len(re.split(r'[^0-9A-Za-z]+', description)) > 10:
                description = description.strip('#').strip('@')
                descriptions.append(self.translate_it_en(description))
                print('description translate')
        print('end get_friends_descriptions ')
        return descriptions


    #get 200 tweets of account
    def get_tweets(self,user, tweet_type='timeline', max_tweets=200, min_words=5):
        api = self.auth_api
        twitter_user = user
        tweets = []
        full_tweets = []
        step = 200  # Maximum value is 200.
        for start in range(0, max_tweets, step):
            print(start)
            end = start + step
            # Maximum of `step` tweets, or the remaining to reach max_tweets.
            count = min(step, max_tweets - start)
            kwargs = {'count': count}
            if full_tweets:
                last_id = full_tweets[-1].id
                kwargs['max_id'] = last_id - 1
            if tweet_type == 'timeline':
                current = api.user_timeline(twitter_user, **kwargs)
            else:
                current = api.favorites(twitter_user, **kwargs)
            full_tweets.extend(current)
        print('full_tweets')
        for tweet in full_tweets:
            text = re.sub(r'(https?://\S+)', '', tweet.text)
            score = tweet.favorite_count + tweet.retweet_count
            if tweet.in_reply_to_status_id_str:
                score -= 15
            # Only tweets with at least five words.
            if len(re.split(r'[^0-9A-Za-z]+', text)) > min_words:
                print('translate')
                text = self.translate_it_en(text)
                tweets.append((text, score))
        return tweets




    def translate_it_en(self, text):
        translator = Translator(service_urls=['translate.googleapis.com'])
        try:
            result = translator.translate(text, dest='it')
        except : print('error translation ')
        return result.text

    #NOT USED
    def dataframe_(self):
        #find correlation between centrality and other measures
        filename = self.account + "_followers.json"
        follower_ids = self.account + "_followers_ids.json"
        user_objects = self.try_load_or_process(filename, self.get_user_objects, follower_ids)
        total_objects = len(user_objects)
        print(user_objects[0])
        '''df = pd.DataFrame(columns=['age', 'followers'])
        for user in user_objects:
            df.loc[len(df)] = [self.twitter_time_to_object(user['created_at']), 1]
        df.to_json('MasiWines_age_followers.json')'''
#
#download folllower of an account and create a graph where someone follow you
#calculate centrality with different measure

import networkx as nx
import network_followers




if __name__ == "__main__":
    # screen name of the twitter user to analyse
    target = 'MasiWines'

    consumer_key="aZQxSXaItLednaywvimyzJObu"
    consumer_secret="dh1ps8q9Ab4ylTIZ75B3yGbd2mAxDRWYsKN2Uo30AvSW2lUIfZ"
    access_token="1235494563730595840-qmcedLeJB2pOLeaj2Pnl0oJoaj25Mi"
    access_token_secret="UM7BnO4GdiYro2B0gLsVCLrSi8poSLblyGs0eN1PPTVpH"
    monkey_token ='13042ce730953f73a91c9916f8220edb6cccefb5'

    print("Processing target: " + target )

# create the graph
    obj = network_followers.Network_followers(consumer_key, consumer_secret, access_token, access_token_secret, monkey_token,target)
    followers_net= obj.get_direct_graph()

# some details of user
    obj.profile_details()

# Get a list of Twitter ids for followers of target account and save it and the insert in the graph
    filename = target + "_follower_ids.json"
    follower_ids = obj.try_load_or_process(filename, obj.get_follower_ids, target)
    number_followers = len(follower_ids)
    print(str(number_followers) + " followers")

# add list in the graph followers_net
    followers_net= obj.add_followers(followers_net, follower_ids)
    print(len(list(followers_net.nodes)))


# for each follower load his follower and add in the graph
    followers_net = obj.calculate_list_followers2(follower_ids,followers_net)
    nx.write_gexf(followers_net, "network_MasiWines.gexf")

#find 10 top influencer with different centrality measures
    obj.centrality_dataframe()

#obj.understand_users('MasiWines')



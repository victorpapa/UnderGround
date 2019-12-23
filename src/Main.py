from QueryData import Data_fetcher
from Post import Post
from Member import Member
from Utils import get_edit_distance, create_edge_table_csv, get_bow, get_n_grams, freq_to_pres, concat_feature_dicts
import os
import csv

# initially, similar_usernames contains low scores for similar usernames, 
# and high scores for different usernames. This function reverts this behavior.
def revert_weights(similar_usernames):

    maximum = 0

    for s in similar_usernames:
        maximum = max(maximum, s[2])

    for i in range(len(similar_usernames)):
        similar_usernames[i] = (similar_usernames[i][0], 
                                similar_usernames[i][1], 
                                maximum - similar_usernames[i][2] + 0.001)

    return similar_usernames

def get_similar_usernames(active_users):

    similar_usernames = []

    for i in range(len(active_users) - 1):
        for j in range(i+1, len(active_users)):
            u1 = active_users[i].Username
            u2 = active_users[j].Username
            dist = get_edit_distance(u1, u2)

            if dist <= 2:
                similar_usernames += [(u1, u2, dist)]

    similar_usernames = revert_weights(similar_usernames)

    return similar_usernames

def get_active_users(names_path):
    f = open(names_path, "r", encoding="utf8")
    df = Data_fetcher()
    ID = 0

    for l in f:
        l = l.split()
        
        for w in l:
            m = Member(Username=w, IdMember=ID)
            ID += 1
            df.add_member(m)

    return df.get_active_users()

# returns the dictionary of features for all the posts written by MemberID
# df is a reference to a data_fetcher object
# feature is a String, which is the type of feature we want to analyse
# n is for n-grams
# presence is for whether we want feeature presence or not
def get_features_dict(df, MemberID, feature, n = 1, presence = False):

    ret = {}

    posts = df.get_posts_written_by(MemberID)

    for p in posts:

        text = p.Content

        if feature == "bow":
            feat_dict = get_bow(text)
        elif feature == "n_grams":
            if n == 1: 
                print("Did you forget to set n when querying n_grams?")
            feat_dict = get_n_grams(text, n)
        else:
            print("Feature type " + feature + " not implemented.")

        if presence == True:
            feat_dict = freq_to_pres(feat_dict)

        concat_feature_dicts(ret, feat_dict)

    return ret

if __name__ == "__main__":

    names_path = os.path.join(os.getcwd(), "..\\res\\First_Names.txt")
    active_users = get_active_users(names_path)
    similar_usernames = get_similar_usernames(active_users)

    csv_file = open("..\\res\\similar_usernames.csv", "w")
    create_edge_table_csv(csv_file, similar_usernames)
    
from QueryData import Data
from Post import Post
from Member import Member
from Utils import get_edit_distance, create_edge_table_csv, get_bow, get_n_grams, freq_to_pres, concat_feature_dicts, shrink_dict, fill_feature_dict, tuples_to_dict, get_dict_keys, normalise_feature_vector, get_dist, get_conex_components_count, create_nodes_table_csv, get_date_from, get_00_time_from
import os
import csv
import re

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

# given a list of Member objects, this method will return triplets (a, b, x), where x is <= max_dist,
# where a and b are usernames (Strings) or IDs (Integers), and x is the reversed edit distance between them
# see the function reverse_weights() for the definition of reversed edit distance
def get_similar_usernames(active_users, max_dist):

    similar_usernames = []

    for i in range(len(active_users) - 1):
        for j in range(i+1, len(active_users)):
            u1 = active_users[i].Username
            u2 = active_users[j].Username

            id1 = active_users[i].IdMember
            id2 = active_users[j].IdMember

            if max_dist > 0:
                dist = get_edit_distance(u1, u2)
            elif max_dist == 0:
                if u1 == u2:
                    dist = 0
                else:
                    dist = 1

            if dist <= max_dist:
                # TODO make sure this gets fixed when needed
                # similar_usernames += [(u1, u2, dist)]
                # similar_usernames += [(u2, u1, dist)]
                similar_usernames += [(id1, id2, dist)]
                similar_usernames += [(id2, id1, dist)]
                    
    similar_usernames = revert_weights(similar_usernames)

    return similar_usernames

# this method creates a Data object containing all the members in names_path
def create_members_df(names_path):
    f = open(names_path, "r", encoding="utf-8")
    df = Data()
    total = 0

    for l in f:
        l = l.split()

        IdMember = l[0]
        Username = l[1]
        Database = l[2]
        aux = re.split("[(,)]", l[3])
        LastVisitDue = ()
        for x in aux:
            if x == "":
                continue
            LastVisitDue += (int(x),)
        
        # TODO maybe use the IdMember, will it be useful for something? If not, just keep using the index here (total)
        m = Member(total, Username=Username, Database=Database, LastVisitDue=LastVisitDue)
        df.add_member(m)

        total += 1

        if total == 40000:
            break
            

    print("The total number of members is " + str(total) + ".")

    return df

# aggregates all the vectors representing the posts written by IdMember, and returns
# the centre of mass of those vectors (if presence is False)
# df is a reference to a Data object
# feature is a String, which is the type of feature we want to analyse (BoW, N-grams etc.)
# n is for n-grams
# presence is for whether we want feeature presence or not
# TODO potentially make a function that returns a similar mapping, but which also maps each post to the vectors
# this function aggregates all the posts and returns the overall feature vector
def get_features_dict_written_by(IdMember, df, feature, presence, n):

    ret = {}

    posts = df.get_posts_written_by(IdMember)

    for p in posts:

        # TODO collapse this code and use the method below (get_features_dict_for_post)
        text = p.Content

        if feature == "bow":
            feat_dict = get_bow(text)
        elif feature == "n_grams":
            if n == 1: 
                print("Did you forget to set n when querying n_grams?")
            feat_dict = get_n_grams(text, n)
        else:
            print("Feature type " + feature + " not implemented.")

        concat_feature_dicts(ret, feat_dict)

    if presence == True:
        ret = freq_to_pres(ret)
    else:
        for i in range(len(ret)):
            ret[i] /= len(posts)

    return ret

def get_features_dict_for_post(post, feature, presence, n = 1):

    ret = {}

    text = post.Content

    if feature == "bow":
        feat_dict = get_bow(text)
    elif feature == "n_grams":
        if n == 1: 
            print("Did you forget to set n when querying n_grams?")
        feat_dict = get_n_grams(text, n)
    else:
        print("Feature type " + feature + " not implemented.")

    concat_feature_dicts(ret, feat_dict)

    if presence == True:
        ret = freq_to_pres(ret)

    return ret


if __name__ == "__main__":

    # Create a csv containing a node table and an edge table for all the users described in names_path

    names_path = os.path.join(os.getcwd(), "..\\res\\Members.txt")
    df = create_members_df(names_path)
    active_users = df.get_active_users() # list of Member objects
    print("The total number of active members is " + str(len(active_users)) + ".")
    similar_usernames_tuples = get_similar_usernames(active_users, 0)
    similar_usernames_dict = tuples_to_dict(similar_usernames_tuples)

    centroids = []
    features = {}
    feat_type = "bow"
    n = 1

    edges_csv_file = open("..\\res\\similar_usernames_edges.csv", "w", encoding = "utf-8")
    nodes_csv_file = open("..\\res\\similar_usernames_nodes.csv", "w", encoding = "utf-8")
    create_edge_table_csv(edges_csv_file, similar_usernames_tuples)
    create_nodes_table_csv(nodes_csv_file, [member.Username for member in active_users])
    edges_csv_file.close()
    nodes_csv_file.close()

    conex_components_count = get_conex_components_count(similar_usernames_dict)
    print("The number of conex components is " + str(conex_components_count) + ".")

    exit()

    # Obtain the clusters
    # TODO test this
    
    clusters = []

    for user in similar_usernames_dict:
        cluster = [user]
        for (n, _) in similar_usernames_dict[user]:
            cluster += [n]

    for cluster in clusters:

        # Obtain the vector for each user

        user_vectors = {}
        use_presence = False

        for user in cluster:
            d = get_features_dict_written_by(user.IdMember, 
                                            df = df, 
                                            feature = feat_type, 
                                            presence = use_presence,
                                            n = n)

            user_vectors[user] = d

        # Aggregate all the keys to get the dimensions
        aggregated_keys = []

        for user in user_vectors:
            vector = user_vectors[user]
            
            for k in vector:
                aggregated_keys += [k]

        # Fill all the vectors to contain all the dimensions
        for user in user_vectors:
            print(user_vectors[user])
            # And also normalise them if presence isn't used, distribution is more important
            if not use_presence:
                normalise_feature_vector(user_vectors[user])

            fill_feature_dict(user_vectors[user], aggregated_keys)
            print(user_vectors[user])

        # iterate through users, and assign each of their posts to one of the other users
        # the most chosen user will be suspected to be the same user as the one we are analysing

        suspects = {}

        for user in user_vectors:
            posts = df.get_posts_written_by(user)
            labels = []

            for p in posts:
                p_dict = get_features_dict_for_post(post = p, 
                                                    feature = feat_type, 
                                                    presence = use_presence,
                                                    n = n)

                fill_feature_dict(p_dict, aggregated_keys)
                
                min_dist = -1
                for other in user_vectors:
                    if other == user:
                        continue

                    dist = get_dist(p_dict, user_vectors[other])

                    if min_dist == -1 or dist < min_dist:
                        min_dist = dist
                        user_label = other

                labels[user_label] += 1
        
            maximum = -1
            for user_label in labels:
                if maximum == -1 or labels[user_label] > maximum:
                    maximum = labels[user_label]
                    closest_user = user_label

            suspects[user] = closest_user

        print(suspects)
        cc = get_conex_components_count(suspects)





    
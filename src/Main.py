from Data import Data
from Post import Post
from Member import Member
from postgres_interface import postgres_interface
from Utils import get_edit_distance, get_bow, get_n_grams, freq_to_pres, shrink_dict, fill_feature_dict, tuples_to_dict, get_dict_keys, get_dict_values, normalise_feature_vector, get_dist, get_conex_components_count, get_clusters
import os
import csv
import re
import logging

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
def get_similar_usernames_and_dbs(active_users, max_dist):

    similar_usernames = []
    similar_dbs = {}

    for i in range(len(active_users) - 1):
        for j in range(i+1, len(active_users)):
            u1 = active_users[i].Username
            u2 = active_users[j].Username

            id1 = active_users[i].IdMember
            id2 = active_users[j].IdMember

            db1 = active_users[i].Database
            db2 = active_users[j].Database

            if db1 > db2:
                db3 = db1
                db1 = db2
                db2 = db3

            if max_dist > 0:
                dist = get_edit_distance(u1, u2)
            elif max_dist == 0:
                if u1 == u2:
                    dist = 0
                else:
                    dist = 1

            if dist <= max_dist:
                # TODO make sure this gets changed when needed
                # similar_usernames += [(u1, u2, dist)]
                # similar_usernames += [(u2, u1, dist)]
                similar_usernames += [(id1, id2, dist)]
                similar_usernames += [(id2, id1, dist)]

                if (db1, db2) in similar_dbs:
                    similar_dbs[(db1, db2)] += 1
                else:
                    similar_dbs[(db1, db2)] = 1
                    
    similar_usernames = revert_weights(similar_usernames)

    return (similar_usernames, similar_dbs)

# Creates a csv file containing an edge table for building a graph
# is not tested
# to_write needs to be a list of 3-tuples
def create_edge_table_csv(csv_file_handler, to_write):
    csv_writer = csv.writer(csv_file_handler, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow(["Source", "Target", "Weight", "Type"])
    for w in to_write:
        csv_writer.writerow([w[0], w[1], w[2], "Undirected"])

# Creates a csv file containing a nodes table for building a graph
# input: output file handle and list of member objects
# is not tested
def create_nodes_table_csv(csv_file_handler, members):
    csv_writer = csv.writer(csv_file_handler, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow(["Id", "Label"])

    for member in members:
        id_member = member.IdMember
        username = member.Username
        csv_writer.writerow([str(id_member), username])

# writes the contents of the dictionary to the file specified
def write_dict_to_file(dict_to_write, file_name):
    g = open(file_name, "w+", encoding="utf-8")
    for k in dict_to_write:
        g.write(str(k) + ": " + str(dict_to_write[k]) + "\n")
    g.close()

# this method creates a Data object containing all the Members in names_path
def create_members_df(names_path):
    f = open(names_path, "r", encoding="utf-8")
    df = Data()

    for l in f:
        l = l.split()

        if len(l) < 4:
            logging.warning("Skipped " + str(l) + ", invalid Member object format. (probably whitespace username)")
            continue

        IdMember = int(l[0])
        Username = l[1]
        index = 2

        while "crimebb" not in l[index].lower():
            Username += " " + l[index]
            index += 1

        Database = l[index]
        aux = re.split("[(,)]", l[index + 1])
        LastVisitDue = ()
        for x in aux:
            if x == "":
                continue
            LastVisitDue += (int(x),)

        m = Member(IdMember = IdMember, Username=Username, Database=Database, LastVisitDue=LastVisitDue)
        df.add_member(m)

            
    total = IdMember + 1 # because we index from 0
    logging.debug("The total number of members is " + str(total) + ".")

    return df

# returns a list of post objects full of posts written by user
def get_posts_from(user, psql_interface):

    #TODO I see that in psql the posts returned contain + signs in between the lines, is that the case here too?
    #TODO posts contain many links, will have to do some input sanitisation and only analyse the actuals words
    posts = []
    raw_posts = pi.get_posts_from(user.IdMember, user.Database)

    for raw_post in raw_posts:
        post_ID = raw_post[0]
        author_ID = raw_post[1]
        content = raw_post[2]

        posts += [Post(IdPost=post_ID, Author=author_ID, Content=content)]

    return posts

# aggregates all the vectors representing the posts written by IdMember, and returns
# the centre of mass of those vectors (if presence is False)
# df is a reference to a Data object
# feature is a String, which is the type of feature we want to analyse (BoW, N-grams etc.)
# n is for n-grams
# presence is for whether we want feeature presence or not
# TODO potentially make a function that returns a similar mapping, but which also maps each post to the vectors
# this function does the opposite, it aggregates all the posts and returns the overall feature vector
def get_features_dict_written_by(user, psql_interface, feature, presence, n):

    ret = {}
    IdMember = user.IdMember
    posts = get_posts_from(user, psql_interface)

    if len(posts) == 0:
        # print("User " + str(user.IdMember) + " from " + user.Database + " has not written any posts.")
        return {}

    for p in posts:

        # TODO collapse this code and use the method below (get_features_dict_for_post)
        text = p.Content

        if feature == "bow":
            feat_dict = get_bow(text)
        elif feature == "n_grams":
            if n == 1: 
                logging.error("Did you forget to set n when querying n_grams?")
            feat_dict = get_n_grams(text, n)
        else:
            logging.critical("Feature type " + feature + " not implemented.")

        for f in feat_dict:
            if f in ret:
                ret[f] += feat_dict[f]
            else:
                ret[f] = feat_dict[f]

    if presence == True:
        ret = freq_to_pres(ret)
    else:
        for i in ret:
            ret[i] /= len(posts)

    return ret

# returns the dictionary of features for the given post
def get_features_dict_for_post(post, feature, presence, n = 1):

    ret = {}

    text = post.Content

    if feature == "bow":
        feat_dict = get_bow(text)
    elif feature == "n_grams":
        if n == 1: 
            logging.error("Did you forget to set n when querying n_grams?")
        feat_dict = get_n_grams(text, n)
    else:
        logging.critical("Feature type " + feature + " not implemented.")

    
    ret.update(feat_dict)

    if presence == True:
        ret = freq_to_pres(ret)

    return ret


if __name__ == "__main__":

    os.chdir("D:\\Program Files (x86)\\Courses II\\Dissertation\\src")
    logging.basicConfig(filename='log.txt',level=logging.DEBUG)

    # Create a csv containing a node table and an edge table for all the users described in names_path

    names_path = os.path.join(os.getcwd(), "..\\res\\Members.txt")
    df = create_members_df(names_path)
    active_users = df.get_active_users() # list of Member objects
    logging.debug("The total number of active members is " + str(len(active_users)) + ".")
    (similar_usernames_tuples, similar_dbs_dict) = get_similar_usernames_and_dbs(active_users, 0)
    # sorts dictionary by 
    similar_dbs_dict = {k: v for k, v in sorted(similar_dbs_dict.items(), key=lambda item: item[1], reverse=True)}
    similar_usernames_dict = tuples_to_dict(similar_usernames_tuples)

    similar_dbs_file = "..\\res\\similar_dbs.txt"
    write_dict_to_file(similar_dbs_dict, similar_dbs_file)

    edges_csv_file = open("..\\res\\similar_usernames_edges.csv", "w", encoding = "utf-8")
    nodes_csv_file = open("..\\res\\similar_usernames_nodes.csv", "w", encoding = "utf-8")
    create_edge_table_csv(edges_csv_file, similar_usernames_tuples)
    create_nodes_table_csv(nodes_csv_file, active_users)
    edges_csv_file.close()
    nodes_csv_file.close()

    conex_components_count = get_conex_components_count(similar_usernames_dict)
    logging.debug("The number of conex components is " + str(conex_components_count) + ".")

    centroids = []
    features = {}
    feat_type = "bow"
    use_presence = False
    pi = postgres_interface()
    pi.start_server()
    n = 1

    # Obtain the clusters
    # TODO test this
    
    id_clusters = get_clusters(similar_usernames_dict)

    clusters = []
    for id_cluster in id_clusters:
        cluster = []
        for idc in id_cluster:
            cluster += [df.get_user_by_id(idc)]

        clusters += [cluster]

    for i in range(len(clusters)):
        
        cluster = clusters[i]
        # Obtain the vector for each user

        logging.debug("The users are:")
        for u in cluster:
            logging.debug(str(u.IdMember) + " " + str(u.Database))
        logging.debug("\n")

        user_dicts = {}

        for j in range(len(cluster)):
            user = cluster[j]
            d = get_features_dict_written_by(user = user, 
                                             psql_interface = pi, 
                                             feature = feat_type, 
                                             presence = use_presence,
                                             n = n)

            if d != {}:
                user_dicts[user] = d

        suspects = {}

        if len(user_dicts) <= 1:
            # print("There are not enough users with posts in the cluster.")
            if len(user_dicts) == 1:
                for user in user_dicts:
                    suspects.update({user:user})
            # for suspect in suspects:
                # print(suspect.Username + " " + suspect.Database + " -----> " + suspects[suspect].Username + " " + suspect.Database)
            continue

        # Aggregate all the keys to get the dimensions
        aggregated_keys = set()

        for user in user_dicts:
            vector = user_dicts[user]
            
            for k in vector:
                aggregated_keys.add(k)

        # Fill all the vectors to contain all the dimensions
        for user in user_dicts:
            # And also normalise them if presence isn't used, distribution is more important
            if not use_presence:
                normalise_feature_vector(user_dicts[user])

            fill_feature_dict(user_dicts[user], aggregated_keys)

        # iterate through users, and assign each of their posts to one of the other users
        # the most chosen user will be suspected to be the same user as the one we are analysing

        for user in user_dicts:
            posts = get_posts_from(user=user, psql_interface=pi)
            labels = {}

            for p in posts:
                p_dict = get_features_dict_for_post(post = p, 
                                                    feature = feat_type, 
                                                    presence = use_presence,
                                                    n = n)
                                                    
                fill_feature_dict(p_dict, aggregated_keys)

                min_dist = -1
                for other in user_dicts:
                    if other == user:
                        continue
                    
                    v1 = []
                    v2 = []
                    for k in p_dict:
                        v1 += [p_dict[k]]
                        #TODO This try block shouldn't be here. After fixing the issue, remove it
                        try:
                            v2 += [user_dicts[other][k]]
                        except:
                            v2 += [0]
                            logging.warning("Couldn't find this key " + str(k) + ".")

                    dist = get_dist(v1, v2)

                    if min_dist == -1 or dist < min_dist:
                        min_dist = dist
                        user_label = other

                if user_label in labels:
                    labels[user_label] += 1
                else:
                    labels[user_label] = 1
        
            maximum = -1
            
            for user_label in labels:
                if maximum == -1 or labels[user_label] > maximum:
                    maximum = labels[user_label]
                    closest_user = user_label

            suspects.update({user:closest_user})

        for suspect in suspects:
            logging.debug(suspect.Username + " " + suspect.Database + " -----> " + suspects[suspect].Username + " " + suspects[suspect].Database)
        # cc = get_conex_components_count(suspects)

    pi.stop_server()





    
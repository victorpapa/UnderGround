from Data import Data
from Post import Post
from Member import Member
from Postgres_interface import Postgres_interface
from Utils import get_edit_distance, get_bow, get_n_grams, freq_to_pres, shrink_dict, fill_feature_dict, tuples_to_dict, get_dict_keys, get_dict_values, normalise_feature_vector, get_dist, get_connected_components_count, get_strongly_connected_components_count, get_connected_components, timestamped
from datetime import datetime
import os
import csv
import re
import logging
from sklearn.cluster import KMeans
from copkmeans.cop_kmeans import cop_kmeans
from matplotlib import pyplot as plt

# initially, similar_usernames contains 3-tuples with low scores for similar usernames, 
# and high scores for more different, but still similar usernames. This function reverses this behavior.
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
def get_similar_usernames_and_dbs(active_members, max_dist):

    similar_usernames_global = []
    similar_dbs = {}

    for i in range(len(active_members) - 1):
        for j in range(i+1, len(active_members)):
            u1 = active_members[i].Username
            u2 = active_members[j].Username

            global_id1 = active_members[i].GlobalId
            global_id2 = active_members[j].GlobalId

            db1 = active_members[i].Database
            db2 = active_members[j].Database

            # sorting them to make sure I can keep track of the number of pairs of users with identical
            # usernames per pair of similar databases
            # for ex, I don't want hack-forums -> mpgh to be diff from mpgh -> hack-forums
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
                # change between usernames and IDs when needed
                # similar_usernames += [(u1, u2, dist)]
                # similar_usernames += [(u2, u1, dist)]
                similar_usernames_global += [(global_id1, global_id2, dist)]
                similar_usernames_global += [(global_id2, global_id1, dist)]

                if (db1, db2) in similar_dbs:
                    similar_dbs[(db1, db2)] += 1
                else:
                    similar_dbs[(db1, db2)] = 1
                    
    similar_usernames_global = revert_weights(similar_usernames_global)

    return (similar_usernames_global, similar_dbs)

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
def create_members_df(members_folder, limit):
    members_files_names = os.listdir(members_folder)
    file_count = len(members_files_names)
    # make sure to use int division to get an integer limit
    limit //= file_count # limit is now the per-file limit, instead of the overall limit
    orig_path = os.getcwd()
    os.chdir(members_folder)
    total = 0
    df = Data()

    for member_file_name in members_files_names:

        f = open(member_file_name, "r", encoding="utf-8")
        curr_file_member_count = 0

        for l in f:
            l = l.split()

            if len(l) < 5:
                # logging.warning(timestamped("Skipped " + str(l) + ", invalid Member object format. (probably whitespace username)"))
                continue

            GlobalId = int(l[0])
            IdMember = int(l[1])

            Username = l[2]
            index = 3

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

            m = Member(GlobalId = GlobalId, IdMember = IdMember, Username=Username, Database=Database, LastVisitDue=LastVisitDue)
            df.add_member(m)
            curr_file_member_count += 1

            if limit != 0 and curr_file_member_count == limit:
                break

        f.close()

    logging.debug(timestamped("The total number of members is " + str(df.get_member_count()) + "."))

    # restore path (go back to src/)
    os.chdir(orig_path)

    return df

# Returns a tuple. See details below
# aggregates all the vectors representing the posts written by IdMember, and 

# ---------------------------------------------------------
# returns the centre of mass of those vectors (if presence is False)
# also returns a dictionary, mapping ecah post written by this member to its corresponding feature vector
# ---------------------------------------------------------

# df is a reference to a Data object
# feature is a String, which is the type of feature we want to analyse (BoW, N-grams etc.)
# n is for n-grams
# presence is for whether we want feeature presence or not
def get_features_dict_written_by(member, psql_interface, feature, presence, n):

    ret_aggregate = {}
    ret_per_post = {}

    posts = psql_interface.get_posts_from(member)

    for post in posts:

        curr_post_feat_dict = get_features_dict_for_post(post = post, feature = feature, presence = presence, n = n)

        for f in curr_post_feat_dict:
            if f in ret_aggregate:
                ret_aggregate[f] += curr_post_feat_dict[f]
            else:
                ret_aggregate[f] = curr_post_feat_dict[f]

        ret_per_post[post] = curr_post_feat_dict

    if presence == True:
        ret_aggregate = freq_to_pres(ret_aggregate)

        for post in ret_per_post:
            ret_per_post[post] = freq_to_pres(ret_per_post[post])
    else:
        for i in ret_aggregate:
            ret_aggregate[i] /= len(posts)

    return ret_aggregate, ret_per_post

# returns the dictionary of features for the given post
def get_features_dict_for_post(post, feature, presence, n = 1):

    ret = {}

    text = post.Content
    # have to provide a list of tokens to the get_bow and get_n_grams methods
    text = text.split()

    if feature == "bow":
        feat_dict = get_bow(text)
    elif feature == "n_grams":
        if n == 1: 
            logging.error(timestamped("Did you forget to set n when querying n_grams?"))
        feat_dict = get_n_grams(text, n)
    else:
        logging.critical(timestamped("Feature type " + feature + " not implemented."))

    
    ret.update(feat_dict)

    if presence == True:
        ret = freq_to_pres(ret)

    return ret

def write_metadata(metadata_file_handler, members_metadata):
    for member_metadata in members_metadata:
        for metadata in member_metadata:
            to_write = ""
            for field in metadata:
                if field != "":
                    to_write += str(field) + " "
                else:
                    to_write = ""
                    break
            
            if to_write != "":
                metadata_file_handler.write(to_write + "\n")

# the two metadata parameters will each be a list of lists, each containing one tuple with data about 
# a member that is because __run_command returns a list of tuples, each tuple representing a row 
# in the output of the command that was run by PSQL
def persist_metadata(all_members, active_members, psql_interface):
    all_members_metadata = psql_interface.get_members_metadata(all_members)
    active_members_metadata = psql_interface.get_members_metadata(active_members)

    # ---------------------------------------------------------------------- #

    metadata_file_name = os.path.join("..", *["res", "Members_metadata", "all_members_metadata.txt"])
    metadata_file_handler = open(metadata_file_name, "w+", encoding = "utf-8")
    write_metadata(metadata_file_handler, all_members_metadata)
    metadata_file_handler.close()

    # ----------------------------------------------------------------------#
    metadata_file_name = os.path.join("..", *["res", "Members_metadata", "active_members_metadata.txt"])
    metadata_file_handler = open(metadata_file_name, "w+", encoding = "utf-8")
    write_metadata(metadata_file_handler, active_members_metadata)
    metadata_file_handler.close()

def write_posts_avg_max(active_members, psql_interface):
    max_posts = 0
    active_post_avg = 0
    for active_member in active_members:
        # TODO should I store posts in Data or not?
        active_member_posts = psql_interface.get_posts_from(member = active_member)

        active_post_avg += len(active_member_posts)
        if len(active_member_posts) > max_posts:
            max_posts = len(active_member_posts)
    active_post_avg /= len(active_members)
    logging.debug(timestamped("The average number of posts for the active users is " + str(active_post_avg)))
    logging.debug(timestamped("The maximum number of posts for the active users is " + str(max_posts)))

def write_csv_data(similar_dbs_dict, similar_usernames_tuples_global, active_members):
    # sorts dictionary by the 2nd component (index 1) of each item in descending order
    similar_dbs_dict = {k: v for k, v in sorted(similar_dbs_dict.items(), key=lambda item: item[1], reverse=True)}

    similar_dbs_file = "..\\res\\similar_dbs.txt"
    write_dict_to_file(similar_dbs_dict, similar_dbs_file)

    edges_csv_file = open("..\\res\\similar_usernames_edges.csv", "w", encoding = "utf-8")
    nodes_csv_file = open("..\\res\\similar_usernames_nodes.csv", "w", encoding = "utf-8")
    create_edge_table_csv(edges_csv_file, similar_usernames_tuples_global)
    create_nodes_table_csv(nodes_csv_file, active_members)
    edges_csv_file.close()
    nodes_csv_file.close()

# creates 2 csv files: one containing all the edges in the similarity graph
#                      one containing all the nodes in the similarity graph
# returns the similarity graph edges as a dictionary
# also creates and writes the database similarity file, username similarity graph csv files (edges and nodes)
# and may also output the average and maximum number of posts written by the active users
def retrieve_similarity_graph(limit, write_csv, active_post_avg, psql_interface):
    # Create a csv containing a node table and an edge table for all the members described in names_path

    members_folder = os.path.join(os.getcwd(), *["..", "res", "Members"])
    df = create_members_df(members_folder, limit = limit)

    all_members = df.get_members()
    active_members = df.get_active_members() # list of Member objects
    logging.debug(timestamped("The total number of active members is " + str(len(active_members)) + "."))

    
    persist_metadata(all_members = all_members, 
                     active_members = active_members, 
                     psql_interface = psql_interface)

    logging.info("Members metadata was written.")

    # ----------------------------------------------------------------------#

    if active_post_avg == True:
        write_posts_avg_max(active_members = active_members,
                            psql_interface = psql_interface)
    

    similar_usernames_tuples_global, similar_dbs_dict = get_similar_usernames_and_dbs(active_members, 
                                                                                      max_dist = 0)

    if write_csv == True:
        write_csv_data(similar_dbs_dict, similar_usernames_tuples_global, active_members)


    similar_usernames_dict_global = tuples_to_dict(similar_usernames_tuples_global)
    connected_components_count = get_connected_components_count(similar_usernames_dict_global)
    logging.debug(timestamped("The number of connected components is " + str(connected_components_count) + ".\n"))

    return similar_usernames_dict_global, df

# given the similarity graph edges as a dictionary, return the connected components
def get_member_clusters(similar_usernames_dict, df):

    # First obtain the global id clusters
    id_clusters = get_connected_components(similar_usernames_dict)

    # Obtain the member clusters from the id clusters
    member_clusters = []
    for id_cluster in id_clusters:
        member_cluster = []
        for idc in id_cluster:
            member_cluster += [df.get_member_by_GlobalId(idc)]

        member_clusters += [member_cluster]

    return member_clusters

# initialising the logging file and setting the correct working directory
def init_env():
    os.chdir("D:\\Program Files (x86)\\Courses II\\Dissertation\\res")
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger_handler = logging.FileHandler("log_main.txt", "w", encoding="utf-8")
    logger_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(logger_handler)
    os.chdir("D:\\Program Files (x86)\\Courses II\\Dissertation\\src")

def get_member_dicts_from_cluster(cluster):

    # Obtain the vector for each member

    logging.debug(timestamped("The members are:"))
    for u in cluster:
        logging.debug(timestamped(str(u.IdMember) + " " + str(u.Database)))

    member_aggr_dicts = {}
    member_per_post_dicts = {}

    for i in range(len(cluster)):
        member = cluster[i]
        member_aggr_feat_dict, member_per_post_feat_dict = get_features_dict_written_by(member = member, 
                                                                                    psql_interface = pi, 
                                                                                    feature = feat_type, 
                                                                                    presence = use_presence,
                                                                                    n = n)

        member_aggr_dicts[member] = member_aggr_feat_dict
        member_per_post_dicts[member] = member_per_post_feat_dict

    # Aggregate all the keys to get the dimensions
    aggregated_keys = set()

    for member in member_aggr_dicts:
        vector = member_aggr_dicts[member]
        
        for k in vector:
            aggregated_keys.add(k)

    # Fill all the vectors to contain all the dimensions
    for member in member_aggr_dicts:
        # And also normalise them if presence isn't used, distribution is more important
        if not use_presence:
            normalise_feature_vector(member_aggr_dicts[member])

        fill_feature_dict(member_aggr_dicts[member], aggregated_keys)
        curr_member_posts_dicts = member_per_post_dicts[member]

        for p in curr_member_posts_dicts:
            if not use_presence:
                normalise_feature_vector(curr_member_posts_dicts[p])

            # check that this changes, and then leave a comment stating the result
            # it works fine
            fill_feature_dict(curr_member_posts_dicts[p], aggregated_keys)

    return member_aggr_dicts, member_per_post_dicts

# only correctly identifies (really) tight clusters
# works 50% of the time (by chance) with groups of 2 users
def get_suspects_intutitively(clusters):
    for cluster in clusters:
        
        member_aggr_dicts, member_per_post_dicts = get_member_dicts_from_cluster(cluster = cluster)

        suspects = {}

        # iterate through members, and assign each of their posts to one of the other members
        # the most chosen member will be suspected to be the same member as the one we are analysing

        for source_member in member_per_post_dicts:
            # curr_member_posts_dicts is a dictionary that maps a member to a dictionary, which maps each post
            # written by source_member to its feature vector
            curr_member_posts_dicts = member_per_post_dicts[source_member]
            labels = {}

            for p in curr_member_posts_dicts:
                # curr_post_dict is a dictionary, which maps each post
                # written by the source_member to its feature vector
                
                curr_post_dict = curr_member_posts_dicts[p]

                min_dist = -1
                for target_member in member_aggr_dicts:
                    if target_member == source_member:
                        # we want a different member
                        continue
                    
                    v1 = []
                    v2 = []
                    for k in curr_post_dict:
                        v1 += [curr_post_dict[k]]
                        v2 += [member_aggr_dicts[target_member][k]]

                    dist = get_dist(v1, v2)

                    if min_dist == -1 or dist < min_dist:
                        min_dist = dist
                        member_label = target_member

                if member_label in labels:
                    labels[member_label] += 1
                else:
                    labels[member_label] = 1
        
            maximum = -1
            
            for member_label in labels:
                if maximum == -1 or labels[member_label] > maximum:
                    maximum = labels[member_label]
                    closest_member = member_label

            suspects.update({source_member:[closest_member]})

        # suspects is a dict, mapping Member objects to lists of Member objects, each list having 1 item
        for suspect in suspects:
            logging.info(timestamped(suspect.Username + " " + suspect.Database + " -----> " + suspects[suspect][0].Username + " " + suspects[suspect][0].Database))
        
        # Here we want STRONGLY CONNECTED COMPONENTS
        
        #  o
        #  ▲ 
        #  | 
        #  ▼                        o
        #  o < - - - - - - - - - - /

        # In this case, I want the program to output 2 components, rather than 1
        cc = get_strongly_connected_components_count(suspects)
        logging.info(timestamped("This cluster thus forms " + str(cc) + " strongly connected subclusters of suspects.\n"))

def get_suspects_k_means(clusters):
    
    for cluster in clusters:

        # member_aggr_dicts is not used in this method
        member_aggr_dicts, member_per_post_dicts = get_member_dicts_from_cluster(cluster = cluster)

        feature_matrix = []
        for member in member_per_post_dicts:
            for post in member_per_post_dicts[member]:
                feature_matrix.append(member_per_post_dicts[member][post])

        # have to sort the features in order to be able to properly analyse them,
        # as we'll only keep the feature values, the keys will be forgotten, 
        # as they are not needed by the clusterer/classifier
        sorted_keys = sorted(get_dict_keys(feature_matrix[0]))

        feature_matrix = [[post_dict[key] for key in sorted_keys] for post_dict in feature_matrix]

        suspect_count = len(cluster)

    
        wcss = []

        for i in range(1, suspect_count + 1):
            k_means = KMeans(n_clusters = i, 
                            init = "k-means++",    
                            max_iter = 300,
                            n_init = 10,
                            random_state = 0)
            k_means.fit(feature_matrix)
            wcss.append(k_means.inertia_)
        
        # TODO instead of plotting a graph and finding K manually, see if it's worth coding the
        # Elbow method using some maths instead
        plt.plot(range(1, suspect_count + 1), wcss)
        plt.title('Elbow Method')
        plt.xlabel('Number of clusters')
        plt.ylabel('WCSS')
        plt.show()

# TODO cite this library
# https://github.com/Behrouz-Babaki/COP-Kmeans
def get_suspects_constrained_k_means(clusters):
    for cluster in clusters:


        # member_aggr_dicts is not used in this method
        member_aggr_dicts, member_per_post_dicts = get_member_dicts_from_cluster(cluster = cluster)

        feature_matrix = []
        for member in member_per_post_dicts:
            for post in member_per_post_dicts[member]:
                feature_matrix.append(member_per_post_dicts[member][post])

        print(len(feature_matrix))
        # have to sort the features in order to be able to properly analyse them,
        # as we'll only keep the feature values, the keys will be forgotten, 
        # as they are not needed by the clusterer/classifier
        sorted_keys = sorted(get_dict_keys(feature_matrix[0]))

        feature_matrix = [[post_dict[key] for key in sorted_keys] for post_dict in feature_matrix]

        suspect_count = len(cluster)

        must_link = []
        cannot_link = []
        wcss = []

        for i in range(1, suspect_count + 1):
            clusters, centres = cop_kmeans(dataset = feature_matrix,
                                           k = i, 
                                           ml = must_link,
                                           cl = cannot_link)
            current_wcss = 0
            for j in range(len(clusters)):
                cluster_index = clusters[j]
                current_wcss += get_dist(feature_matrix[j], centres[cluster_index]) ** 2

            wcss.append(current_wcss)
        
        # TODO instead of plotting a graph and finding K manually, see if it's worth coding the
        # Elbow method using some maths instead
        plt.plot(range(1, suspect_count + 1), wcss)
        plt.title('Elbow Method')
        plt.xlabel('Number of clusters')
        plt.ylabel('WCSS')
        plt.show()

if __name__ == "__main__":

    init_env()

    # TODO some of these variables can be seen by the get_suspects methods. Do some tests and see how scopes work
    centroids = []
    features = {}
    feat_type = "bow"
    use_presence = False
    n = 1
    
    pi = Postgres_interface()
    pi.start_server()

    # instead of getting the first <limit> members, get the first <limit / number of databases> members
    # in order to get the most recent ones from all of them

    # another sol which is even better, and is implemented in this code (Postgres_interface.py),
    # is to sort them alphabetically and get the first few from each database
    similar_usernames_dict, df = retrieve_similarity_graph(limit = 1000, 
                                                           write_csv = True,
                                                           active_post_avg = True, 
                                                           psql_interface = pi)
    # clusters will be a list of lists of Member objects
    clusters = get_member_clusters(similar_usernames_dict = similar_usernames_dict, df = df)

    # ---------------------------

    # get_suspects_intutitively(clusters)
    get_suspects_k_means(clusters)
    get_suspects_constrained_k_means(clusters)

    # TODO
    # pi.stop_server()





    
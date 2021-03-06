from Data import Data
from Post import Post
from Member import Member
from Postgres_interface import Postgres_interface
from Utils import get_edit_distance, tuples_to_dict, get_connected_components_count, get_connected_components, timestamped
from datetime import datetime
from suspect_detection import get_suspects
import os
import csv
import re
import logging

# TODO move all comments to be docstrings for each method and class

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

# TODO The TotalPosts field is invalid, use the count of get_posts_from_user instead
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
    # all_members_metadata = []
    # for i in range((len(all_members) + 99) // 100):
    #     curr_metadata = psql_interface.get_members_metadata(all_members[100 * i : 100 * (i+1)])
    #     all_members_metadata += curr_metadata
    #     print(str((i+1) * 100 * 100 / len(all_members)) + "%")
    # all_members_metadata = psql_interface.get_members_metadata(all_members)

    active_members_metadata = []
    for i in range((len(active_members) + 99) // 100):
        curr_metadata = psql_interface.get_members_metadata(active_members[100 * i : 100 * (i+1)])
        active_members_metadata += curr_metadata
        print(str((i+1) * 100 * 100 / len(active_members)) + "%")
    # active_members_metadata = psql_interface.get_members_metadata(active_members)

    # ---------------------------------------------------------------------- #

    # metadata_file_name = os.path.join("..", *["out", "Members_metadata", "all_members_metadata.txt"])
    # metadata_file_handler = open(metadata_file_name, "w+", encoding = "utf-8")
    # write_metadata(metadata_file_handler, all_members_metadata)
    # metadata_file_handler.close()

    # ----------------------------------------------------------------------#
    metadata_file_name = os.path.join("..", *["out", "Members_metadata", "active_members_metadata.txt"])
    metadata_file_handler = open(metadata_file_name, "w+", encoding = "utf-8")
    write_metadata(metadata_file_handler, active_members_metadata)
    metadata_file_handler.close()

def persist_best_members(active_members, psql_interface):
    max_posts = 0
    active_post_avg = 0
    best_members = {}
    index = 0
    for active_member in active_members:

        active_member_posts = psql_interface.get_posts_from(member = active_member)
        index += 1

        if index % 100 == 0:
            print(str(index * 100 / len(active_members)) + "%")

        active_post_avg += len(active_member_posts)
        if len(active_member_posts) > 10:
            best_members[active_member] = len(active_member_posts)

        if len(active_member_posts) > max_posts:
            max_posts = len(active_member_posts)
            best_member = active_member

    active_post_avg /= len(active_members)
    logging.debug(timestamped("The average number of posts for the active users is " + str(active_post_avg)))
    logging.debug(timestamped("The maximum number of posts for the active users is " + str(max_posts)))
    
    best_members = {k: v for k, v in sorted(best_members.items(), key=lambda item: item[1], reverse=True)}

    best_members_file = os.path.join("..", *["out", "best_members.txt"])
    g = open(best_members_file, "w+", encoding="utf-8")
    for member in best_members:
        g.write(str(member.IdMember) + " " + member.Database + " " + str(best_members[member]) + "\n")
        logging.info(str(member.IdMember) + " " + member.Database + " " + str(best_members[member]))
    g.close()

def write_csv_data(similar_dbs_dict, similar_usernames_tuples_global, active_members):
    # sorts dictionary by the 2nd component (index 1) of each item in descending order
    similar_dbs_dict = {k: v for k, v in sorted(similar_dbs_dict.items(), key=lambda item: item[1], reverse=True)}

    similar_dbs_file = "..\\out\\similar_dbs.txt"
    write_dict_to_file(similar_dbs_dict, similar_dbs_file)

    edges_csv_file = open("..\\out\\similar_usernames_edges.csv", "w", encoding = "utf-8")
    nodes_csv_file = open("..\\out\\similar_usernames_nodes.csv", "w", encoding = "utf-8")
    create_edge_table_csv(edges_csv_file, similar_usernames_tuples_global)
    create_nodes_table_csv(nodes_csv_file, active_members)
    edges_csv_file.close()
    nodes_csv_file.close()

# creates 2 csv files: one containing all the edges in the similarity graph
#                      one containing all the nodes in the similarity graph
# returns the similarity graph edges as a dictionary
# also creates and writes the database similarity file, username similarity graph csv files (edges and nodes)
# and may also output the average and maximum number of posts written by the active users
def retrieve_similarity_graph(limit, write_metadata, write_csv, write_best_members, psql_interface):
    # Create a csv containing a node table and an edge table for all the members described in names_path

    members_folder = os.path.join(os.getcwd(), *["..", "res", "Members"])
    df = create_members_df(members_folder, limit = limit)

    all_members = df.get_members()
    active_members = df.get_active_members() # list of Member objects
    logging.debug(timestamped("The total number of active members is " + str(len(active_members)) + "."))

    
    if write_metadata == True:
        persist_metadata(all_members = all_members, 
                        active_members = active_members, 
                        psql_interface = psql_interface)

        logging.info("Members metadata was written.")
    else:
        logging.info("Skipped writing member metadata.")

    # ----------------------------------------------------------------------#

    if write_best_members == True:
        persist_best_members(active_members = active_members,
                           psql_interface = psql_interface)
    else:
        logging.info("Skipped writing best members.")
    

    similar_usernames_tuples_global, similar_dbs_dict = get_similar_usernames_and_dbs(active_members, 
                                                                                      max_dist = 0)

    if write_csv == True:
        write_csv_data(similar_dbs_dict, similar_usernames_tuples_global, active_members)
    else:
        logging.info("Skipped writing csvs.")

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
    os.chdir("D:\\Program Files (x86)\\Courses II\\Dissertation\\log")
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger_handler = logging.FileHandler("log_main.txt", "w", encoding="utf-8")
    logger_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(logger_handler)
    os.chdir("D:\\Program Files (x86)\\Courses II\\Dissertation\\src")

if __name__ == "__main__":

    init_env()

    # TODO some of these variables can be seen by the get_suspects methods. Do some tests and see how scopes work
    # TODO DEBUG findfont: score(<Font 'Trebuchet MS' (trebuc.ttf) normal normal 400 normal>) = 10.05 
    # solve that ^
    
    pi = Postgres_interface()
    pi.start_server()

    # instead of getting the first <limit> members, get the first <limit / number of databases> members
    # in order to get the most recent ones from all of them

    # another sol which is even better, and is implemented in this code (Postgres_interface.py),
    # is to sort them alphabetically and get the first few from each database
    similar_usernames_dict, df = retrieve_similarity_graph(limit = 0, 
                                                           write_metadata = False,
                                                           write_csv = False,
                                                           write_best_members = False, 
                                                           psql_interface = pi)
    # clusters will be a list of lists of Member objects
    clusters = get_member_clusters(similar_usernames_dict = similar_usernames_dict, df = df)

    # --------------------------- #

    feat_type = ["bow", "n_grams", "function_words_bow"]
    use_presence = False
    n = 5
    posts_args = (feat_type, use_presence, n)

    results = get_suspects(method = "intuitive", 
                            clusters = clusters, 
                            psql_interface = pi, 
                            posts_args = posts_args, 
                            reduce_dim = True,
                            plot = False,
                            dim_reduction = "tsne",
                            n_components = 2, # setting this to a different value while still plotting will lead
                                              # to an error
                            testing = False)

    total = len(results)
    total_groups = 0
    for i in results:
        group_size, group_labels = results[i]
        total_groups += group_size
    logging.info("There are " + str(total_groups) + " people who own more than 1 account.")

    # TODO
    # pi.stop_server()


    
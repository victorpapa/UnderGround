from Post import Post
from Member import Member
from suspect_detection import get_suspects
from Postgres_interface import Postgres_interface
from random import choice, sample
import os
import logging

def get_test_members():
    test_members = []

    test_members_file = os.path.join("..", *["out", "best_members.txt"])
    f = open(test_members_file, "r", encoding="utf-8")
    for line in f:
        line = line.split()
        IdMember = int(line[0])
        Database = line[1]

        curr_member = Member(IdMember = IdMember, Database = Database)
        test_members.append(curr_member)

    # get 50 random members
    return sample(test_members, 50)


# initialising the logging file and setting the correct working directory
def init_env():
    os.chdir("D:\\Program Files (x86)\\Courses II\\Dissertation\\log")
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger_handler = logging.FileHandler("log_evaluator.txt", "w", encoding="utf-8")
    logger_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(logger_handler)
    os.chdir("D:\\Program Files (x86)\\Courses II\\Dissertation\\src")

if __name__ == "__main__":

    init_env()
    
    test_members = get_test_members()
    psql_interface = Postgres_interface()
    psql_interface.start_server()

    # create a list of N users with a lot of posts
    # For each one of them, split the number of posts they've written into "fake_members_per_member" and 
    # create "fake_members_per_member" fake users
    # We now have "N * fake_members_per_member" fake users
    
    N = len(test_members)
    fake_members = []
    fake_members_per_member = 2

    for member in test_members:
        posts = psql_interface.get_posts_from(member)
        post_portion = len(posts) // fake_members_per_member

        for i in range(fake_members_per_member):
            fake_member = Member(IdMember = member.IdMember * 100000 + i + 1, Database=member.Database)
            fake_member.Manual_Posts += posts[i * post_portion : (i+1) * post_portion]
            fake_members.append(fake_member)

    # Group them into m groups, each of random size between 2 and 8 inclusive
    # The algorithm succeeds if it finds that each cluster has size(cluster) / 2 subclusters
    # , because each account was split into 2 fake accounts
   
    clusters = []
    index = 0

    while index < len(fake_members):
        curr_cluster_size = choice([4]) # always set this to be even
        clusters.append(fake_members[index : index + curr_cluster_size])
        index += curr_cluster_size

    # define system arguments
    feat_type = "function_words_bow"
    use_presence = False
    n = 5
    posts_args = (feat_type, use_presence, n)

    # solve authorship attribution problem
    results = get_suspects(method = "cop_k_means", 
                            clusters = clusters, 
                            psql_interface = psql_interface, 
                            posts_args = posts_args, 
                            reduce_dim = True,
                            plot = False,
                            dim_reduction = "tsne",
                            n_components = 2, # setting this to a different value while still plotting will lead
                                              # to an error
                            testing = "True") # always set "testing" to True in this case

    # for each of the groups created above, the real number of members should be 
    # len(group) / fake_members_per_member
    total = len(results)
    correct_guesses = 0
    for i in results:
        group_size, group_labels = results[i]
        if group_size == len(clusters[i]) / fake_members_per_member:
            correct_guesses += 1

    # TODO also check that they are correct because of the correct reason
    logging.info("Out of %s tests, %s have succesfully passed, giving the accuracy of " % (str(total), str(correct_guesses)) + "{:.2%}".format(correct_guesses / total))

    mean_accuracy = 0
    mean_precision = 0
    mean_recall = 0
    mean_f1_measure = 0

    member_index = 0
    for test_index, cluster in enumerate(clusters):
        group_size, group_labels = results[test_index]

        # in the case of K-means can't calculate precision, recall, f1-measure
        if group_labels == None:
            break
        tp = 0
        tn = 0
        fp = 0
        fn = 0

        for i in range(len(group_labels) - 1):
            for j in range(i + 1, len(group_labels)):
                member_A = list(group_labels.keys())[i]
                member_B = list(group_labels.keys())[j]

                # actual class is yes
                if member_A.IdMember // 100000 == member_B.IdMember // 100000:
                    # predicted class is yes
                    if group_labels[member_A] == group_labels[member_B]:
                        tp += 1
                    # predicted class is no
                    else:
                        fn += 1
                # actual class is no
                else:
                    # predicted class is yes
                    if group_labels[member_A] == group_labels[member_B]:
                        fp += 1
                    # predicted class is no
                    else:
                        tn += 1

        # TODO calculate accuracy, precision, recall, f1_measure
        try:
            accuracy = (tp + tn) / (tp + fp + fn + tn)
        except:
            accuracy = 0
        
        try:
            precision = tp / (tp + fp)
        except:
            precision = 0

        try:
            recall = tp / (tp + fn)
        except:
            recall = 0
        
        try:
            f1_measure = 2 * (precision * recall) / (recall + precision)
        except:
            f1_measure = 0

        print(str(accuracy) + " " + str(precision) + " " + str(recall) + " " + str(f1_measure))

        mean_accuracy += accuracy
        mean_precision += precision
        mean_recall += recall
        mean_f1_measure += f1_measure

    mean_accuracy /= len(clusters)
    mean_precision /= len(clusters)
    mean_recall /= len(clusters)
    mean_f1_measure /= len(clusters)

    print(str(mean_accuracy) + " " + str(mean_precision) + " " + str(mean_recall) + " " + str(mean_f1_measure))

        

    
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
            fake_member = Member(IdMember = member.IdMember * 1000 + i + 1, Database=member.Database)
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
        group_size = results[i]
        if group_size == len(clusters[i]) / fake_members_per_member:
            correct_guesses += 1

    # TODO also check that they are correct because of the correct reason
    logging.info("Out of %s tests, %s have succesfully passed, giving the accuracy of " % (str(total), str(correct_guesses)) + "{:.2%}".format(correct_guesses / total))

    

    
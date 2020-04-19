from Post import Post
from Member import Member
from suspect_detection import get_suspects
from Postgres_interface import Postgres_interface
from random import choice
import os
import logging

def get_test_members():
    test_members = []
    # curr_member = Member(IdMember = 7, Database = "crimebb-crackedto-2020-01-02")
    # test_members.append(curr_member)
    # curr_member = Member(IdMember = 14883, Database = "crimebb-crackedto-2020-01-02")
    # test_members.append(curr_member)
    # curr_member = Member(IdMember = 94080, Database = "crimebb-crackedto-2020-01-02")
    # test_members.append(curr_member)
    # curr_member = Member(IdMember = 23364, Database = "crimebb-crackedto-2020-01-02")
    # test_members.append(curr_member)
    # curr_member = Member(IdMember = 9218, Database = "crimebb-crackedto-2020-01-02")
    # test_members.append(curr_member)
    # curr_member = Member(IdMember = 35234, Database = "crimebb-crackedto-2020-01-02")
    # test_members.append(curr_member)
    # curr_member = Member(IdMember = 37004, Database = "crimebb-crackedto-2020-01-02")
    # test_members.append(curr_member)
    # curr_member = Member(IdMember = 4143, Database = "crimebb-crackedto-2020-01-02")
    # test_members.append(curr_member)
    # curr_member = Member(IdMember = 982451, Database = "crimebb-nulled-2020-01-02")
    # test_members.append(curr_member)
    # # first and last are the same real person, so the real number of clusters ***should be*** total-1

    test_members_file = os.path.join("..", *["out", "best_members.txt"])
    f = open(test_members_file, "r", encoding="utf-8")
    for line in f:
        line = line.split()
        IdMember = int(line[0])
        Database = line[1]

        curr_member = Member(IdMember = IdMember, Database = Database)
        test_members.append(curr_member)

    return test_members


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

    # create a list of 1000 users with a lot of posts
    # For each one of them, split the number of posts they've written into 2 and 
    # create 2 fake users
    # We now have 2000 fake users
    
    fake_members = []
    fake_members_per_member = 2

    for member in test_members:
        posts = psql_interface.get_posts_from(member)
        post_portion = len(posts) // fake_members_per_member

        for i in range(fake_members_per_member):
            fake_member = Member(IdMember = member.IdMember * 1000 + i + 1, Database=member.Database)
            fake_member.Manual_Posts += posts[i * post_portion : (i+1) * post_portion]
            fake_members.append(fake_member)

    # Group them into n groups, each of random size between 2 and 8 inclusive
    # The algorithm succeeds if it finds that each cluster has size(cluster) / 2 subclusters
    # , because each account was split into 2 fake accounts
   
    clusters = []
    index = 0

    while index < len(fake_members):
        curr_cluster_size = choice([6])
        clusters.append(fake_members[index : index + curr_cluster_size])
        index += curr_cluster_size

    feat_type = "function_words_bow"
    use_presence = False
    n = 5
    posts_args = (feat_type, use_presence, n)

    results = get_suspects(method = "intuitive", 
                               clusters = clusters, 
                               psql_interface = psql_interface, 
                               posts_args = posts_args, 
                               reduce_dim = True,
                               plot = False,
                               dim_reduction = "tsne",
                               n_components = 2,
                               testing = "True") # always set "testing" to True in this case

    total = len(results)
    correct_guesses = 0
    for i in results:
        group_size = results[i]
        if group_size == len(clusters[i]) / fake_members_per_member:
            correct_guesses += 1

    # TODO also check that they are correct because of the correct reason
    logging.info("Out of %s tests, %s have succesfully passed, giving the accuracy of " % (str(total), str(correct_guesses)) + "{:.2%}".format(correct_guesses / total))

    

    
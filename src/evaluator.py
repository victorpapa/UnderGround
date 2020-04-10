from Post import Post
from Member import Member
from suspect_detection import get_suspects
from Postgres_interface import Postgres_interface
import os
import logging

def get_test_members():
    test_members = []
    curr_member = Member(IdMember = 7, Database = "crimebb-crackedto-2020-01-02")
    test_members.append(curr_member)
    curr_member = Member(IdMember = 14883, Database = "crimebb-crackedto-2020-01-02")
    test_members.append(curr_member)
    curr_member = Member(IdMember = 94080, Database = "crimebb-crackedto-2020-01-02")
    test_members.append(curr_member)
    curr_member = Member(IdMember = 23364, Database = "crimebb-crackedto-2020-01-02")
    test_members.append(curr_member)
    curr_member = Member(IdMember = 9218, Database = "crimebb-crackedto-2020-01-02")
    test_members.append(curr_member)
    curr_member = Member(IdMember = 35234, Database = "crimebb-crackedto-2020-01-02")
    test_members.append(curr_member)
    curr_member = Member(IdMember = 37004, Database = "crimebb-crackedto-2020-01-02")
    test_members.append(curr_member)
    curr_member = Member(IdMember = 4143, Database = "crimebb-crackedto-2020-01-02")
    test_members.append(curr_member)
    curr_member = Member(IdMember = 982451, Database = "crimebb-nulled-2020-01-02")
    test_members.append(curr_member)

    # first and last are the same real person, so the real number of clusters ***should be*** total-1

    return test_members

# initialising the logging file and setting the correct working directory
def init_env():
    os.chdir("D:\\Program Files (x86)\\Courses II\\Dissertation\\res")
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

    features = {}
    feat_type = "n_grams"
    use_presence = False
    n = 5
    posts_args = (feat_type, use_presence, n)

    my_posts = []
    for test_member in test_members:
        my_posts += psql_interface.get_posts_from(test_member)

    clusters = [test_members] # one cluster containing all the users

    get_suspects(method = "k_means", 
                 clusters = clusters, 
                 psql_interface = psql_interface, 
                 posts_args = posts_args, 
                 reduce_dim = True,
                 dim_reduction = "pca",
                 n_components = 2)

    

    
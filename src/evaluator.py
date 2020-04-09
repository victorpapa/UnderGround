from Post import Post
from Member import Member
from Main import get_suspects_intutitively, get_suspects_k_means, get_suspects_constrained_k_means
from Postgres_interface import Postgres_interface

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
    curr_member = Member(IdMember = 982451, Database = "crimebb-nulled-2020-01-02")
    test_members.append(curr_member)

    # 0 and 5 are the same real person, so the real number of clusters ***should be*** 5, not 6

    return test_members

if __name__ == "__main__":
    
    test_members = get_test_members()
    psql_interface = Postgres_interface()
    psql_interface.start_server()

    features = {}
    feat_type = "n_grams"
    use_presence = False
    n = 3
    posts_args = (feat_type, use_presence, n)

    my_posts = []
    for test_member in test_members:
        my_posts += psql_interface.get_posts_from(test_member)

    clusters = [test_members] # one cluster containing all the users
    get_suspects_k_means(clusters, psql_interface = psql_interface, posts_args = posts_args)

    

    
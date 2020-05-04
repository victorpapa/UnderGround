from Post import Post
from Member import Member
from suspect_detection import get_suspects
from Postgres_interface import Postgres_interface
from random import choice, sample, randint
import os
import logging
import operator as op
from functools import reduce

# from https://stackoverflow.com/questions/4941753/is-there-a-math-ncr-function-in-python
def ncr(n, r):
    r = min(r, n-r)
    numer = reduce(op.mul, range(n, n-r, -1), 1)
    denom = reduce(op.mul, range(1, r+1), 1)
    return numer / denom

def sign_test(p, n, t, alpha):
    s = 0

    p += t//2
    n += t//2

    total = p + n

    k = min(p, n)

    for i in range(k):
        s += ncr(total, i) * pow(0.5, i) * pow(0.5, total - i)
    
    s *= 2

    logging.info("The sign test value is equal to " + str(s))

    if s <= alpha:
        return True # have obtained statistical significance with alpha

    return False # null hypothesis holds at alpha, so no statistical significance

def copy_list(my_list):
        new_list = []

        for i in my_list:
            new_list += [i]

        return new_list

def get_mean(my_list):
    my_sum = 0

    for i in my_list:
        my_sum += i

    return my_sum / len(my_list)

def perm_test(predictions_a, predictions_b, R):
        n = len(predictions_a)

        assert(n == len(predictions_b))

        copy_a = copy_list(predictions_a)
        copy_b = copy_list(predictions_b)

        init_mean_a = get_mean(predictions_a)
        init_mean_b = get_mean(predictions_b)

        init_diff = init_mean_a - init_mean_b

        s = 0

        for i in range(R):

            indexes = [randint(0, 1) for i in range(n)]
            for j in range(len(indexes)):
                if indexes[j] == 1 and predictions_a[j] != predictions_b[j]:
                    aux = predictions_a[j]
                    predictions_a[j] = predictions_b[j]
                    predictions_b[j] = aux

            curr_mean_a = get_mean(predictions_a)
            curr_mean_b = get_mean(predictions_b)

            # print(str(init_mean_a) + " " + str(curr_mean_a))

            curr_diff = curr_mean_a - curr_mean_b

            if curr_diff >= init_diff:
                s += 1

            predictions_a = copy_list(copy_a)
            predictions_b = copy_list(copy_b)

        return (s+1) / (R+1)

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

    # get X random members
    return sample(test_members, 1000)

def measure_performance(results, clusters):

    # for each of the groups created above, the real number of members should be 
    # len(group) / fake_members_per_member
    total = len(results)
    correct_guesses = 0
    for i in results:
        group_size, group_labels = results[i]
        if group_size == len(clusters[i]) / fake_members_per_member:
            correct_guesses += 1


    logging.info("Out of %s tests, %s have succesfully passed, giving the accuracy of " % (str(total), str(correct_guesses)) + "{:.2%}".format(correct_guesses / total))

    mean_accuracy = 0
    mean_precision = 0
    mean_recall = 0
    mean_f1_measure = 0

    member_index = 0

    p = 0
    n = 0
    t = 0
    total_cases = 0
    
    to_return = []

    for test_index, cluster in enumerate(clusters):
        group_size, group_labels = results[test_index]

        # in the case of K-means can't calculate accuracy, precision, recall, f1-measure
        if group_labels == None:
            to_return.append(None)
            continue 

        total_cases += 1
        
        tp = 0
        tn = 0
        fp = 0
        fn = 0

        for i in range(len(group_labels) - 1):
            for j in range(i + 1, len(group_labels)):

                # ------------------ first system ------------------ #
                member_A = list(group_labels.keys())[i]
                member_B = list(group_labels.keys())[j]

                # actual class is yes
                if member_A.IdMember // 100000 == member_B.IdMember // 100000:
                    # predicted class is yes
                    if group_labels[member_A] == group_labels[member_B]:
                        tp += 1
                        to_return.append(1)
                        correct = True
                    # predicted class is no
                    else:
                        fn += 1
                        to_return.append(0)
                        correct = False
                # actual class is no
                else:
                    # predicted class is yes
                    if group_labels[member_A] == group_labels[member_B]:
                        fp += 1
                        to_return.append(0)
                        correct = False
                    # predicted class is no
                    else:
                        tn += 1
                        to_return.append(1)
                        correct = True

        # calculate accuracy, precision, recall, f1_measure
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

        mean_accuracy += accuracy
        mean_precision += precision
        mean_recall += recall
        mean_f1_measure += f1_measure

    mean_accuracy /= total_cases
    mean_precision /= total_cases
    mean_recall /= total_cases
    mean_f1_measure /= total_cases

    logging.info("Performance: " + str(mean_accuracy) + " " + str(mean_precision) + " " + str(mean_recall) + " " + str(mean_f1_measure))

    return to_return

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
        curr_cluster_size = choice([2 * fake_members_per_member]) # always set this to be a multiple of fake_members_per_member
        clusters.append(fake_members[index : index + curr_cluster_size])
        index += curr_cluster_size

    # define system arguments "bow", "n_grams", 
    feat_type = ["bow", "n_grams", "function_words_bow"]
    use_presence = False
    n = 5
    posts_args = (feat_type, use_presence, n)

    # solve authorship attribution problem
    results = get_suspects(method = "intuitive", 
                            clusters = clusters, 
                            psql_interface = psql_interface, 
                            posts_args = posts_args, 
                            reduce_dim = True,
                            plot = False,
                            dim_reduction = "tsne",
                            n_components = 2, # setting this to a different value while still plotting will lead
                                              # to an error
                            testing = True) # always set "testing" to True in this case


    system_1 = measure_performance(results, clusters)


    results = get_suspects(method = "cop_k_means", 
                            clusters = clusters, 
                            psql_interface = psql_interface, 
                            posts_args = posts_args, 
                            reduce_dim = True,
                            plot = False,
                            dim_reduction = "tsne",
                            n_components = 2, # setting this to a different value while still plotting will lead
                                              # to an error
                            testing = True) # always set "testing" to True in this case


    system_2 = measure_performance(results, clusters)

    assert(len(system_1) == len(system_2))

    to_del = []
    for i in range(len(system_1)):
        if system_1[i] == None or system_2[i] == None:
            to_del.append(i)

    system_1 = [system_1[i] for i in range(len(system_1)) if i not in to_del]
    system_2 = [system_2[i] for i in range(len(system_2)) if i not in to_del]


    # statistical significance
    # ---------------------- sign test ---------------------- #

    p = 0
    n = 0
    t = 0

    for i in range(len(system_1)):

        if system_1[i] == system_2[i]:
            t += 1
        elif system_1[i] == 1 and system_2[i] == 0:
            p += 1
        else:
            n += 1

    alpha = 0.05
    logging.info(str(p) + " " + str(n) + " " + str(t))
    stat_signif = sign_test(p, n, t, alpha = alpha)

    if stat_signif == False:
        logging.info("There is no statistical difference between the two systems at alpha " + str(alpha))
    else:
        logging.info("There is a statistical difference between the two systems at alpha " + str(alpha))

    # ---------------------- perm_test ---------------------- #
        
    p_value = perm_test(system_1, system_2, R = 5000)
    stat_signif = (p_value <= alpha)

    logging.info("The P value is " + str(p_value))

    if stat_signif == False:
        logging.info("There is no statistical difference between the two systems at alpha " + str(alpha))
    else:
        logging.info("There is a statistical difference between the two systems at alpha " + str(alpha))

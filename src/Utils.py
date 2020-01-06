import csv
import nltk
import math

# TODO input: tuple: (days, hours, minutes, seconds)
#      return true if tuple is at least "days" days long
#      return false otherwise
def is_longer_than(self, tuple, days):
    return False

# TODO return the distance between date1 and date2, in a tuple: (days, hours, minutes, seconds)
def get_date_distance(date1, date2):
    return 0

# returns the Levenshtein distance between username1 and username2
def get_edit_distance(username1, username2):

    edit_cost = 1
    indel_cost = edit_cost / 2

    l1 = len(username1)
    l2 = len(username2)

    dp = [[0 for j in range(l2 + 1)] for i in range(l1 + 1)]

    for i in range(l1 + 1):
        dp[i][0] = i * indel_cost

    for j in range(l2 + 1):
        dp[0][j] = j * indel_cost
        
    for i in range(1, l1+1):
        for j in range(1, l2+1):
            
            if username1[i-1] == username2[j-1]:
                val = dp[i-1][j-1]
            else:
                val = dp[i-1][j-1] + edit_cost # replacement
                
            val = min(val, dp[i][j-1] + indel_cost) # deletion
            val = min(val, dp[i-1][j] + indel_cost) # insertion

            dp[i][j] = val

    return dp[l1][l2]

def create_edge_table_csv(csv_file, to_write):
    csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow(["Source", "Target", "Weight"])
    for w in to_write:
        csv_writer.writerow([w[0], w[1], w[2]])

# input: post as a String
# returns the list of words that make up the post
def get_list_from_string(post):
    ret = []

    for w in post.split():
        ret += [w]

    return ret

# input: post as a list of tokens
# stems every word in post and returns a list containing all stemmed words
def stem_post(post):
    porter_stemmer = nltk.stem.PorterStemmer()
    ret = []

    for w in post:
        w = porter_stemmer.stem(w)
        ret += [w]
    
    return ret

# input: list of tokens
# output: dictionary containing all n-grams and the occurences
def get_n_grams(post, n):
    ret = {}

    index = 0
    n_gram = ()
    for w in post:
        index += 1
        w = w.strip()
        n_gram = n_gram + (w,)
        
        if index == n:
            index -= 1

            if n_gram in ret:
                ret[n_gram] = ret[n_gram] + 1
            else:
                ret[n_gram] = 1

            n_gram = n_gram[1:]

    return ret

# input: post as a list of tokens
# returns a dictionary mapping each word to the number of occurences
def get_bow(post):
    ret = {}

    for w in post:
        if w in ret:
            ret[w] = ret[w] + 1
        else:
            ret[w] = 1

    return ret

# converts a frequency feature vector to a presence feature vector
def freq_to_pres(features):
    ret = {}

    for f in features:
        ret[f] = 1

    return ret

# returns the distance between 2 n-dimensional vectors
def get_dist(vec1, vec2):
    ret = 0

    assert(len(vec1) == len(vec2))

    for i in range(len(vec1)):
        d = vec2[i] - vec1[i]
        ret += d * d

    return math.sqrt(ret)

# input: a target vector, and a list of centres
# output: index of the knn of target
def get_knn(target, centres):
    min_dist = -1
    
    for i in range(len(centres)):
        c = centres[i]
        dist = get_dist(target, c)
        if min_dist == -1 or dist < min_dist:
            min_dist = dist
            ret = i

    return ret

# appends missing elements from to_concat to total
def concat_feature_dicts(total, to_concat):
    for f in to_concat:
        if f in total:
            total[f] += to_concat[f]
        else:
            total[f] = to_concat[f]

# to_be_filled will contain all the keys from total that it doesn't contain, all initialised to 0
def fill_feature_dict(to_be_filled, total):
    for f in total:
        if f not in to_be_filled:
            to_be_filled[f] = 0

# returns the keys of a dictionary as a lsit
def get_dict_keys(dict):
    ret = []

    for f in dict:
        ret += [f]

    return ret

# returns the values of a dictionary as a lsit
def get_dict_values(dict):
    ret = []

    for f in dict:
        ret += dict[f]

    return ret

# normalises the feature vector
def normalise_feature_vector(features):
    total = 0

    for x in features:
        total += x

    for i in range(len(features)):
        features[i] = features[i] / total

# returns a dict that only contains the entries in to_be_shrunk whose keys are present in master
def shrink_dict(to_be_shrunk, master):

    ret = {}

    for k in to_be_shrunk:
        if k in master:
            ret[k] = to_be_shrunk[k]

    return ret

# converts a list of 3-tuples to a dictionary
def tuples_to_dict(tuples):
    ret = {}

    for t in tuples:
        if t[0] not in ret:
            ret[t[0]] = [(t[1], t[2])]
        else:
            ret[t[0]] += [(t[1], t[2])]

    return ret

if __name__ == "__main__":

    # print(get_list_from_string("a b c d e f"))
    # print(get_n_grams(get_list_from_string("a b c d a b"), 2))
    # print(get_bow(get_list_from_string("a a c c e f")))

    init_features = {"a":1, "b":2}
    all_features = {"c":5}

    fill_feature_dict(init_features, all_features)
    print(all_features)
    print(init_features)

    print(shrink_dict(init_features, all_features))
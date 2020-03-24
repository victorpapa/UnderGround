import csv
import nltk
import math
import re

# returns true if date_n_time1 is later or equal to date_n_time2
def is_later_than(date_n_time1, date_n_time2):
    assert(len(date_n_time1) == 6 and len(date_n_time2) == 6)

    for i in range(len(date_n_time1)):
        if date_n_time1[i] < date_n_time2[i]:
            return False
        
        if date_n_time1[i] > date_n_time2[i]:
            return True

    return True


# input: tuple: (years, months, days, hours, minutes, seconds)
# return true if tuple is at least (including) "days" days long
# return false otherwise
def is_longer_than(time, days):
    d = time[0] * 365 + time[1] * 30 + time[2]
    h = time[3]
    m = time[4]
    s = time[5]

    if d > days:
        return True

    if d < days:
        return False

    if h == 0 and m == 0 and s == 0:
        return True

    return True

# returns True if the string s represents an integer number
def is_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

# returns the date present in the string s
def get_date_from(s):

    res = s

    # db_name example: crimeBB_2018-07-03_mpgh
    s = re.split("[_-]", s)
    for i in range(len(s)):
        if is_int(s[i]) and is_int(s[i+1]) and is_int(s[i+2]):
            return (int(s[i]), int(s[i+1]), int(s[i+2]))

    print("Couldn't extract date from " + res + ".")
    exit()

# returns the number of days that should be added to the date (due to time zone)
# and also returns the time present in the string s
def get_00_time_from(s):
    # time example 1: 07:38:00+00:00
    # time example 2: 17:11:55.376518+01:00
    if "+" in s:
        s = s.split("+")
        time_zone = int(s[1].split(":")[0])
    elif "-" in s:
        s = s.split("-")
        time_zone = -int(s[1].split(":")[0])
    else:
        print("Invalid time format: " + s + ".")
        exit()

    (h, m, s) = s[0].split(":")
    h = int(h)
    m = int(m)
    s = int(float(s)) # because of cases such as example 2, where milliseconds are also present

    h -= time_zone

    if h >= 24:
        d = 1
        h -= 24
    elif h < 0:
        d = -1
        h += 24
    else:
        d = 0
    
    return (d, (h, m, s))

# input: date_n_time1: (years, months, days, hours, minutes, seconds)
# input: date_n_time2: (years, months, days, hours, minutes, seconds)
# returns the time diff with the same format as above
def get_time_diff(date_n_time1, date_n_time2):

    if not is_later_than(date_n_time1, date_n_time2):
        return (0, 0, 0, 0, 0, 0)

    s = date_n_time1[5] - date_n_time2[5]
    m = date_n_time1[4] - date_n_time2[4]
    h = date_n_time1[3] - date_n_time2[3]
    d = date_n_time1[2] - date_n_time2[2]
    mo = date_n_time1[1] - date_n_time2[1]
    y = date_n_time1[0] - date_n_time2[0]

    if s < 0:
        s += 60
        m -= 1
    
    if m < 0:
        m += 60
        h -= 1
    
    if h < 0:
        h += 24
        d -= 1
    
    if d < 0:
        d += 30
        mo -= 1

    if mo < 0:
        mo += 12
        y -= 1

    return (y, mo, d, h, m, s)

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


# input: post as a String
# returns the list of words separated by whitespace that make up the post
def get_tokens_from(post):
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

# input: post as a list of tokens
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

    if len(vec1) != len(vec2):
        print("Vector dimensions " + str(len(vec1)) + " " + str(len(vec2)) + " not matching! Exiting ...")
        exit()

    for i in range(len(vec1)):
        d = vec2[i] - vec1[i]
        ret += d * d

    return math.sqrt(ret)

# input: a target vector, and a list of centres
# output: knn of target
def get_knn(target, centres):
    min_dist = -1
    
    for i in range(len(centres)):
        c = centres[i]
        dist = get_dist(target, c)
        if min_dist == -1 or dist < min_dist:
            min_dist = dist
            ret = i

    return centres[ret]

# to_be_filled will contain all the keys from total that it doesn't contain, all initialised to 0
def fill_feature_dict(to_be_filled, total):
    for f in total:
        if f not in to_be_filled:
            to_be_filled[f] = 0

# returns the keys of a dictionary as a lsit
def get_dict_keys(dict):
    return list(dict.keys())

# returns the values of a dictionary as a lsit
def get_dict_values(dict):
    return list(dict.values())

# normalises the feature vector
def normalise_feature_vector(features):
    total = 0

    for x in features:
        total += features[x]

    for i in features:
        features[i] = features[i] / total

# returns a dict that only contains the entries in to_be_shrunk whose keys are present in total
def shrink_dict(to_be_shrunk, total):

    ret = {}

    for k in to_be_shrunk:
        if k in total:
            ret[k] = to_be_shrunk[k]

    return ret

# converts a list of 3-tuples to a dictionary
# is not tested
def tuples_to_dict(tuples):
    ret = {}

    for t in tuples:
        if t[0] not in ret:
            ret[t[0]] = [(t[1], t[2])]
        else:
            ret[t[0]] += [(t[1], t[2])]

    return ret

# edges is an edge table for a weighted graph, e.g. source -> (target, weight)
# performs a dfs and keeps track of visited nodes
def visit(node, edges, visited):

    visited[node] = True

    for (n, _) in edges[node]:
        if not visited[n]:
            visit(n, edges, visited)

# given a dictionary representing an undirected graph, obtain the number of conex components
# edges is an edge table for a weighted graph, e.g. source -> (target, weight)
def get_conex_components_count(edges):

    total = 0
    visited = {}
    for u in edges:
        visited[u] = False

    for u in edges:
        if not visited[u]:
            visit(u, edges, visited)
            total += 1

    return total

# edges is an edge table for a weighted graph, e.g. source -> [(target, weight), (target, weight), ...]
# performs a dfs and returns the current conex component
def get_current_cluster(node, edges, visited, cluster):

    cluster += [node]
    visited[node] = True

    for (n, w) in edges[node]:
        if not visited[n]:
            get_current_cluster(n, edges, visited, cluster)

# given a dictionary representing an undirected graph, obtain the list of conex components
# edges is an edge table for a weighted graph, e.g. source -> [(target, weight), (target, weight), ...]
def get_clusters(edges):

    total = []
    visited = {}
    for u in edges:
        visited[u] = False

    for u in edges:
        if not visited[u]:
            cluster = []
            get_current_cluster(u, edges, visited, cluster)
            total += [cluster]

    return total


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
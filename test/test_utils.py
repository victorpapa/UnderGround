import sys

sys.path.insert(1, "..\\src")

import pytest
import nltk
from Utils import is_longer_than, is_later_than, get_edit_distance, get_date_from, get_tokens_from, stem_post, get_bow, get_n_grams, freq_to_pres, get_knn, shrink_dict, fill_feature_dict, tuples_to_dict, get_dict_keys, normalise_feature_vector, get_dist, get_connected_components_count, visit, get_00_time_from, get_time_diff, get_connected_components, get_strongly_connected_components_count

def test_is_longer_than():
    time = (0, 0, 10, 23, 59, 59)
    days = 11
    assert(is_longer_than(time, days) == False)

    time = (0, 0, 10, 23, 59, 59)
    days = 10
    assert(is_longer_than(time, days) == True)

    time = (0, 0, 10, 0, 0, 0)
    days = 0
    assert(is_longer_than(time, days) == True)

def test_is_later_than():
    t1 = (0, 0, 10, 23, 59, 59)
    t2 = (0, 0, 10, 24, 59, 59)
    assert(is_later_than(t1, t2) == False)

    t1 = (0, 0, 10, 23, 59, 59)
    t2 = (0, 0, 10, 23, 59, 59)
    assert(is_later_than(t1, t2) == True)

    t1 = (0, 0, 10, 23, 1, 59)
    t2 = (0, 0, 10, 23, 0, 59)
    assert(is_later_than(t1, t2) == True)

# was deleted from the repo, no longer useful
# def test_get_date_distance():
#     t1 = (10, 23, 59, 59)
#     t2 = (10, 24, 59, 59)
#     assert(get_date_distance(t1, t2) == (0, 0, 0, 0))

#     t1 = (10, 23, 59, 59)
#     t2 = (10, 23, 59, 59)
#     assert(get_date_distance(t1, t2) == (0, 0, 0, 0))

#     t1 = (15, 24, 1, 58)
#     t2 = (10, 23, 3, 59)
#     assert(get_date_distance(t1, t2) == (5, 0, 57, 59))

def test_get_date_from():
    assert(get_date_from("crimeBB_2018-07-03_mpgh") == (2018, 7, 3))
    assert(get_date_from("crimebb-crackedto-2020-01-02") == (2020, 1, 2))

def test_get_00_time_from():
    assert(get_00_time_from("07:38:00+00") == (0, (7, 38, 0)))
    assert(get_00_time_from("17:11:55.376518+01") == (0, (16, 11, 55)))
    assert(get_00_time_from("01:11:55.376518+03") == (-1, (22, 11, 55)))
    
def test_get_edit_distance():
    u1 = "victor"
    u2 = "victor98"
    assert(get_edit_distance(u1, u2) == 1)

    u1 = "victor"
    u2 = "victoe98"
    assert(get_edit_distance(u1, u2) == 2)

    u1 = "abc"
    u2 = "abc"
    assert(get_edit_distance(u1, u2) == 0)

def test_get_list_from_string():
    s = "abc de f"
    l = get_tokens_from(s)
    assert(l == ["abc", "de", "f"])

def test_stem_post():
    porter_stemmer = nltk.stem.PorterStemmer()
    post = "The tanggu (堂鼓; pinyin: tánggǔ, pronounced [tʰɑ̌ŋkù]; literally ceremonial hall drum; sometimes spelled tang gu) is a traditional Chinese drum from the 19th century. It is medium in size and barrel-shaped, with two heads made of animal skin, and is played with two sticks."

    stemmed_post = stem_post(post)

    for w in stemmed_post:
        assert (w == porter_stemmer.stem(w))

def test_get_dict_keys():
    my_dict = {"abc":1, "def":2}
    keys = get_dict_keys(my_dict)
    assert(keys == ["abc", "def"])

def test_get_n_grams():
    post = "1 2 3 4 5 6 7 8 9 10"
    post = get_tokens_from(post)
    n_grams = get_n_grams(post, 3)
    n_grams = get_dict_keys(n_grams)
    assert(len(n_grams) == 8)

    for i in range(1, 9):
        assert(n_grams[i-1] == (str(i), str(i+1), str(i+2)))

def test_get_bow():
    post = "a a b c b"
    post = get_tokens_from(post)
    bow = get_bow(post)
    assert(bow == {"a": 2, "b" : 2, "c" : 1})

def test_freq_to_pres():
    features = {"a": 2, "b" : 2, "c" : 1}
    features = freq_to_pres(features)
    for f in features:
        assert(features[f] == 1)

def test_get_dist():
    vec1 = [1]
    vec2 = [1]
    d = get_dist(vec1, vec2)
    assert(d == 0)

    vec1 = [1, 2, 3, 4]
    vec2 = [2, 3, 4, 5]
    d = get_dist(vec1, vec2)
    assert(d == 2)

def test_get_knn():
    centres = [[1, 2, 3], [5, 6, 7], [11, 12, 13]]
    target = [2, 6, 7]
    knn = get_knn(target, centres)
    assert(knn == centres[1])

def test_fill_feature_dict():
    to_be_filled = {"a": 2, "b" : 2, "c" : 1}
    total = {"a": 2, "b" : 2, "c" : 1, "d": 2}
    fill_feature_dict(to_be_filled, total)
    assert(to_be_filled == {"a": 2, "b" : 2, "c" : 1, "d": 0})

def test_normalise_feature_vector():
    features = {"a": 2, "b" : 2, "c" : 1}
    normalise_feature_vector(features)
    s = 0
    for i in features:
        s += features[i]

    assert(s == 1)

def test_shrink_dict():
    to_be_shrunk = {"a": 2, "b" : 2, "c" : 1, "d": 1}
    total = {"a": 2, "b" : 2, "c" : 1}
    to_be_shrunk = shrink_dict(to_be_shrunk, total)
    assert(to_be_shrunk == total)

def test_visit():
    node = 1
    edges = {1:{(2, 1), (3, 2), (4, 1)}, 2:{(1, 1), (3, 1)}, 3:{(1, 2), (2, 1)}, 4:{(1, 1), (5, 1)}, 5:{(4, 1)}}
    visited = {}
    for n in edges:
        visited[n] = False
    visit(node, edges, visited)
    for i in edges:
        assert(visited[i] == True)

def test_get_connected_components_count():
    edges = {1:{(2, 1), (3, 2), (4, 1)}, 2:{(1, 1), (3, 1)}, 3:{(1, 2), (2, 1)}, 4:{(1, 1)}, 5:{(6, 1)}, 6:{(5, 1)}}
    cc = get_connected_components_count(edges)
    assert(cc == 2)

def test_get_time_diff():
    date_n_time1 = (1,2,3,4,5,6)
    date_n_time2 = (1,2,3,4,5,7)
    assert(get_time_diff(date_n_time1, date_n_time2) == (0,0,0,0,0,0))


    date_n_time1 = (1,2,3,4,5,6)
    date_n_time2 = (1,2,3,3,3,8)
    assert(get_time_diff(date_n_time1, date_n_time2) == (0,0,0,1,1,58))

def test_get_connected_components():
    edges = {
        1 : [(2, 0), (3, 0)],
        2 : [(1, 0)],
        3 : [(1, 0), (6, 0)],
        4 : [(5, 0)],
        5 : [(4, 0)],
        6 : [(3, 0)]
    }

    assert(get_connected_components(edges) == [[1,2,3,6], [4,5]])

    edges = {
        1 : [(2, 0), (3, 0)],
        2 : [(1, 0)],
        3 : [(1, 0), (6, 0)],
        4 : [],
        5 : [],
        6 : [(3, 0)]
    }

    assert(get_connected_components(edges) == [[1,2,3,6], [4], [5]])

def test_get_strongly_connected_components_count():
    edges = {
        0 : [2, 3],
        1 : [0],
        2 : [1],
        3 : [4],
        4 : [],
    }

    assert(get_strongly_connected_components_count(edges) == 3)
import csv
import nltk

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

# input: list of tokens
# stems every word in post and returns a list containing all stemmed words
def stem_post(post):
    porter_stemmer = nltk.stem.PorterStemmer()
    ret = []

    for w in post:
        w = porter_stemmer.stem(w)
        ret += [w]
    
    return ret

# input: list of tokens
# output: list containing all n-grams
def get_n_grams(post, n):
    ret = []

    index = 0
    n_gram = ()
    for w in post:
        index += 1
        w = w.strip()
        n_gram = n_gram + (w,)
        
        if index == n:
            index -= 1
            ret += [n_gram]
            n_gram = n_gram[1:]

    return ret

if __name__ == "__main__":

    print(get_list_from_string("a b c d e f"))
    print(get_n_grams(get_list_from_string("a b c d e f"), 2))
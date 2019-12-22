from QueryData import Data_fetcher
from Post import Post
from Member import Member
from Utils import get_edit_distance
import os

def get_similar_usernames(active_users):

    similar_usernames = []

    for i in range(len(active_users) - 1):
        for j in range(i+1, len(active_users)):
            u1 = active_users[i].Username
            u2 = active_users[j].Username
            dist = get_edit_distance(u1, u2)

            if dist <= 2:
                similar_usernames += (u1, u2, dist)

    return similar_usernames

if __name__ == "__main__":
    names_path = os.path.join(os.getcwd(), "..\\res\\First_Names.txt")
    f = open(names_path, "r", encoding="utf8")
    df = Data_fetcher()
    ID = 0

    for l in f:
        l = l.split()
        
        for w in l:
            m = Member(Username=w, IdMember=ID)
            ID += 1
            df.add_member(m)

    active_users = df.get_active_users()

    similar_usernames = get_similar_usernames(active_users)

    for w in similar_usernames:
        print(w)


class Post:

    def __init__(self, IdPost = 0, Author = 0, Thread = 0, TimeStamp = "", Content = "", 
                AuthorNumPosts = 0, AuthorReputation = 0, LastParse = "", parsed = False, 
                Site = 0, CitedPost = [], AuthorName = '', Likes = 0):
        
        self.IdPost = IdPost # integer
        self.Author = Author # integer
        self.Thread = Thread # integer
        self.TimeStamp = TimeStamp # timestamp with time zone
        self.Content = Content # string
        self.AuthorNumPosts = AuthorNumPosts # integer
        self.AuthorReputation = AuthorReputation # integer
        self.LastParse = LastParse # timestamp with time zone
        self.parsed = parsed # boolean
        self.Site = Site # integer
        self.CitedPost = CitedPost # bigint[] 
        self.AuthorName = AuthorName # character varying
        self.Likes = Likes # integer

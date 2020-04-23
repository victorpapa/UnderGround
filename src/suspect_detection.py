import os
import logging
from Utils import timestamped, get_bow, get_n_grams, get_function_words_bow, freq_to_pres, fill_feature_dict, normalise_feature_vector, get_dist, get_dict_keys, get_dict_values, get_strongly_connected_components_count
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, silhouette_samples
from copkmeans.cop_kmeans import cop_kmeans
from matplotlib import pyplot as plt
import matplotlib.cm as cm
import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from nltk.stem import PorterStemmer


# returns the dictionary of features for the given post
def get_features_dict_for_post(post, feature, presence, n = 1):

    ret = {}

    text = post.Content

    # have to provide a list of tokens to the get_bow and get_n_grams methods
    text = text.split()

    # stemming words
    # TODO see if it works
    ps = PorterStemmer()
    for i in range(len(text)):
        text[i] = ps.stem(text[i])
    del ps

    if feature == "bow":
        feat_dict = get_bow(text)
    elif feature == "n_grams":
        if n == 1: 
            logging.warning(timestamped("Did you forget to set n when querying n_grams?"))
        feat_dict = get_n_grams(text, n)
    elif feature == "function_words_bow":
        feat_dict = get_function_words_bow(text)
    else:
        logging.critical(timestamped("Feature type " + feature + " not implemented."))

    
    ret.update(feat_dict)

    if presence == True:
        ret = freq_to_pres(ret)

    return ret

# df is a reference to a Data object
# feature is a String, which is the type of feature we want to analyse (BoW, N-grams etc.)
# n is for n-grams
# presence is for whether we want feeature presence or not
def get_features_dict_written_by(member, psql_interface, feature, presence, n, testing):

    ret_aggregate = {}
    ret_per_post = {}

    # TODO keep getting memory errors if number of posts is not limited
    if testing == False:
        posts = psql_interface.get_posts_from(member)[:100]
    else:
        posts = member.Manual_Posts[:100]

    for post in posts:

        curr_post_feat_dict = get_features_dict_for_post(post = post, feature = feature, presence = presence, n = n)

        for f in curr_post_feat_dict:
            if f in ret_aggregate:
                ret_aggregate[f] += curr_post_feat_dict[f]
            else:
                ret_aggregate[f] = curr_post_feat_dict[f]

        ret_per_post[post] = curr_post_feat_dict

    if presence == True:
        ret_aggregate = freq_to_pres(ret_aggregate)

        for post in ret_per_post:
            ret_per_post[post] = freq_to_pres(ret_per_post[post])
    else:
        for i in ret_aggregate:
            ret_aggregate[i] /= len(posts)

    return ret_aggregate, ret_per_post

def get_member_dicts_from_cluster(cluster, psql_interface, posts_args, testing):

    feat_type = posts_args[0]
    use_presence = posts_args[1]
    n = posts_args[2]

    # Obtain the vector for each member

    logging.debug(timestamped("The members are:"))
    for u in cluster:
        logging.debug(timestamped(str(u.IdMember) + " " + str(u.Database)))

    member_aggr_dicts = {}
    member_per_post_dicts = {}

    for i in range(len(cluster)):
        member = cluster[i]
        member_aggr_feat_dict, member_per_post_feat_dict = get_features_dict_written_by(member = member, 
                                                                                    psql_interface = psql_interface, 
                                                                                    feature = feat_type, 
                                                                                    presence = use_presence,
                                                                                    n = n, 
                                                                                    testing = testing)
        if len(member_aggr_feat_dict) == 0:
            continue
            
        member_aggr_dicts[member] = member_aggr_feat_dict
        member_per_post_dicts[member] = member_per_post_feat_dict

    # Aggregate all the keys to get the dimensions
    aggregated_keys = set()

    for member in member_aggr_dicts:
        vector = member_aggr_dicts[member]
        
        for k in vector:
            aggregated_keys.add(k)

    # Fill all the vectors to contain all the dimensions
    for member in member_aggr_dicts:
        # And also normalise them if presence isn't used, distribution is more important
        if not use_presence:
            normalise_feature_vector(member_aggr_dicts[member])

        fill_feature_dict(member_aggr_dicts[member], aggregated_keys)
        curr_member_posts_dicts = member_per_post_dicts[member]

        for p in curr_member_posts_dicts:
            if not use_presence:
                normalise_feature_vector(curr_member_posts_dicts[p])

            # check that this changes, and then leave a comment stating the result
            # it works fine
            fill_feature_dict(curr_member_posts_dicts[p], aggregated_keys)

    return member_aggr_dicts, member_per_post_dicts        


# only correctly identifies (really) tight clusters
# works 50% of the time (by chance) with groups of 2 users
def get_suspects_intuitively(member_aggr_dicts, member_per_post_dicts):

    suspects = {}

    # iterate through members, and assign each of their posts to one of the other members
    # the most chosen member will be suspected to be the same member as the one we are analysing

    for source_member in member_per_post_dicts:
        # curr_member_posts_dicts is a dictionary that maps a member to a dictionary, which maps each post
        # written by source_member to its feature vector
        curr_member_posts_dicts = member_per_post_dicts[source_member]
        labels = {}

        for p in curr_member_posts_dicts:
            # curr_post_dict is a dictionary, which maps each post
            # written by the source_member to its feature vector
            
            curr_post_dict = curr_member_posts_dicts[p]

            min_dist = -1
            for target_member in member_aggr_dicts:
                if target_member == source_member:
                    # we want a different member
                    continue
                
                # we only need the values of the dicts, and we want the features in the same order
                v1 = []
                v2 = []
                for k in curr_post_dict:
                    v1 += [curr_post_dict[k]]
                    v2 += [member_aggr_dicts[target_member][k]]

                dist = get_dist(v1, v2)

                if min_dist == -1 or dist < min_dist:
                    min_dist = dist
                    member_label = target_member

            if member_label in labels:
                labels[member_label] += 1
            else:
                labels[member_label] = 1
    
        maximum = -1
        
        for member_label in labels:
            if maximum == -1 or labels[member_label] > maximum:
                maximum = labels[member_label]
                closest_member = member_label

        suspects.update({source_member:[closest_member]})

    # suspects is a dict, mapping Member objects to lists of Member objects, each list having 1 item
    for suspect in suspects:
        logging.info(timestamped(str(suspect.IdMember) + " " + suspect.Database + " -----> " + str(suspects[suspect][0].IdMember) + " " + suspects[suspect][0].Database))
    
    # Here we want STRONGLY CONNECTED COMPONENTS
    
    #  o
    #  ▲ 
    #  | 
    #  ▼                        o
    #  o < - - - - - - - - - - /

    # In this case, I want the program to output 2 components, rather than 1
    cc = get_strongly_connected_components_count(suspects)
    logging.info(timestamped("This cluster thus forms " + str(cc) + " strongly connected subclusters of suspects.\n"))

    return cc

def plot_results(wcss, sil_avgs):

    suspect_count = len(wcss)

    # instead of just plotting a graph and finding K manually,
    # use the Silhouette method as well
    fig, axs = plt.subplots(1, 2)
    axs[0].plot(range(1, suspect_count + 1), wcss)
    axs[0].set_title('Elbow Method')
    axs[0].set(xlabel='Number of clusters', ylabel='WCSS')

    if suspect_count > 2:
        axs[1].plot(range(2, suspect_count + 1), sil_avgs)
        axs[1].set_title('Silhouette Method')
        axs[1].set(xlabel='Number of clusters', ylabel='S_SCORE')

    plt.show()

def populate_must_link(must_link, member_per_post_dicts):
    idx = 0
    for member in member_per_post_dicts:
        post_count = len(member_per_post_dicts[member])
        for i in range(idx+1, idx + post_count):
            must_link += [(idx, i)]
        idx += post_count

# part of the code from
# https://scikit-learn.org/stable/auto_examples/cluster/plot_kmeans_silhouette_analysis.html#sphx-glr-auto-examples-cluster-plot-kmeans-silhouette-analysis-py
def plot_silhouettes_and_posts(n_clusters, feature_matrix, centers, labels, sil_avg, reduce_dim):

    fig, (ax1, ax2) = plt.subplots(1, 2)
    ax1.set_xlim([-0.1, 1])
    # The (n_clusters+1)*10 is for inserting blank space between silhouette
    # plots of individual clusters, to demarcate them clearly.
    ax1.set_ylim([0, len(feature_matrix) + (n_clusters + 1) * 10])

    sil_samples = silhouette_samples(feature_matrix, labels, metric = "euclidean")
    y_lower = 10
    for i in range(n_clusters):
        ith_cluster_sil_values = sil_samples[labels == i]
        ith_cluster_sil_values.sort()
        ith_cluster_size = ith_cluster_sil_values.shape[0]

        y_upper = y_lower + ith_cluster_size
        color = cm.nipy_spectral(float(i) / n_clusters)

        ax1.fill_betweenx(np.arange(y_lower, y_upper),
                0, ith_cluster_sil_values,
                facecolor=color, edgecolor=color, alpha=0.7)

            # Label the silhouette plots with their cluster numbers at the middle
        ax1.text(-0.05, y_lower + 0.5 * ith_cluster_size, str(i))

            # Compute the new y_lower for next plot
        y_lower = y_upper + 10  # 10 for the 0 samples

    ax1.set_title("The silhouette plot for the various clusters.")
    ax1.set_xlabel("The silhouette coefficient values")
    ax1.set_ylabel("Cluster label")

    # The vertical line for average silhouette score of all the values
    ax1.axvline(x = sil_avg, color="red", linestyle="--")

    ax1.set_yticks([])  # Clear the yaxis labels / ticks
    ax1.set_xticks([-0.1, 0, 0.2, 0.4, 0.6, 0.8, 1])

    plt.suptitle(("Silhouette analysis for KMeans clustering on sample data "
        "with n_clusters = %d" % n_clusters),
        fontsize=14, fontweight='bold')

    if reduce_dim == False:
        return

    # -------------------------- Plotting the posts -------------------------- #

    colors = cm.nipy_spectral(labels.astype(float) / n_clusters)

    ax2.scatter(feature_matrix[:, 0], feature_matrix[:, 1], marker='.', s=30, lw=0, alpha=0.7,
                c=colors, edgecolor='k')

    # Draw white circles at cluster centers
    ax2.scatter(centers[:, 0], centers[:, 1], marker='o',
                c="white", alpha=1, s=200, edgecolor='k')

    for i, c in enumerate(centers):
        ax2.scatter(c[0], c[1], marker='$%d$' % i, alpha=1,
                    s=50, edgecolor='k')

    ax2.set_title("The visualization of the clustered data.")
    ax2.set_xlabel("Feature space for the 1st feature")
    ax2.set_ylabel("Feature space for the 2nd feature")

# https://github.com/Behrouz-Babaki/COP-Kmeans
# it appears that the differences between the wcss of clusters is lower here than without contraints
def get_suspects_constrained_k_means(suspect_count, feature_matrix, member_per_post_dicts, reduce_dim, plot):

    must_link = []
    cannot_link = []
    wcss = []
    sil_avgs = []

    most_likely_k = 0
    max_sil_avg = 0

    populate_must_link(must_link, member_per_post_dicts)

    for n_clusters in range(1, suspect_count + 1):
        k_clusters, k_centers = cop_kmeans(dataset = feature_matrix,
                                            k = n_clusters, 
                                            ml = must_link,
                                            cl = cannot_link)
        current_wcss = 0
        for j in range(len(k_clusters)):
            cluster_index = k_clusters[j]
            current_wcss += get_dist(feature_matrix[j], k_centers[cluster_index]) ** 2

        wcss.append(current_wcss)

        if n_clusters >= 2 and n_clusters <= len(feature_matrix) - 1:
            labels = np.array(k_clusters)
            sil_avg = silhouette_score(feature_matrix, labels, metric = "euclidean")
            sil_avgs.append(sil_avg)

            if sil_avg > max_sil_avg:
                max_sil_avg = sil_avg
                most_likely_k = n_clusters

            # required by some code in plot_silhouettes_and_posts()
            k_centers = np.array(k_centers)

            if plot == True:
                plot_silhouettes_and_posts(n_clusters, feature_matrix, k_centers, labels, sil_avg, reduce_dim)

    if plot == True:      
        plot_results(wcss = wcss, sil_avgs = sil_avgs)

    logging.info("This group most likely has %d subclusters of real users.\n" % most_likely_k)

    return most_likely_k

def get_suspects_k_means(suspect_count, feature_matrix, reduce_dim, plot):

    wcss = []
    sil_avgs = []

    most_likely_k = 0
    max_sil_avg = 0

    for n_clusters in range(1, suspect_count + 1):
        k_means = KMeans(n_clusters = n_clusters, 
                            init = "k-means++",    
                            max_iter = 300,
                            n_init = 10,
                            random_state = 0)
        k_means.fit(feature_matrix)
        wcss.append(k_means.inertia_)

        if n_clusters >= 2:
            labels = k_means.labels_
            sil_avg = silhouette_score(feature_matrix, labels, metric = "euclidean")
            sil_avgs.append(sil_avg)

            if sil_avg > max_sil_avg:
                max_sil_avg = sil_avg
                most_likely_k = n_clusters

            if plot == True:
                plot_silhouettes_and_posts(n_clusters, feature_matrix, k_means.cluster_centers_, labels, sil_avg, reduce_dim)

    if plot == True:
        plot_results(wcss = wcss, sil_avgs = sil_avgs)

    logging.info("This group most likely has %d subclusters of real users.\n" % most_likely_k)

    return most_likely_k

# TODO create dendogram technique (hierarchical clustering)
def get_suspects(method, clusters, psql_interface, posts_args, reduce_dim, plot, dim_reduction, n_components, testing):

    to_ret = {}

    if dim_reduction == "pca":
        reducer = PCA(n_components = n_components)
    elif dim_reduction == "tsne":
        reducer = TSNE(n_components = n_components)
    for i in range(len(clusters)):

        cluster = clusters[i]

        # member_aggr_dicts is not used in this method
        member_aggr_dicts, member_per_post_dicts = get_member_dicts_from_cluster(cluster = cluster, 
                                                                                 psql_interface = psql_interface,
                                                                                 posts_args = posts_args,
                                                                                 testing = testing)

        # during the previous method, it may be the case that some member(s) have no features at all
        # I have discovered this when using function words.
        # This means that the size of the cluster will no longer be the correct limit for the number of 
        # possible subclusters. Instead, use the size of member_aggr_dicts. It ignores users with no features
        # Also, it's possible that no member in this cluster has any features. In that case, just say
        # you cannot analyse this cluster

        suspect_count = len(member_aggr_dicts)

        if suspect_count == 0:
            logging.debug(timestamped("Cannot analyse this cluster. It doesn't have any features.\n"))
            continue
        elif suspect_count == 1:
            logging.debug(timestamped("Cannot analyse this cluster. There is only 1 user with features in this cluster.\n"))
            continue

        feature_matrix = []
        for member in member_per_post_dicts:
            for post in member_per_post_dicts[member]:
                feature_matrix.append(member_per_post_dicts[member][post])


        # have to sort the features in order to be able to properly analyse them,
        # as we'll only keep the feature values, the keys will be forgotten, 
        # as they are not needed by the clusterer/classifier
        sorted_keys = sorted(get_dict_keys(feature_matrix[0]))

        feature_matrix = [[post_dict[key] for key in sorted_keys] for post_dict in feature_matrix]

        if reduce_dim == True:
            feature_matrix = reducer.fit_transform(feature_matrix)

        # TODO see if the plots can be saved somewhere in res\ instead of being immediately displayed
        # on the screen after process finishes executing

        if method == "intuitive":
            k = get_suspects_intuitively(member_aggr_dicts = member_aggr_dicts, member_per_post_dicts = member_per_post_dicts)
        elif method == "k_means":
            k = get_suspects_k_means(suspect_count = suspect_count, feature_matrix = feature_matrix, reduce_dim = reduce_dim, plot = plot)
        elif method == "cop_k_means":
            k = get_suspects_constrained_k_means(suspect_count = suspect_count, feature_matrix = feature_matrix, member_per_post_dicts = member_per_post_dicts, reduce_dim = reduce_dim, plot = plot)
        else:
            logging.error(timestamped("Method not implemented."))

        to_ret[i] = k

    return to_ret

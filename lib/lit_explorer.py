import os
import re
import spacy
import numpy as np
from numpy import unique
from numpy import where
from sklearn.cluster import AffinityPropagation
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
from joblib import load
from nltk.corpus import stopwords
import math

included_fields = load(os.path.join(os.path.dirname(__file__), 'data', 'included_fields.joblib'))
jurisdictions = load(os.path.join(os.path.dirname(__file__), 'data', 'jurisdictions.joblib'))
groups = load(os.path.join(os.path.dirname(__file__), 'data', 'groups.joblib'))
clf_field_names = load(os.path.join(os.path.dirname(__file__), 'data', 'clf_field_names.joblib'))
stop_words = set(stopwords.words('english'))

nlp = spacy.load('en_core_web_lg') # this takes a while to loadimport os


def reCase(text):
    # a quick and dirty way to pull words out of
    # snake_case, camelCase and the like.
    output = re.sub("(\w|\d)(_|-)(\w|\d)","\\1 \\3",text.strip())
    output = re.sub("([a-z])([A-Z]|\d)","\\1 \\2",output)
    output = re.sub("(\d)([A-Z]|[a-z])","\\1 \\2",output)
    return output


def regex_norm_field(text):
    # Takes an auto-generated form field name and uses
    # regex to convert it into an Assembly Line standard field.
    # See https://suffolklitlab.org/docassemble-AssemblyLine-documentation/docs/label_variables/

    regex_list = [

        # Personal info
        ## Name & Bio
        ["^((My|Full( legal)?) )?Name$","users1_name"],
        ["^(Typed or )?Printed Name\s?\d*$","users1_name"],
        ["^(DOB|Date of Birth|Birthday)$","users1_birthdate"],
        ## Address
        ["^(Street )?Address$","users1_address_line_one"],
        ["^City State Zip$","users1_address_line_two"],
        ["^City$","users1_address_city"],
        ["^State$","users1_address_state"],
        ["^Zip( Code)?$","users1_address_zip"],
        ## Contact
        ["^(Phone|Telephone)$","users1_phone_number"],
        ["^Email( Adress)$","users1_email"],

        # Parties
        ["^plaintiff\(?s?\)?$","plantiff1_name"],
        ["^defendant\(?s?\)?$","defendant1_name"],
        ["^petitioner\(?s?\)?$","petitioners1_name"],
        ["^respondent\(?s?\)?$","respondents1_name"],

        # Court info
        ["^(Court\s)?Case\s?(No|Number)?\s?A?$","docket_number"],
        ["^File\s?(No|Number)?\s?A?$","docket_number"],

        # Form info
        ["^(Signature|Sign( here)?)\s?\d*$","users1_signature"],
        ["^Date\s?\d*$","signature_date"],
    ]

    for regex in regex_list:
        text = re.sub(regex[0],regex[1],text, flags=re.IGNORECASE)
    return text


def reformat_field(text,max_length=30):
    # h/t https://towardsdatascience.com/nlp-building-a-summariser-68e0c19e3a93

    #print(text)

    orig_title = text.lower()
    orig_title = re.sub("[^a-zA-Z]+"," ",orig_title)
    orig_title_words = orig_title.split()

    deduped_sentence = []
    for word in orig_title_words:
        if word not in deduped_sentence:
            deduped_sentence.append(word)

    filtered_sentence = [w for w in deduped_sentence if not w.lower() in stop_words]

    filtered_title_words = filtered_sentence

    characters = len(' '.join(filtered_title_words))

    if characters > 0:

        words = len(filtered_title_words)
        av_word_len = math.ceil(len(' '.join(filtered_title_words))/len(filtered_title_words))
        x_words = math.floor((max_length)/av_word_len)


        sim_mat = np.zeros([len(filtered_title_words),len(filtered_title_words)])# will populate it with cosine_similarity values
        # for each word compared to other
        for i in range(len(filtered_title_words)):
            for j in range(len(filtered_title_words)):
                if i != j:
                    sim_mat[i][j] = cosine_similarity(nlp(filtered_title_words[i]).vector.reshape(1,300), nlp(filtered_title_words[j]).vector.reshape(1,300))[0,0]

        try:
            nx_graph = nx.from_numpy_array(sim_mat)
            scores = nx.pagerank(nx_graph)# print final values of words
            sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)

            if x_words > len(scores):
                x_words=len(scores)

            i = 0
            new_title = ""
            for x in filtered_title_words:
                #print(scores[i],sorted_scores[x_words][1])
                if scores[i] >= sorted_scores[x_words-1][1]:
                    if len(new_title)>0: new_title+="_"
                    new_title += x
                i+=1

            return new_title
        except:
            return '_'.join(filtered_title_words)
    else:
        if re.search("^(\d+)$", text):
            return "unknown"
        else:
            return re.sub("\s+","_",text.lower())


def vectorize(text):
    output = nlp(str(text)).vector
    return output


def norm(row):
    try:
        matrix = row.reshape(1,-1).astype(np.float64)
        return normalize(matrix, axis=1, norm='l1')[0]
    except Exception as e:
        print("===================")
        print("Error: ",e)
        print("===================")
        return np.NaN


def normalize_name(jur,group,n,per,last_field,this_field):

    # Add hard coded conversions maybe by calling a function
    # if returns 0 then fail over to ML or otherway around poor prob -> check hard-coded

    if this_field not in included_fields:
        this_field = reCase(this_field)

        out_put = regex_norm_field(this_field)
        conf = 1.0

        if out_put==this_field:
            params = []
            for item in jurisdictions:
                if jur== item:
                    params.append(1)
                else:
                    params.append(0)
            for item in groups:
                if group== item:
                    params.append(1)
                else:
                    params.append(0)
            params.append(n)
            params.append(per)
            for vec in norm(vectorize(this_field)):
                params.append(vec)
            #for vec in norm(vectorize(last_field)):
            #    params.append(vec)

            for item in included_fields:
                if last_field==item:
                    params.append(1)
                else:
                    params.append(0)

            pred = clf_field_names.predict([params])
            prob = clf_field_names.predict_proba([params])

            conf = prob[0].tolist()[prob[0].tolist().index(max(prob[0].tolist()))]
            out_put = pred[0]

    else:
        out_put = this_field
        conf = 1

    if out_put in included_fields:
        if conf >= 0:
            return "*"+out_put,conf #+"| was <i>%s</i> (%.2f conf)"%(this_field,conf) #, conf
        else:
            return reformat_field(this_field),conf #+"| was <i>%s</i> (%.2f conf)"%(this_field,conf) #, conf
    else:
        return reformat_field(this_field),conf #+"| was <i>%s</i> (%.2f conf)"%(this_field,conf) #, conf


def cluster_screens(fields=[],damping=0.7):
    # Takes in a list (fields) and returns a suggested screen grouping
    # Set damping to value >= 0.5 or < 1 to tune how related screens should be

    vec_mat = np.zeros([len(fields),300])
    for i in range(len(fields)):
        vec_mat[i] = [nlp(reCase(fields[i])).vector][0]

    # create model
    model = AffinityPropagation(damping=damping,random_state=4)
    # fit the model
    model.fit(vec_mat)
    # assign a cluster to each example
    yhat = model.predict(vec_mat)
    # retrieve unique clusters
    clusters = unique(yhat)

    screens = {}
    #sim = np.zeros([5,300])
    i=0
    for cluster in clusters:
        this_screen = where(yhat == cluster)[0]
        vars = []
        j=0
        for screen in this_screen:
            #sim[screen]=vec_mat[screen] # use this spot to add up vectors for compare to list
            vars.append(fields[screen])
            j+=1
        screens["screen_%s"%i]=vars
        i+=1

    return screens

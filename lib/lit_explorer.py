import re

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

import spacy
import numpy as np
from numpy import unique
from numpy import where
from sklearn.cluster import AffinityPropagation
from sklearn.metrics.pairwise import cosine_similarity

nlp = spacy.load('en_core_web_lg') # this takes a while to loadimport os

def cluster_screens(fields=[],damping=0.9):
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

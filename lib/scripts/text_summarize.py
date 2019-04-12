import numpy as np
import pandas as pd
import re
import networkx as nx
from sklearn.metrics.pairwise import cosine_similarity

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize

import requests


# function to remove stopwords
def remove_stopwords(sen):
    stop_words = stopwords.words('english')
    sen_new = " ".join([i for i in sen if i not in stop_words])
    return sen_new

def preprocess_sentences(sentences):
    # remove punctuations, numbers and special characters
    clean_sentences = pd.Series(sentences).str.replace("[^a-zA-Z]", " ")

    # make alphabets lowercase
    clean_sentences = [s.lower() for s in clean_sentences]
    # remove stopwords from the sentences
    clean_sentences = [remove_stopwords(r.split()) for r in clean_sentences]

    return clean_sentences

def extract_word_vec():
    # Extract word vectors
    word_embeddings = {}
    f = open('glove.6B.100d.txt', encoding='utf-8')
    for line in f:
        values = line.split()
        word = values[0]
        coefs = np.asarray(values[1:], dtype='float32')
        word_embeddings[word] = coefs
    f.close()

    return word_embeddings

def get_sent_scores(word_embeddings, sentences):
    clean_sentences = preprocess_sentences(sentences)

    # get sentence vectors
    sentence_vectors = []
    for i in clean_sentences:
        if len(i) != 0:
            v = sum([word_embeddings.get(w, np.zeros((100,))) for w in i.split()])/(len(i.split())+0.001)
        else:
            v = np.zeros((100,))
        sentence_vectors.append(v)

    # get similarity matrix
    sim_mat = np.zeros([len(clean_sentences), len(clean_sentences)])
    for i in range(len(clean_sentences)):
        for j in range(len(clean_sentences)):
            if i != j:
                sim_mat[i][j] = cosine_similarity(sentence_vectors[i].reshape(1,100), sentence_vectors[j].reshape(1,100))[0,0]

    # apply page rank to similarity matrix
    nx_graph = nx.from_numpy_array(sim_mat)
    scores = nx.pagerank(nx_graph)

    return scores

if __name__ == "__main__":
    df = pd.read_csv("tennis_articles_v4.csv")
    sentences = []
    for s in df['article_text']:
        sentences.append(sent_tokenize(s))

    sentences = [y for x in sentences for y in x] # flatten list

    print('tokenized sentences')

    r = requests.post('http://localhost:8080/get_sent_scores', json={"sentences": sentences})

    print(r.json())
    """
    word_embeddings = extract_word_vec()
    scores = get_sent_scores(word_embeddings, sentences)

    ranked_sentences = sorted(((scores[i],s) for i,s in enumerate(sentences)), reverse=True)

    for i in range(10):
        print(ranked_sentences[i][1])
    """


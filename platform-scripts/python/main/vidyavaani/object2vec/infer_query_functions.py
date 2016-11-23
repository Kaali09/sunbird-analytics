import os
import sys
import gensim as gs
import logging  # Log the data given
import numpy as np
import ConfigParser
import json
import ast  # remove
import langdetect
import re
from nltk.corpus import stopwords
stopword = set(stopwords.words("english"))
langdetect.DetectorFactory.seed = 0

root = os.path.dirname(os.path.abspath(__file__))
utils = os.path.join((os.path.split(root)[0]), 'utils')
# Insert at front of list ensuring that our util is executed first in
sys.path.insert(0, utils)
from find_files import *
resource = os.path.join((os.path.split(root)[0]), 'resources')
config_file = os.path.join(resource, 'config.properties')
# geting paths from config file
config = ConfigParser.SafeConfigParser()
config.read(config_file)

# op_dir = config.get('FilePath', 'corpus_path')
log_dir = config.get('FilePath', 'log_path')

# if not os.path.exists(model_loc):
#     logging.info('model folder do not exist')

# Set up logging
infer_log_file = os.path.join(log_dir, 'inferQuery.log')

def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]

def get_immediate_subdirectories_fullpath(a_dir):
    return [os.path.join(a_dir, name) for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]

def uniqfy_list(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def get_all_lang(directory, string):
    lst_lang = [name
                for root, dirs, files in os.walk(directory)
                for name in files
                if name.endswith((string))]
    lst_lang = uniqfy_list(lst_lang)
    return lst_lang

def get_vector_dimension():
    try:
        all_models = findFiles(model_loc, ['text', 'tags'])
        any_model = all_models[0]
        model_path = os.path.join(model_loc, any_model)
        query = 'test'
        model = gs.models.doc2vec.Doc2Vec.load(model_path)
        q_vec = model.infer_vector(query)
        test_vector_list = np.array(q_vec).tolist()
        n_dim = len(test_vector_list)
    except:
        n_dim = 50  # default value ,should take it from stdin?
    return n_dim

def is_ascii(s):
    return all(ord(c) < 128 for c in s)

def get_norm_vec(vector_list):
    if not  all(v == 0 for v in vector_list):
        x = np.array(vector_list).reshape(1,50)
#         t = x.transpose()
#         dot_product = math.sqrt(np.dot(x, t))
        norm_vector = x/np.linalg.norm(x)
        norm_vector = norm_vector.tolist()[0]
    else:
        norm_vector = vector_list
#     norm_vector = [ '%.6f' % elem for elem in norm_vector ]
    return norm_vector
def process_query(line,language):
    # word_list = []
    # if(language == 'en' or language == 'en-text'):
    #     line = re.sub("[^a-zA-Z]", " ", line)
    #     for word in line.split(' '):
    #         if word not in stopword and len(word) > 1:
    #             word_list.append(word.lower())
    # elif(language == 'tags'):
    #     pre_query = line.split(",")
    #     word_list = []
    #     for str_word in pre_query:
    #         word_list.append("".join(str_word.split()).lower())     
    # else:
    #     for word in line.split(' '):
    #         word_list.append(word.lower())
    # return word_list

    word_list = []

    if language == 'tags':
        pre_query = line.split(",")
        word_list = []
        for str_word in pre_query:
            word_list.append("".join(str_word.split()).lower())
            word_list = uniqfy_list(word_list)
    else:
        try:
            line = unicode(line, "UTF-8")
            line = line.replace(u"\u00A0", " ")
        except:
            line = line
        if is_ascii(line):# Any language using ASCII characters goes here
            line = re.sub("[^a-zA-Z]", " ", line)
            for word in line.split(' '):
                if word not in stopword and len(word) > 1:
                    word_list.append(word.lower())
        else:
            for word in line.split(' '):
                word_list.append(word)
    return word_list

def get_vectors_LDA(model, query):
#     print 'query: '+ str(query)
    pr_query = model.id2word.doc2bow(query)
#     print 'pr_query: '+ str(pr_query)
    temp_vec = model[pr_query]
    num = range(0,50)
    listofzeros = [0] * 50 
    t_dict = dict(zip(num, listofzeros))
    for t_list in temp_vec:
        key = t_list[0]
        t_dict[key] = t_list[1]
    # flattened = []
    flattened = t_dict.values()
    return flattened

response = {}
all_vector = []
# to get the dimension of vectors from model
n_dim = get_vector_dimension()

def infer_query(inferFlag, model_loc, op_dir):
    if inferFlag == 'true':
        # if vectors for all the content are to be populated
        lst_folder = get_immediate_subdirectories(op_dir)
        for folder in lst_folder:
            vector_dict = {}
            content_folder = os.path.join(op_dir, folder)
            lst_lang = get_all_lang(content_folder, ('tags', 'text'))
            for lang in lst_lang:
                file_path = os.path.join(content_folder, lang)
                if not os.path.exists(file_path):
                    logging.info('%s not found' % (file_path))
                    continue
                txt = open(file_path)
                # reading the text from corpus
                query = txt.read()
                query = process_query(query,lang)
                if lang == "tags":
                    query = uniqfy_list(query)
                model_path = os.path.join(model_loc, lang)
                # logging.info("model_path:"+model_path)
                if not os.path.exists(model_path):
                    logging.info(
                        '%s model not found, using default model' % (lang))
                    model_path = os.path.join(model_loc, 'en-text')
                    if not os.path.exists(model_path):
                        logging.info(
                            'default model not found, skipping vector this language')
                        continue
                model = gs.models.doc2vec.Doc2Vec.load(model_path)
                q_vec = model.infer_vector(query, alpha=0.1, min_alpha=0.0001,steps=20)
                # q_vec=model.infer_vector(query.split(' '),alpha=0.1, min_alpha=0.0001, steps=5)
                vector_list = np.array(q_vec).tolist()
                vector_list = get_norm_vec(vector_list)
                if not lang == 'tags':
                    vector_dict['text_vec'] = vector_list
                    logging.info('Vectors for text retrieved')
                else:
                    vector_dict['tag_vec'] = vector_list
                    # logging.info(vector_list)
                    logging.info('Vectors for tags retrieved')
            vector_dict['contentId'] = folder
            if not 'tag_vec' in vector_dict:
                logging.info('no tags data, so adding zero vectors')
                vector_dict['tag_vec'] = np.array(np.zeros(n_dim)).tolist()
            if not 'text_vec' in vector_dict:
                logging.info('no text data, so adding zero vectors')
                vector_dict['text_vec'] = np.array(np.zeros(n_dim)).tolist()
            all_vector.append(vector_dict)
            response['content_vectors'] = all_vector
        # logging.info(json.dumps(response))
        return(json.dumps(response))

    else:
        contentID = std_input['contentId']
        docs = std_input['document']
        vector_dict = {}
        for key in docs.keys():
            if not key == 'tags':
                model = '%s-text' % (key)
            else:
                model = key
            query = docs[key]
            query = process_query(query,key)
            if key == 'tags':
                query = uniqfy_list(query)
            model_path = os.path.join(model_loc, model)
            if not os.path.exists(model_path):
                logging.info('%s model not found, using default model' % (model))
                model_path = os.path.join(model_loc, 'en-text')
                if not os.path.exists(model_path):
                    logging.info(
                        'default model not found, skipping vector this language')
                    continue
            gensim_model = gs.models.doc2vec.Doc2Vec.load(model_path)
            q_vec = gensim_model.infer_vector(query, alpha=0.1, min_alpha=0.0001,steps=20 )
            vector_list = np.array(q_vec).tolist()
            if not key == 'tags':
                vector_dict['text_vec'] = vector_list
                logging.info('Vectors for text retrieved')
            else:
                vector_dict['tag_vec'] = vector_list
                logging.info('Vectors for tags retrieved')
        vector_dict['contentId'] = contentID
        if not 'tag_vec' in vector_dict:
            logging.info('no tags data, so adding zero vectors')
            vector_dict['tag_vec'] = np.array(np.zeros(n_dim)).tolist()
        if not 'text_vec' in vector_dict:
            logging.info('no text data, so adding zero vectors')
            vector_dict['text_vec'] = np.array(np.zeros(n_dim)).tolist()
        all_vector.append(vector_dict)
        response['content_vectors'] = all_vector
        return (json.dumps(response))

def get_vectors(model_loc, op_dir):
    lst_folder = get_immediate_subdirectories_fullpath(op_dir)
    for content_folder in lst_folder:
        vector_dict = {}
        lst_lang = get_all_lang(content_folder, ('tags', 'text')) 
        # print content_folder
        # print lst_lang
        for lang in lst_lang:
            file_path = os.path.join(content_folder, lang)
            if not os.path.exists(file_path):
                logging.info('%s not found' % (file_path))
                continue   
            model_path = os.path.join(model_loc, lang)
            model = gs.models.doc2vec.Doc2Vec.load(model_path)
            # print file_path
            q_vec = model.docvecs[file_path]
            vector_list = np.array(q_vec).tolist()
            if not lang == 'tags':
                vector_dict['text_vec'] = vector_list
                logging.info('Vectors for text retrieved')
            else:
                vector_dict['tag_vec'] = vector_list
                # logging.info(vector_list)
                logging.info('Vectors for tags retrieved')
        folder = os.path.basename(os.path.normpath(content_folder))
        vector_dict['contentId'] = folder            
        if not 'tag_vec' in vector_dict:
            logging.info('no tags data, so adding zero vectors')
            vector_dict['tag_vec'] = np.array(np.zeros(n_dim)).tolist()
        if not 'text_vec' in vector_dict:
            logging.info('no text data, so adding zero vectors')
            vector_dict['text_vec'] = np.array(np.zeros(n_dim)).tolist()
        all_vector.append(vector_dict)
        response['content_vectors'] = all_vector
    # logging.info(json.dumps(response))
    return(json.dumps(response))

# Infer search string from model
# https://github.com/RaRe-Technologies/gensim/blob/develop/gensim/models/doc2vec.py#L499
def infer_query_LDA(inferFlag, model_loc, op_dir):
    if inferFlag == 'true':
        # if vectors for all the content are to be populated
        lst_folder = get_immediate_subdirectories(op_dir)
        for folder in lst_folder:
            vector_dict = {}
            content_folder = os.path.join(op_dir, folder)
            lst_lang = get_all_lang(content_folder, ('tags', 'text'))
            for lang in lst_lang:
                file_path = os.path.join(content_folder, lang)
                if not os.path.exists(file_path):
                    logging.info('%s not found' % (file_path))
                    continue
                txt = open(file_path)
                # reading the text from corpus
                query = txt.read()
                query = process_query(query,lang)
                if lang == "tags":
                    query = uniqfy_list(query)
                model_path = os.path.join(model_loc, lang)
                # logging.info("model_path:"+model_path)
                if not os.path.exists(model_path):
                    logging.info(
                        '%s model not found, using default model' % (lang))
                    model_path = os.path.join(model_loc, 'en-text')
                    if not os.path.exists(model_path):
                        logging.info(
                            'default model not found, skipping vector this language')
                        continue
                model = gs.models.ldamodel.LdaModel.load(model_path)
                # pr_query = model.id2word.doc2bow(query)
                q_vec = get_vectors_LDA(model, query)
                # q_vec=model.infer_vector(query.split(' '),alpha=0.1, min_alpha=0.0001, steps=5)
                vector_list = np.array(q_vec).tolist()
                if not lang == 'tags':
                    vector_dict['text_vec'] = vector_list
                    logging.info('Vectors for text retrieved')
                else:
                    vector_dict['tag_vec'] = vector_list
                    # logging.info(vector_list)
                    logging.info('Vectors for tags retrieved')
            vector_dict['contentId'] = folder
            if not 'tag_vec' in vector_dict:
                logging.info('no tags data, so adding zero vectors')
                vector_dict['tag_vec'] = np.array(np.zeros(n_dim)).tolist()
            if not 'text_vec' in vector_dict:
                logging.info('no text data, so adding zero vectors')
                vector_dict['text_vec'] = np.array(np.zeros(n_dim)).tolist()
            all_vector.append(vector_dict)
            response['content_vectors'] = all_vector
        # logging.info(json.dumps(response))
        return(json.dumps(response))


def inference(query, model):
    model.sg = 1  # https://github.com/RaRe-Technologies/gensim/blob/develop/gensim/models/doc2vec.py#L721
    q_vec = model.infer_vector(query.split(
        ' '), alpha=0.1, min_alpha=0.0001, steps=5)
    distance = 0
    predicted_idx = 0
    for idx in range(len(model.docvecs)):
        dist = np.dot(gs.matutils.unitvec(
            model.docvecs[idx]), gs.matutils.unitvec(q_vec))
        if(dist > distance):
            distance = dist
            predicted_idx = idx
    # print(distance)
    return model.docvecs.index_to_doctag(predicted_idx)
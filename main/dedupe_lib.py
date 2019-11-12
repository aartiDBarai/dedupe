from future.builtins import next
from builtins import input

import os
import csv
import re
import logging
import optparse

import dedupe
from unidecode import unidecode

optp = optparse.OptionParser()
optp.add_option('-v', '--verbose', dest='verbose', action='count',
                help='Increase verbosity (specify multiple times for more)'
                )
(opts, args) = optp.parse_args()
log_level = logging.WARNING 
if opts.verbose:
    if opts.verbose == 1:
        log_level = logging.INFO
    elif opts.verbose >= 2:
        log_level = logging.DEBUG
logging.getLogger().setLevel(log_level)


input_file = ''
output_file = 'output.csv'
settings_file = 'learned_settings'
training_file = 'training.json'


def preProcess(column):
    try : # python 2/3 string differences
        column = column.decode('utf8')
    except AttributeError:
        pass
    column = unidecode(column)
    column = re.sub('  +', ' ', column)
    column = re.sub('\n', ' ', column)
    column = column.strip().strip('"').strip("'").lower().strip()
    # If data is missing, indicate that by setting the value to `None`
    if not column:
        column = None
    return column

def readData(filename, unique_col):
    data_d = {}
    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            clean_row = [(k, preProcess(v)) for (k, v) in row.items()]
            row_id = int(row[unique_col])
            data_d[row_id] = dict(clean_row)

    return data_d


def unique(seq) :
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def mark(label):
    if label == 'y' :
        labels['match'].append(record_pair)
        labeled = True
    elif label == 'n' :
        labels['distinct'].append(record_pair)
        labeled = True
    deduper.markPairs(labels)


def active_train():
    deduper.train()

    with open(os.getcwd()+"/media/training_files/"+training_file, 'w') as tf:
        deduper.writeTraining(tf)

    with open(os.getcwd()+"/media/settings_files/"+settings_file, 'wb') as sf:
        deduper.writeSettings(sf)
    rundedupe2()


def generate_question():
    global labels, record_pair
    n_match, n_distinct = (len(deduper.training_pairs['match']),
                               len(deduper.training_pairs['distinct']))

    uncertain_pairs = deduper.uncertainPairs()

    labels = {'distinct' : [], 'match' : []}
    label = ''

    record_pair = uncertain_pairs[0]
    que = []
    for pair in record_pair:
        rec = []
        for field in fields:
            line = "%s : %s" % (field, pair[field])
            rec.append(line)
        que.append(rec)
    que.append(["Yes: "+str(n_match), "No: "+str(n_distinct)])
    return que


def rundedupe(input_file_path, unique_col, dedupe_cols):
    global input_file, data_d, deduper, fields
    input_file = input_file_path
    print('importing data ...')
    data_d = readData(input_file, unique_col)
    if os.path.exists(os.getcwd()+"/media/settings_files/"+settings_file):
        print('reading from', settings_file)
        with open(os.getcwd()+"/media/settings_files/"+settings_file, 'rb') as f:
            deduper = dedupe.StaticDedupe(f)
        ret = False
    else:
        fields = []
        for i in dedupe_cols:
            fields.append({'field' : i, 'type': 'String'})

        deduper = dedupe.Dedupe(fields)
        deduper.sample(data_d, 15000)
        if os.path.exists(os.getcwd()+"/media/training_files/"+training_file):
            print('reading labeled examples from ', training_file)
            with open(os.getcwd()+"/media/training_files/"+training_file, 'rb') as f:
                deduper.readTraining(f)
        print('starting active labeling...')
        ret = True
    fields = unique(field.field
                    for field
                    in deduper.data_model.primary_fields)
    return ret


def rundedupe2():
    threshold = deduper.threshold(data_d, recall_weight=1)
    print('clustering...')
    clustered_dupes = deduper.match(data_d, threshold)
    print('# duplicate sets', len(clustered_dupes))
    cluster_membership = {}

    cluster_id = 0
    for (cluster_id, cluster) in enumerate(clustered_dupes):
        id_set, scores = cluster
        cluster_d = [data_d[c] for c in id_set]
        canonical_rep = dedupe.canonicalize(cluster_d)
        for record_id, score in zip(id_set, scores):
            cluster_membership[record_id] = {
            "cluster id" : cluster_id,
            "canonical representation" : canonical_rep,
            "confidence": score
            }
    singleton_id = cluster_id + 1
    with open(os.getcwd()+"/media/output_files/"+output_file, 'w') as f_output, open(input_file) as f_input:
        writer = csv.writer(f_output)
        reader = csv.reader(f_input)
        heading_row = next(reader)
        heading_row.insert(0, 'confidence_score')
        heading_row.insert(0, 'Cluster ID')
        canonical_keys = canonical_rep.keys()
        for key in canonical_keys:
            heading_row.append('canonical_' + key)
            writer.writerow(heading_row)
            for row in reader:
                row_id = int(row[0])
                if row_id in cluster_membership:
                    cluster_id = cluster_membership[row_id]["cluster id"]
                    canonical_rep = cluster_membership[row_id]["canonical representation"]
                    row.insert(0, cluster_membership[row_id]['confidence'])
                    row.insert(0, cluster_id)
                    for key in canonical_keys:
                        row.append(canonical_rep[key].encode('utf8'))
                else:
                    row.insert(0, None)
                    row.insert(0, singleton_id)
                    singleton_id += 1
                    for key in canonical_keys:
                        row.append(None)
                writer.writerow(row)



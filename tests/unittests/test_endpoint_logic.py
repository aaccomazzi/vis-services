import sys, os
import unittest
import json
PROJECT_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__),'../../'))
sys.path.append(PROJECT_HOME)
from lib import author_network
from lib import word_cloud
import config


#input data


input_js_word_cloud = json.load(open(PROJECT_HOME + "/tests/test_input/word_cloud_input.json"))

#has more than 50 nodes
input_js_author_network = json.load(open(PROJECT_HOME + "/tests/test_input/author_network_before_groups_func_large.json"))

# has fewer than 50 nodes
input_js_author_network_small = json.load(open(PROJECT_HOME + "/tests/test_input/author_network_before_groups_func_small.json"))

#result data

test_js_word_cloud = json.load(open(PROJECT_HOME + "/tests/test_output/word_cloud_accomazzi,a.json"))
test_json_word_cloud_min_occurrences = json.load(open(PROJECT_HOME + "/tests/test_output/word_cloud_accomazzi,a_min_occurrence_word_5.json"))

test_js_author_network = json.load(open(PROJECT_HOME + "/tests/test_output/author_network_accomazzi,a.json"))
test_js_author_network_max_groups = json.load(open(PROJECT_HOME + "/tests/test_output/author_network_accomazzi,a_max_groups_3.json"))


class TestEndpointLogic(unittest.TestCase):

  def test_word_cloud_resource(self):

    self.maxDiff = None

    # function: add_punc_and_remove_redundancies 
    # uses the text returned from solr to do some cleaning up of the idf info returned by solr,
    # reducing counts of token components of slashed or dashed words
    # after this point the solr text is ignored, only the tf/idf data is used

    tf_idf_dict = {'word':{'tf' :[3], 'tf-idf' : [0.5]}, 'dashed' : {'tf' :[1], 'tf-idf' : [0.5]}, 'slashed' : {'tf' :[1], 'tf-idf' : [0.5]}, 'dashedword' : {'tf' :[1], 'tf-idf' : [0.5]}, 'slashedword' : {'tf' :[1], 'tf-idf' : [0.5]}}

    text_list = ['word', 'dashed-word', 'slashed/word']

    updated_info_dict = word_cloud.add_punc_and_remove_redundancies(tf_idf_dict, text_list)

    expected_outcome_info_dict = {'word':{'tf' :[1], 'tf-idf' : [0.5]}, 'dashed-word': {'tf' :[1], 'tf-idf' : [0.5]}, 'slashed/word' : {'tf' :[1], 'tf-idf' : [0.5]}, 'dashed' : {'tf' :[-1], 'tf-idf' : [0.5]}, 'slashed' : {'tf' :[0], 'tf-idf' : [0.5]}}

    self.assertEqual(updated_info_dict, expected_outcome_info_dict)

    # function: build_dict 
    # is a parent function to add_punc_and_remove_redundancies that takes an tf idf info and text info
    # and returns a token and acronym dictionary. The token dictionary is grouped by stem and includes
    # a list of idf for each different word


    tf_idf_dict = {
        'fakeId': {
            'abstract': {
                'word': {
                    'tf': [3],
                    'tf-idf': [0.5]
                },
                'dashed': {
                    'tf': [1],
                    'tf-idf': [0.5]
                },
                'slashed': {
                    'tf': [1],
                    'tf-idf': [0.5]
                },
                'dashedword': {
                    'tf': [1],
                    'tf-idf': [0.5]
                },
                'slashedword': {
                    'tf': [1],
                    'tf-idf': [0.5]
                }
            },
            'title': {
                'research': {
                    'tf': [1],
                    'tf-idf': [0.1]
                },
                'researcher': {
                    'tf': [1],
                    'tf-idf': [0.9]
                },
                'acr::fake': {
                    'tf': [1],
                    'tf-idf': [0.5]
                }
            }
        }
    }

    text_list = [{'id': 'fakeId', 'abstract': 'word dashed-word slashed/word', 'title' : 'research researcher FAKE'}]

    
    expected_outcome_info_dict = ({'dashedword': {'idf': [0.5], 'tokens': {'dashed-word': 1},  'record_count' : ['fakeId']},
    'research': {'idf': [0.9, 0.1], 'tokens': {'research': 1, 'researcher': 1},  'record_count' : ['fakeId', 'fakeId']},
    'slashedword': {'idf': [0.5], 'tokens': {'slashed/word': 1},  'record_count' : ['fakeId']},
    'word': {'idf': [0.5], 'tokens': {'word': 1}, 'record_count' : ['fakeId']}},
    {'FAKE': {'idf': [0.5], 'total_occurrences': 1, 'record_count' : ['fakeId']}})


    updated_info_dict = word_cloud.build_dict(tf_idf_dict, text_list)

    self.assertEqual(updated_info_dict, expected_outcome_info_dict)


    #function: combine_and_process_dicts
    #uses the expected outcome from the previous function

    combined_dict = word_cloud.combine_and_process_dicts(expected_outcome_info_dict[0], expected_outcome_info_dict[1])

    expected_combined_dict = {
    'dashed-word': {'idf': 0.5, 'total_occurrences' :1, 'record_count' :1 },
    'research' : {'idf': 0.5, 'total_occurrences' :2, 'record_count' :1 },
    'slashed/word':{'idf': 0.5, 'total_occurrences' :1, 'record_count' :1 },
    'word': {'idf': 0.5, 'total_occurrences' :1, 'record_count' :1 },
    'FAKE' : {'idf': 0.5, 'total_occurrences' :1, 'record_count' :1 }
    }

    self.assertEqual(combined_dict, expected_combined_dict)

   #testing the main word cloud generation function with large data

    processed_data = word_cloud.generate_wordcloud(input_js_word_cloud, min_occurrences_word=2, min_percent_word=3)
    self.assertEqual(json.loads(json.dumps(processed_data)), test_js_word_cloud)

    processed_data = word_cloud.generate_wordcloud(input_js_word_cloud, min_occurrences_word=5, min_percent_word=3)
    self.assertEqual(json.loads(json.dumps(processed_data)), test_json_word_cloud_min_occurrences)



  def test_author_network_resource(self):

    #current default
    max_groups = 8

    #testing group aggregation function

    #if it receives fewer than 50 nodes, it should just return the graph in the form {fullgraph : graph}

    processed_data_small = author_network.augment_graph_data(input_js_author_network_small, max_groups=max_groups)

    self.assertNotIn("summaryGraph", processed_data_small)

    #otherwise, it should return two graphs, the fullgraph and the group node graph. 

    input_js_author_network = json.load(open(PROJECT_HOME + "/tests/test_input/author_network_before_groups_func_large.json"))

    processed_data = author_network.augment_graph_data(input_js_author_network, max_groups=max_groups)

    self.assertTrue("summaryGraph" in processed_data)
    self.assertTrue("fullGraph" in processed_data)


    #The full graph will be filtered of nodes that didn't make it into one of the groups

    allowed_groups = sorted([n["id"] for n in test_js_author_network_max_groups["summaryGraph"]["nodes"]])
    allowed_groups = [a for a in allowed_groups if isinstance(a, int)]
    group_nums =sorted(list(set([n["group"]for n in test_js_author_network_max_groups['fullGraph']['nodes']])))

    self.assertEqual(allowed_groups, group_nums)

    # And it will have no more than max_groups number of groups

    groups = [d for d in processed_data["summaryGraph"]["nodes"] if not d.get("connector", None)]

    self.assertLessEqual(len(groups), max_groups)

    #testing entire function

    input_js_author_network = json.load(open(PROJECT_HOME + "/tests/test_input/author_network_before_groups_func_large.json"))

    processed_data = author_network.augment_graph_data(input_js_author_network, max_groups=max_groups)


    with open("test2.json", "w") as f:
        json.dump(processed_data, f)

    self.assertEqual(processed_data, test_js_author_network)
    



if __name__ == '__main__':
  unittest.main()
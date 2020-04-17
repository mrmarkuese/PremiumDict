# -*- coding: utf-8 -*-

import unittest
import sys
sys.path.insert(0, '../')
from PremiumDict.premium_dict import PremiumDict


class TestPremiumDictMethods(unittest.TestCase):
    def test_init(self):
        print('--- test_init() ---')
        test_dict = PremiumDict()
        self.assertIsNotNone(test_dict)

    def test_class_type(self):
        print('--- test_class_type() ---')
        self.assertIsInstance(PremiumDict(), dict)

    def test_instance_type(self):
        print('--- test_instance_type() ---')
        test_dict = PremiumDict()
        self.assertTrue(test_dict.__class__.__name__ == "PremiumDict")

    # def test_update(self):
    #     print('--- test_update() ---')
    #     test_dict = PremiumDict()
    #     test_dict.update([('test', True)])
    #     self.assertDictEqual(test_dict, {'test': True})



    def test_items(self):
        print('--- test_items() ---')
        test_dict = PremiumDict()
        test_dict.update([('test', True), ('pest', False)])
        self.assertEqual(test_dict.items(), {'test': True, 'pest': False}.items())

    def test_item_changed(self):
        print('--- test_item_changed() ---')
        test_dict = PremiumDict()
        test_dict['test'] = False
        test_dict.update([('test', True)])
        self.assertTrue(test_dict.item_changed())

    def test_set_value(self):
        print('--- test_set_value() ---')
        test_dict = PremiumDict()
        test_dict['test'] = True
        self.assertDictEqual(test_dict, {'test': True})

    def test_storing_and_loading_yaml(self):
        print('--- test_storing_and_loading_yaml() ---')
        filename = "test_dict.yaml"
        test_dict_in = PremiumDict(filename)
        test_dict_in['test'] = True
        test_dict_out = PremiumDict(filename)
        self.assertDictEqual(test_dict_in, test_dict_out)

    def test_storing_and_loading_json(self):
        print('--- test_storing_and_loading_json() ---')
        filename = "test_dict.json"
        test_dict_in = PremiumDict(filename)
        test_dict_in['test'] = True
        test_dict_out = PremiumDict(filename)
        self.assertDictEqual(test_dict_in, test_dict_out)

    def test_storing_and_loading_pickle(self):
        print('--- test_storing_and_loading_pickle() ---')
        filename = "test_dict.pickle"
        test_dict_in = PremiumDict(filename)
        test_dict_in['test'] = True
        test_dict_out = PremiumDict(filename)
        self.assertDictEqual(test_dict_in, test_dict_out)

    def test_storing_and_loading_xml(self):
        print('--- test_storing_and_loading_xml() ---')
        filename = "test_dict.xml"
        test_dict_in = PremiumDict(filename)
        test_dict_in['test'] = 'True'   # all is str
        test_dict_out = PremiumDict(filename)
        self.assertDictEqual(test_dict_in, test_dict_out)

    def test_storing_and_loading_csv(self):
        print('--- test_storing_and_loading_csv() ---')
        filename = "test_dict.csv"
        test_dict_in = PremiumDict(filename)
        test_dict_in['test'] = 'True'   # all is str
        test_dict_out = PremiumDict(filename)
        self.assertDictEqual(test_dict_in, test_dict_out)


if __name__ == '__main__':
    unittest.main()

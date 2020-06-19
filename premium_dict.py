# -*- coding: utf-8 -*-
# file: premium_dict.py
# author: mr.markuese
# works for python 2.7 and 3.5+

import yaml
import json
import pickle
import csv
from dicttoxml import dicttoxml
import xmltodict
import os
import stat
import sys
from enum import Enum
from switch import Switch
import string
import logging.handlers

# TODO: Since Iterable has moved from collections to collections.abc, there is a deprecation warning in
#       dicttoxml in Python 3.9 that is used in func _store_as_xml(), this may be fixed soon
# https://github.com/quandyfactory/dicttoxml/pull/73/commits/2b7b4522b7255fbc8f1e04304d2e440d333909d5

# Rotating logger setup
log_level = logging.DEBUG
log_dir = '' # Set to 'YOUR_LOG_DIR'

# Get the fully-qualified logger
logger = logging.getLogger('premium_dict')

# Important: set perminssions to overwrite log files for all users
if log_dir:
    os.chmod(log_dir, stat.S_IRWXG | stat.S_IRWXU | stat.S_IRWXO)
log_filename = 'premium.log'
log_path = log_dir + log_filename
# Let the log files rotate
max_keep_files = 2  # Change here the number of rotation files
max_file_size = 10000  # Change here the max log file size (bytes)
file_handler = logging.handlers.RotatingFileHandler(log_path,
                                                    mode='a',
                                                    maxBytes=max_file_size,
                                                    backupCount=max_keep_files)
# Choose logging format
fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
file_handler.setFormatter(fmt)
# Create root logger and add the custom logger
root_logger = logging.getLogger()
root_logger.addHandler(file_handler)
root_logger.setLevel(log_level)


class Format(Enum):
    ''' A class derived from Enum that contains the file formats for serialization in PremiumDict '''

    YAML = 0
    JSON = 1
    PICKLE = 2
    XML = 3
    CSV = 4


class PremiumDict(dict):
    ''' A class derived from dict that contains additional features, e. g. Serializing '''

    def __init__(self, filename=None, path=None):
        super(PremiumDict, self).__init__
        self.sentinel = list()

        # To initialize a dict with serialization ability a file name is needed
        if filename is not None:
            # First check whether the file name has correct type
            assert isinstance(filename, str), "filename has to be a string"
            input = filename.split('.')
            assert len(input) == 2, "Only one '.' allowed to separate filename and format: {}".format(input)
            (name, format) = input
            allowed = string.ascii_letters + string.digits + '_' + '-'
            not_allowed = set(name) - set(allowed)
            assert len(not_allowed) == 0, "Error filename: characters {} are not allowed".format(not_allowed)
            assert name[:1].isalpha() is True, "Error filename: first character has to be a letter, but is '{}'".format(name[:1])
            self.name = name

            if format == "yaml":
                self.format = Format.YAML
            elif format == "json":
                self.format = Format.JSON
            elif format == "pickle":
                self.format = Format.PICKLE
            elif format == "xml":
                self.format = Format.XML
            elif format == "csv":
                self.format = Format.CSV
            else:
                self.format = Format.YAML
                logger.error("Unsupported file format '{}' given, choose '{}' for now".format(format, self.format.name))
            # Set file path for storing dict
            if path == None:
                # Get path from working dir
                self.path = self.get_filepath()
            else:
                # Or take path from parameter
                self.path = path
            logger.debug("File path: {}.".format(self.path))
            # Load data from file if exists
            data_dict = self.load()
            # Reformat loaded data for input into update()
            tuple_list = list(data_dict.items())
            logger.debug("Init with {}.".format(tuple_list.__repr__()))
            # Initialize PremiumDict instance with previous saved data (if they exist)
            self.update(tuple_list)

    def get_filepath(self):
        dir_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(dir_path, self.name + '.' + self.format.name.lower())
        return file_path

    def __setitem__(self, item, value):
        assert isinstance(self, PremiumDict), logger.exception("Wrong object type - not an instance of PremiumDict")
        logger.debug("sentinel: {}.".format(self.sentinel))
        self.sentinel.append(item)
        logger.debug("sentinel appended item: '{}' and is now: {}.".format(item, self.sentinel))
        logger.debug("Changing value of key '{}' to '{}'!!".format(item, value))
        # Set data
        super(PremiumDict, self).__setitem__(item, value)
        print("__setitem__ self.sentinel: {}".format(self.sentinel))
        # Callback store data
        if hasattr(self, 'name') and hasattr(self, 'path'):
            logger.debug("Saving changes to {}.".format(self.path))
            self.store()

    def __getitem__(self, item):
        logger.debug("sentinel: {}.".format(self.sentinel))
        self.sentinel.remove(item)
        logger.debug("sentinel removed item: '{}' and is now: {}.".format(item, self.sentinel))
        value = super(PremiumDict, self).__getitem__(item)
        logger.debug("Reading data: '{}' for key: '{}'.".format(value, item))
        print("__getitem__ self.sentinel: {}".format(self.sentinel))
        return value

    # Takes a list of tuples, like [('some', 'thing')]
    def update(self, iterable):
        logger.debug("Updating with '{}'.".format(iterable))
        super(PremiumDict, self).update(iterable)
        logger.debug("sentinel: {}.".format(self.sentinel))
        self.sentinel.extend(k for k, v in iterable)
        logger.debug("sentinel extended: {}.".format(self.sentinel))
        print("update self.sentinel: {}".format(self.sentinel))

    def items(self):
        self.sentinel = list()
        logger.debug("Get a list of all items.")
        return super(PremiumDict, self).items()

    def item_changed(self):
        logger.debug("Retrieve data object change state.")
        return bool(self.sentinel), self.sentinel

    def load(self):
        data_dict = {}
        with Switch(self.format.name) as case:
            if case('YAML'):
                data_dict = self._load_yaml()
            if case('JSON'):
                data_dict = self._load_json()
            if case('PICKLE'):
                data_dict = self._load_pickle()
            if case('XML'):
                data_dict = self._load_xml()
            if case('CSV'):
                data_dict = self._load_csv()
            if case.default:
                logger.error("Error, unknown file format: {}.".format(self.format.name))
        return data_dict

    def _load_yaml(self):
        data_dict = {}
        if os.path.exists(self.path):
            # with open(self.path, 'r', newline='') as f:
            with open(self.path, 'r') as f:
                try:
                    data_dict = yaml.load(f, Loader=yaml.Loader)
                except yaml.YAMLError as yaml_excp:
                    logger.exception(yaml_excp)
        else:
            logger.info("File '{}' not exists. Return empty dict().".format(self.path))
        return data_dict

    def _load_json(self):
        data_dict = {}
        if os.path.exists(self.path):
            with open(self.path, 'r') as f:
                data_dict = json.load(f)
        else:
            logger.info("File '{}' not exists. Return empty dict().".format(self.path))
        return data_dict

    def _load_pickle(self):
        data_dict = {}
        if os.path.exists(self.path):
            try:
                with open(self.path, 'rb') as f:
                    data_dict = pickle.load(f)
            except pickle.UnpicklingError as pickle_excp:
                logger.exception(pickle_excp)
        else:
            logger.info("File '{}' not exists. Return empty dict().".format(self.path))
        return data_dict

    def _load_xml(self):
        data_dict = {}
        if os.path.exists(self.path):
            with open(self.path, 'r') as f:
                root = xmltodict.parse(f.read(), dict_constructor=dict)
                data_dict = root['root']
        else:
            logger.info("File '{}' not exists. Return empty dict().".format(self.path))
        return data_dict

    def _load_csv(self):
        data_dict = {}
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r') as f:
                    reader = csv.reader(f)
                    data_dict = dict(reader)
            except csv.Error as e:
                logger.exception(e)
        else:
            logger.info("File '{}' not exists. Return empty dict().".format(self.path))
        return data_dict

    def store(self):
        with Switch(self.format.name) as case:
            if case('YAML'):
                self._store_as_yaml()
            if case('JSON'):
                self._store_as_json()
            if case('PICKLE'):
                self._store_as_pickle()
            if case('XML'):
                self._store_as_xml()
            if case('CSV'):
                self._store_as_csv()
            if case.default:
                logger.info("File '{}' not exists. Return empty dict().".format(self.path))
        logger.debug("Stored {} in {} format at {}".format(dict(zip(self.keys(), self.values())), self.format.name, self.path))

    def _store_as_yaml(self):
        try:
            with open(self.path, 'w') as f:
                yaml.dump(dict(zip(self.keys(), self.values())), f)
        except Exception as e:
            logger.exception("Error writing the {} file: {}".format(self.format.name, e))

    def _store_as_json(self):
        try:
            with open(self.path, 'w') as f:
                json.dump(dict(zip(self.keys(), self.values())), f, sort_keys=True)
        except Exception as e:
            logger.exception("Error writing the {} file: {}".format(self.format.name, e))

    def _store_as_pickle(self):
        try:
            with open(self.path, 'wb') as f:
                try:
                    pickle.dump(dict(zip(self.keys(), self.values())), f)
                except pickle.PicklingError as pickle_excp:
                    logger.exception(pickle_excp)
        except Exception as e:
            logger.exception("Error writing the {} file: {}".format(self.format.name, e))

    def _store_as_xml(self):
        try:
            xml = dicttoxml(dict(zip(self.keys(), self.values())), attr_type=False)
            with open(self.path, 'w+') as f:
                f.write(xml.decode('utf-8'))
        except Exception as e:
            logger.exception("Error writing the {} file: {}".format(self.format.name, e))

    def _store_as_csv(self):
        try:
            with open(self.path, 'w') as f:
                writer = csv.writer(f)
                for key, value in zip(self.keys(), self.values()):
                    writer.writerow([key, value])
        except Exception as e:
            logger.exception("Error writing the {} file: {}".format(self.format.name, e))


# Try this for several formats
if __name__ == '__main__':

    def test_for_formats(format):
        print("------------------------------------")
        print("--- Running example for '{}' ---".format(format.upper()))
        print("------------------------------------")

        filename = 'user_data.' + format

        ## If file exists, delete it ##
        if os.path.isfile(filename):
            os.remove(filename)
        premium_dict = PremiumDict(filename)
        print(premium_dict.__class__.__name__, ": ", premium_dict)

        # Nested example structure
        premium_dict['Users'] = {'safelist': {'member_01': {'multiple_IDs': [11, 12, 13]}, 'member_02': 222},
                                 'blocklist': {'nonmember_01': 123, 'nonmember_02': 234}
                                 }
        # Check if there is a new entry
        print(premium_dict.item_changed())

        # Get the entry
        user_lists = premium_dict['Users']
        print("Users: {}".format(dict(zip(user_lists.keys(), user_lists.values()))))

        print(premium_dict.items())
        print(premium_dict.item_changed())


    # Run tests for every entry in Format
    for format in Format.__members__.keys():
        print("Format: {}".format(format.lower()))
        test_for_formats(format.lower())

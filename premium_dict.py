# -*- coding: utf-8 -*-
import yaml
import json
import pickle
import csv
from dicttoxml import dicttoxml
import xmltodict
import os
from enum import Enum
from switch import Switch
import string
import logging.handlers

# TODO: Since Iterable has moved from collections to collections.abc, there is a deprecation warning in
#       dicttoxml in Python 3.9 that is used in func __store_as_xml__(), this may be fixed soon
# https://github.com/quandyfactory/dicttoxml/pull/73/commits/2b7b4522b7255fbc8f1e04304d2e440d333909d5

# Rotating logger setup
log_level = logging.DEBUG

# Get the fully-qualified logger
logger = logging.getLogger('premium_dict')
log_filename = 'premium.log'
# Let the log files rotate
max_keep_files = 2              # Change here the number of rotation files
max_file_size = 10000           # Change here the max log file size (bytes)
file_handler = logging.handlers.RotatingFileHandler(log_filename,
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
        self.sentinal = list()

        # To initialize a dict with serialization ability a file name is needed
        if filename is not None:
            input = filename.split('.')
            assert len(input) == 2, f"Only one '.' allowed to separate filename and format: {input}"
            (name, format) = input
            # First check whether the file name has been selected correctly
            assert isinstance(name, str), "filename has to be a string"
            assert isinstance(format, str), "format has to be a string"
            allowed = string.ascii_letters + string.digits + '_' + '-'
            not_allowed = set(name) - set(allowed)
            assert len(not_allowed) == 0, f"Error filename: characters {not_allowed} are not allowed"
            assert name[:1].isalpha() is True, f"Error filename: first character has to be a letter, but is '{name[:1]}'"
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
                logger.error(f"Unsupported file format '{format}' given, choose '{self.format.name}' for now")
            # Set file path for storing dict
            if path == None:
                # Get path from working dir
                self.path = self.__get_filepath__()
            else:
                # Or take path from parameter
                self.path = path
            logger.debug(f"File path: {self.path}.")
            # Load data from file if exists
            data_dict = self.load()
            # Reformat loaded data for input into update()
            tuple_list = zip(data_dict.keys(), data_dict.values())
            logger.debug(f"Init with {tuple_list.__repr__()}.")
            # Initialize PremiumDict instance with previous saved data (if they exist)
            self.update(tuple_list)

    def __get_filepath__(self):
        dir_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(dir_path, self.name + '.' + self.format.name.lower())
        return file_path

    def __setitem__(self, item, value):
        assert isinstance(self, PremiumDict), logger.exception(f"Wrong object type - not an instance of PremiumDict")
        logger.debug(f"sentinal: {self.sentinal}.")
        self.sentinal.append(item)
        logger.debug(f"sentinal appended item: '{item}' and is now: {self.sentinal}.")
        logger.debug(f"Changing value of key '{item}' to '{value}'!!")
        # Set data
        super(PremiumDict, self).__setitem__(item, value)
        # Callback store data
        if hasattr(self, 'name') and hasattr(self, 'path'):
            logger.debug(f"Saving changes to {self.path}.")
            self.store()

    def __getitem__(self, item):
        logger.debug(f"sentinal: {self.sentinal}.")
        self.sentinal.remove(item)
        logger.debug(f"sentinal removed item: '{item}' and is now: {self.sentinal}.")
        value = super(PremiumDict, self).__getitem__(item)
        logger.debug(f"Reading data: '{value}' for key: '{item}'.")
        return value

    # Takes a list of tuples, like [('some', 'thing')]
    def update(self, iterable):
        logger.debug(f"Updating with '{iterable}'.")
        super(PremiumDict, self).update(iterable)
        logger.debug(f"Sentinal: {self.sentinal}.")
        self.sentinal.extend(k for k, v in iterable)
        logger.debug(f"Sentinal extended: {self.sentinal}.")

    def items(self):
        self.sentinal = list()
        logger.debug("Get a list of all items.")
        return super(PremiumDict, self).items()

    def item_changed(self):
        logger.debug("Retrieve data object change state.")
        return bool(self.sentinal), self.sentinal

    def load(self):
        data_dict = {}
        with Switch(self.format.name) as case:
            if case('YAML'):
                data_dict = self.__load_yaml__()
            if case('JSON'):
                data_dict = self.__load_json__()
            if case('PICKLE'):
                data_dict = self.__load_pickle__()
            if case('XML'):
                data_dict = self.__load_xml__()
            if case('CSV'):
                data_dict = self.__load_csv__()
            if case.default:
                logger.error(f"Error, unknown file format: {self.format.name}.")
        return data_dict

    def __load_yaml__(self):
        data_dict = {}
        if os.path.exists(self.path):
            with open(self.path, 'r', newline='') as f:
                try:
                    data_dict = yaml.load(f, Loader=yaml.Loader)
                except yaml.YAMLError as yaml_excp:
                    logger.exception(yaml_excp)
        else:
            logger.info(f"File '{self.path}' not exists. Return empty dict().")
        return data_dict

    def __load_json__(self):
        data_dict = {}
        if os.path.exists(self.path):
            with open(self.path, 'r') as f:
                data_dict = json.load(f)
        else:
            logger.info("File '{}' not exists. Return empty dict().".format(self.path))
        return data_dict

    def __load_pickle__(self):
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

    def __load_xml__(self):
        data_dict = {}
        if os.path.exists(self.path):
            with open(self.path, 'r') as f:
                root = xmltodict.parse(f.read(), dict_constructor=dict)
                data_dict = root['root']
        else:
            logger.info("File '{}' not exists. Return empty dict().".format(self.path))
        return data_dict

    def __load_csv__(self):
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
                self.__store_as_yaml__()
            if case('JSON'):
                self.__store_as_json__()
            if case('PICKLE'):
                self.__store_as_pickle__()
            if case('XML'):
                self.__store_as_xml__()
            if case('CSV'):
                self.__store_as_csv__()
            if case.default:
                logger.error("Error, unknown file format: {}.".format(self.format.name))
        logger.debug("Stored {} in {} format at {}".format(dict(zip(self.keys(), self.values())), self.format.name, self.path))

    def __store_as_yaml__(self):
        try:
            with open(self.path, 'w') as f:
                yaml.dump(dict(zip(self.keys(), self.values())), f)
        except Exception as e:
            logger.exception('Error writing the {} file: {}'.format(self.format.name, e))

    def __store_as_json__(self):
        try:
            with open(self.path, 'w') as f:
                json.dump(dict(zip(self.keys(), self.values())), f, sort_keys=True)
        except Exception as e:
            logger.exception('Error writing the {} file: {}'.format(self.format.name, e))

    def __store_as_pickle__(self):
        try:
            with open(self.path, 'wb') as f:
                try:
                    pickle.dump(dict(zip(self.keys(), self.values())), f)
                except pickle.PicklingError as pickle_excp:
                    logger.exception(pickle_excp)
        except Exception as e:
            logger.exception('Error writing the {} file: {}'.format(self.format.name, e))

    def __store_as_xml__(self):
        try:
            xml = dicttoxml(dict(zip(self.keys(), self.values())), attr_type=False)
            with open(self.path, 'w+') as f:
                f.write(xml.decode('utf-8'))
        except Exception as e:
            logger.exception('Error writing the {} file: {}'.format(self.format.name, e))

    def __store_as_csv__(self):
        try:
            with open(self.path, 'w') as f:
                writer = csv.writer(f)
                for key, value in zip(self.keys(), self.values()):
                    #logger.debug(f"Storing key: {key}, value: {value}")
                    writer.writerow([key, value])
        except Exception as e:
            logger.exception('Error writing the {} file: {}'.format(self.format.name, e))


# Try this for several formats
if __name__ == '__main__':

    def test_for_formats(format: str):
        print("_________________________________")
        print(f"--- Running test for '{format.upper()}' ---")
        print("---------------------------------")

        filename = 'user_data.' + format
        premium_dict = PremiumDict(filename)
        print(premium_dict.__class__.__name__, ": ", premium_dict)

        # Nested example structure
        premium_dict['Users'] = {'white_list': {'member_01': {'multiple_IDs': [11, 12, 13]}, 'member_02': 222},
                                 'black_list': {'nonmember_01': 123, 'nonmember_02': 234}}
        # Check if there is a new entry
        print(premium_dict.item_changed())

        # Get the entry
        user_lists = premium_dict['Users']
        print('Users: {}'.format(dict(zip(user_lists.keys(), user_lists.values()))))

        print(premium_dict.items())
        print(premium_dict.item_changed())


    # Run tests for every entry in Format
    for format in Format.__members__.keys():
        test_for_formats(format.lower())











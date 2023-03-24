import json
import os
import re
from unittest import mock

import requests
from jinja2 import BaseLoader, Environment, FileSystemLoader, TemplateNotFound

import shrub_util.core.config as config
import shrub_util.core.file as file
import shrub_util.core.logging as logging
import shrub_util.core.secrets as secrets
import shrub_util.generation.template_renderer as template_renderer


class MockTemplateLoader(BaseLoader):
    def __init__(self, basepath):
        self.basepath = basepath

    def get_source(self, environment, template):
        if self.basepath is None:
            path = template
        else:
            path = os.path.join(self.path, template)

        source = file.file_read_file(__name__, path)

        return source, path, lambda: True

    @staticmethod
    def get_loader(basepath):
        return MockTemplateLoader(basepath)


class MockFileReaderStore:
    def __init__(self):
        self.content = {}

    def set_file(self, key, content):
        self.content[key] = content

    def file_reader(self, context, filename):
        # try to read based on context
        if context in self.content:
            return self.content[context]
        # try to read based on filename
        if filename in self.content:
            return self.content[filename]

        return None

    def file_exists(self, context, filename):
        # try to read based on context
        if context in self.content:
            return True
        # try to read based on filename
        if filename in self.content:
            return True

        return False


class MockResponseMatcher:
    def __init__(self, path_regex, messages):
        self.path_regex = path_regex
        self.path_matcher = re.compile(self.path_regex)
        self.messages = []
        for message in messages:
            if type(message) is str:
                with open(os.path.normpath(message), "r", encoding="utf-8") as fip:
                    content = fip.read()
                    messages.append(json.loads(content))
            else:
                self.messages.append(message)
        self.count = 0

    def incr(self):
        self.count += 1

    def matches(self, url):
        return self.path_matcher.match(url)

    def get_next_message(self):
        return self.messages[list(divmod(self.count, len(self.messages)))[1]]


class MockResponseDefinition:
    """Mock response defintion"""

    def __init__(self, mock_response_config):
        """the configuration is a list of path configuration dictionaries,
        and looks as follows
        [{  "/<path1 regular expression>": [
                { 'path1_response1': {dictionary 1}},
                { 'path1_response2': {dictionary 2}}]
        },{ "/<path2 regular expression>": [
                { 'path2_response1': {dictionary 1}}},
                { 'path2_response2': {dictionary 2}},
                { 'path2_response3': {dictionary 3}}
                { 'path2_response4': '<file reference>'}]
        }]
        """
        self.config = []
        for path_config in mock_response_config:
            for path_regex in path_config:
                self.config.append(
                    MockResponseMatcher(path_regex, path_config[path_regex])
                )

    def get_response_message(self, url):
        message = None
        for state in self.config:
            if state.matches(url):
                message = state.get_next_message()
                state.incr()
                break
        return message


class Context:
    """Test base class"""

    def __init__(self):
        self.test_data_folder = None
        self._original_requests = None
        self._original_file_reader = None
        self._original_file_exists = None
        self._orginal_template_renderer_loader = None
        self.mock_file_reader_store = MockFileReaderStore()
        self.mock_file_reader = self.mock_file_reader_store.file_reader
        self.mock_file_exists = self.mock_file_reader_store.file_exists
        self.mock_response_definition = None
        self.mock_template_renderer_loader = MockTemplateLoader.get_loader

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            logging.get_logger().error(
                f"exiting test context with error : {exc_val}", ex=exc_val
            )
        self.teardown()
        if exc_val is not None:
            raise exc_val

    def set_file(self, name, content):
        self.mock_file_reader_store.set_file(name, content)

    def set_template(self, name, content):
        self.set_file(name, content)

    def set_config_file(self, content):
        self.mock_file_reader_store.set_file(config.__name__, content)

    def set_secrets_file(self, content):
        self.mock_file_reader_store.set_file(secrets.__name__, content)

    def set_rest_api_mocks(self, mock_response_definition):
        """Return mock responses for consecutive calls on
        requests.get,
        requests.posts
        and requests.patch"""
        self.mock_response_definition = MockResponseDefinition(mock_response_definition)

        def wrapper(*args, **kwargs):
            """wrapper for requests.get, requests.post and requests.patch
            This allows for returning a mock value depending on the number
            of times the method is called.
            """
            result = mock.Mock()
            # simplify get result
            # the URL is either the first positional argument or the kwarg named url
            url = None
            if len(args) > 0:
                url = args[0]
            if url is None:
                url = kwargs["url"]
            result.json.return_value = (
                self.mock_response_definition.get_response_message(url)
            )
            return result

        # override, easy mock
        requests.get = wrapper
        requests.post = wrapper
        requests.patch = wrapper

    def setup(self):
        self._original_requests = (requests.get, requests.post, requests.patch)
        self._original_file_reader = file.file_read_file
        self._original_file_exists = file.file_exists
        file.file_read_file = self.mock_file_reader
        file.file_exists = self.mock_file_exists
        self._orginal_template_renderer_loader = template_renderer.get_loader
        template_renderer.get_loader = self.mock_template_renderer_loader

    def teardown(self):
        (requests.get, requests.post, requests.patch) = self._original_requests
        file.file_read_file = self._original_file_reader
        file.file_exists = self._original_file_exists
        template_renderer.get_loader = self._orginal_template_renderer_loader

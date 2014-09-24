# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json


TEST_SEPARATOR = '.'


def make_full_results(metadata, seconds_since_epoch, all_test_names, results):
    """Convert the typ results to the Chromium JSON test result format.

    See http://www.chromium.org/developers/the-json-test-results-format
    """
    full_results = {}
    full_results['interrupted'] = False
    full_results['path_delimiter'] = TEST_SEPARATOR
    full_results['version'] = 3
    full_results['seconds_since_epoch'] = seconds_since_epoch
    for md in metadata:
        key, val = md.split('=', 1)
        full_results[key] = val

    sets_of_passing_test_names = map(_passing_test_names, results)
    sets_of_failing_test_names = map(failed_test_names, results)

    skipped_tests = (set(all_test_names) - sets_of_passing_test_names[0]
                                         - sets_of_failing_test_names[0])

    n_tests = len(all_test_names)
    n_failures = len(sets_of_failing_test_names[-1])
    n_skips = len(skipped_tests)
    n_passes = n_tests - n_failures - n_skips
    full_results['num_failures_by_type'] = {
        'FAIL': n_failures,
        'PASS': n_passes,
        'SKIP': n_skips,
    }

    full_results['tests'] = {}

    for test_name in all_test_names:
        if test_name in skipped_tests:
            value = {
                'expected': 'SKIP',
                'actual': 'SKIP',
            }
        else:
            value = {
                'expected': 'PASS',
                'actual': _actual_results_for_test(test_name,
                                                   sets_of_failing_test_names,
                                                   sets_of_passing_test_names),
            }
            if value['actual'].endswith('FAIL'):
                value['is_unexpected'] = True
        _add_path_to_trie(full_results['tests'], test_name, value)

    return full_results


def make_upload_request(test_results_server, builder, master, testtype,
                        full_results):
    url = 'http://%s/testfile/upload' % test_results_server
    attrs = [('builder', builder),
             ('master', master),
             ('testtype', testtype)]
    content_type, data = _encode_multipart_form_data(attrs, full_results)
    return url, content_type, data


def exit_code_from_full_results(full_results):
    return 1 if num_failures(full_results) else 0


def num_failures(full_results):
    return full_results['num_failures_by_type']['FAIL']


def failed_test_names(result):
    test_names = set()
    for test, _ in result.failures + result.errors:
        assert isinstance(test, str), ('Unexpected test type: %s' %
                                       test.__class__)
        test_names.add(test)
    return test_names


def _passing_test_names(result):
    return set(test for test, _ in result.successes)


def _actual_results_for_test(test_name, sets_of_failing_test_names,
                             sets_of_passing_test_names):
    actuals = []
    for retry_num in range(len(sets_of_failing_test_names)):
        if test_name in sets_of_failing_test_names[retry_num]:
            actuals.append('FAIL')
        elif test_name in sets_of_passing_test_names[retry_num]:
            assert ((retry_num == 0) or
                    (test_name in sets_of_failing_test_names[retry_num - 1])), (
                      'We should not have run a test that did not fail '
                      'on the previous run.')
            actuals.append('PASS')

    assert actuals, 'We did not find any result data for %s.' % test_name
    return ' '.join(actuals)


def _add_path_to_trie(trie, path, value):
    if TEST_SEPARATOR not in path:
        trie[path] = value
        return
    directory, rest = path.split(TEST_SEPARATOR, 1)
    if directory not in trie:
        trie[directory] = {}
    _add_path_to_trie(trie[directory], rest, value)


def _encode_multipart_form_data(attrs, test_results):
    # Cloned from webkitpy/common/net/file_uploader.py
    BOUNDARY = '-M-A-G-I-C---B-O-U-N-D-A-R-Y-'
    CRLF = '\r\n'
    lines = []

    for key, value in attrs:
        lines.append('--' + BOUNDARY)
        lines.append('Content-Disposition: form-data; name="%s"' % key)
        lines.append('')
        lines.append(value)

    lines.append('--' + BOUNDARY)
    lines.append('Content-Disposition: form-data; name="file"; '
                 'filename="full_results.json"')
    lines.append('Content-Type: application/json')
    lines.append('')
    lines.append(json.dumps(test_results))

    lines.append('--' + BOUNDARY + '--')
    lines.append('')
    body = CRLF.join(lines)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

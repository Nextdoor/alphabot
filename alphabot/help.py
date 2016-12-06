from __future__ import print_function

import logging

log = logging.getLogger(__name__)


class Help(object):

    def __init__(self):
        self._func_map = {}

    def update(self, function, usage, tags=None, desc=None):
        if usage and not tags:
            # Default to using 'usage' as the tag.
            tags = [usage]
        existing = self._func_map.get(function, None)
        if function in self._func_map:
            # Update if not set in original.
            existing['usage'] = existing['usage'] or usage
            existing['tags'] = existing['tags'] or tags
            existing['desc'] = existing['desc'] or desc
            self._func_map[function] = existing
        else:
            self._func_map[function] = {
                'usage': usage,
                'tags': tags,
                'desc': desc
            }

    def list(self, filter=None):
        results = []
        if filter:
            for _, help in self._func_map.iteritems():
                for tag in help['tags']:
                    if type(tag) is not str:
                        log.warning('Tag %s is not a str' % tag)
                        continue
                    if filter in tag:
                        results.append((help['usage'], help['desc']))
                        break
        else:
            results = [(help['usage'], help['desc']) for _, help in self._func_map.iteritems()]
        # Sort by 'usage' string.
        return sorted(results, key=lambda x: x[0])

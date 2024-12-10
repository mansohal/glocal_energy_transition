#
# GAMS - General Algebraic Modeling System Python API
#
# Copyright (c) 2017-2024 GAMS Development Corp. <support@gams.com>
# Copyright (c) 2017-2024 GAMS Software GmbH <support@gams.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from cerberus import Validator
from cerberus.platform import Hashable


class ConnectValidator(Validator):

    def __init__(self, *args, **kwargs):
        super(ConnectValidator, self).__init__(*args, **kwargs)

    # Custom validator that does not consider null values when validating excludes rule
    def _validate_excludes(self, excluded_fields, field, value):
        """{'type': ('hashable', 'list'), 'schema': {'type': 'hashable'}}"""
        if isinstance(excluded_fields, Hashable):
            excluded_fields = [excluded_fields]

        # get all fields from excluded_fields which values are not None
        not_none_fields = [
            ef
            for ef in excluded_fields
            # if self.document.get(ef) != self.schema[ef]["default"]
            if self.document.get(ef) is not None
        ]
        # if value == self.schema[field]["default"]:
        if value is None:  # None value is considered to be the same as missing
            if (
                not_none_fields
            ):  # if all other fields are None or missing as well, we can skip validation
                return

        # if not_none_fields has values, then we want to get the default behavior for those fields only
        super()._validate_excludes(not_none_fields, field, value)

    def normalize_of_rules(self, document):
        """
        Perform normalization of 'anyof' and 'oneof' on the first
        level of the document only. The implementation looks for 'anyof' and 'oneof'
        in the schema and finds the first sub schema that matches. This needs to be
        considered especially for 'anyof' since multiple sub schemas are allowed to
        match. The determined sub schema will be used to perform the normalization.
        :param document: the document to be normalized
        :return: the normalized document
        """

        document_copy = dict(document)
        for k, v in self.schema.items():
            if document[k] is not None:
                is_list = v.get("type") == "list"
                of_rule = v
                if is_list:
                    of_rule = of_rule.get("schema", {})
                of_rule = of_rule.get("anyof", of_rule.get("oneof"))
                if of_rule is not None:
                    document_copy[k] = []
                    if is_list:
                        doc_list = [{k: x} for x in document[k]]
                    else:
                        doc_list = [{k: document[k]}]
                    for sub_doc in doc_list:
                        for sub_schema in of_rule:
                            new_schema = {k: sub_schema}
                            v = ConnectValidator(new_schema)
                            sub_doc_normalized = v.validated(sub_doc)
                            if sub_doc_normalized is not None:
                                if is_list:
                                    document_copy[k].append(sub_doc_normalized[k])
                                else:
                                    document_copy[k] = sub_doc_normalized[k]
        return document_copy

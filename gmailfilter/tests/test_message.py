

from testtools import TestCase

from gmailfilter._message import parse_list_id


class ListIdParsingTestCase(TestCase):

    def test_list_id_equality_as_string(self):
        l = parse_list_id('mail.asana.com')
        self.assertEqual('mail.asana.com', str(l))
        self.assertEqual('mail.asana.com', l)

    def test_list_id_inequality_as_string(self):
        l = parse_list_id('mail.asana.com')
        self.assertNotEqual('foo.com', str(l))
        self.assertNotEqual('foo.com', l)

    def test_can_extract_list_id_from_description(self):
        l = parse_list_id('Some list description <some.list.id>')
        self.assertEqual('some.list.id', l)

    def test_list_ids_with_different_descriptions_are_equal(self):
        self.assertEqual(
            parse_list_id('some description <list.id>'),
            parse_list_id('some other description <list.id>'),
            )

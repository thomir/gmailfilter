from unittest import TestCase


from gmailfilter import _connection as c

class SequenceChunkTests(TestCase):

    def assertSequenceChunk(self, messages, chunk_size, expected):
        observed = list(c.sequence_chunk(messages, chunk_size))
        self.assertEqual(expected, observed)

    def test_no_messages(self):
        self.assertSequenceChunk(0, 10, [])

    def test_single_message(self):
        self.assertSequenceChunk(1, 10, ['1'])

    def test_two_messages(self):
        self.assertSequenceChunk(2, 10, ['1:*'])

    def test_one_chunk(self):
        self.assertSequenceChunk(10, 10, ['1:*'])

    def test_one_and_a_bit_chunks(self):
        self.assertSequenceChunk(11, 10, ['1:10', '11'])

    def test_two_chunks(self):
        self.assertSequenceChunk(20, 10, ['1:10', '11:*'])

    def test_with_no_chunking(self):
        self.assertSequenceChunk(5, 1, ['1', '2', '3', '4', '5'])



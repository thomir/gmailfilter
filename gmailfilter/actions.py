
import imapclient
import logging

"""Classes that manipulate mails."""


class Action(object):
    """
    All actions must implement this interface (though they need not inherit
    from this class).

    """

    def process(self, client_conn, message):
        """Run the action.

        'client_conn' will be an IMAPClient.IMAPClient object, possibly with
        access to dangerous methods removed (TODO: Document this interface
        explicitly).

        'message' will be a message interface object.

        If this method raises any exceptions, action processing will stop, and
        an error will be logged (TODO: Actually do that somewhere).

        """


class Move(Action):

    def __init__(self, target_folder):
        self._target_folder = target_folder

    def process(self, conn, message):
        try:
            conn.copy(message.uid(), self._target_folder)
        except imapclient.IMAPClient.Error:
            status = conn.create_folder(self._target_folder)
            assert status.lower() == b"success", \
                "Unable to create folder %s" % self._target_folder
            conn.copy(message.uid(), self._target_folder)

        # TODO: Maybe provide logging facilities in parent 'Action' class?
        conn.delete_messages(message.uid())
        logging.info(
            "Moving message %r to %s" % (message, self._target_folder))


class DeleteMessage(Action):

    def process(self, conn, message):
        conn.delete_messages(message.uid())
        logging.info("Deleting message %r" % message)


class LogMessage(Action):

    """A Simple action that just logs the message."""

    def __init__(self, message_template="LOG Message={}"):
        """Create a new LogMessage object.

        The message_template string must be a string with a single '{}' in it,
        which will be replaced with the message's repr().

        """
        self.message_template = message_template

    def process(self, conn, message):
        logging.info(self.message_template.format(repr(message)))


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
        # TODO: optimise this by trying the copy, and if we get 'NO' with
        # 'TRYCREATE' then, and only then try and create the folder. Removes the
        # overhead of the existance check for every message,
        if not conn.folder_exists(self._target_folder):
            status = conn.create_folder(self._target_folder)

            assert status.lower() == "success", "Unable to create folder %s" % self._target_folder

        conn.copy(message.uid(), self._target_folder)
        # TODO: Maybe provide logging facilities in parent 'Action' class?
        conn.delete_messages(message.uid())
        logging.info("Moving message %r to %s" % (message, self._target_folder))


class DeleteMessage(Action):

    def process(self, conn, message):
        conn.delete_messages(message.uid())
        logging.info("Deleting message %r" % message)

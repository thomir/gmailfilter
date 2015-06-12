

"""Classes that manipulate mails."""


class Action(object):
    """
    All actions must implement this interface (though they need not inherit
    from this class).

    """

    def process(self, client_conn, message_uid):
        """Run the action.

        'client_conn' will be an IMAPClient.IMAPClient object, possibly with
        access to dangerous methods removed (TODO: Document this interface
        explicitly).

        'message_uid' will be the message uid, as a string.

        If this method raises any exceptions, action processing will stop, and
        an error will be logged (TODO: Actually do that somewhere).

        """


class Move(Action):

    def __init__(self, target_folder):
        self._target_folder = target_folder

    def process(self, conn, uid):
        # TODO: optimise this by trying the copy, and if we get 'NO' with
        # 'TRYCREATE' then, and only then try and create the folder. Removes the
        # overhead of the existance check for every message,
        if not conn.folder_exists(self._target_folder):
            status = conn.create_folder(self._target_folder)

            assert status.lower() == "success", "Unable to create folder %s" % self._target_folder

        conn.copy(uid, self._target_folder)
        # TODO: Maybe provide logging facilities in parent 'Action' class?
        # logging.info("Deleting %s" % uid)
        conn.delete_messages(uid)

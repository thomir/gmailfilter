= What is this? =

This is the source code to my personal IMAP-based mail filtering tool. I use it every day, and it has proven to be useful for me. You are more than welcome to use and contribute to it.

= How does it work? =

You must create a `rules` configuration file which tells `gmailfilter` how to connect to your IMAP mail server, and what to do with all the mail in your inbox. The approach `gmailfilter` takes to mail filtering is that your inbox should be virtually empty at the end of a filter run - only messages which need "active processing" should remain (usually this means "unread and flagged (starred) messages"). `gmailfilter` takes care of iterating over the messages in your inbox, and will run your rules over any new messages that arrive. 

You can use `gmailfilter` to achieve the following:

 * Automatically move mailing list messages to a separate folder.
 * Automatically delete spam messages from automated services such as jenkins.
 * Move messages that are older than a certain age to a different folder.
 * ...much much more!

 Rules are written in python, so you can do pretty much whatever you want!
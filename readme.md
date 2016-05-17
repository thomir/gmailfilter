[![Build Status](https://travis-ci.org/thomir/gmailfilter.svg?branch=master)](https://travis-ci.org/thomir/gmailfilter)

# What is this?

This is the source code to my personal IMAP-based mail filtering tool. I use it every day, and it has proven to be useful for me. You are more than welcome to use and contribute to it.

# How does it work?

You must create a `rules` configuration file which tells `gmailfilter` how to connect to your IMAP mail server, and what to do with all the mail in your inbox. The approach `gmailfilter` takes to mail filtering is that your inbox should be virtually empty at the end of a filter run - only messages which need "active processing" should remain (usually this means "unread and flagged (starred) messages"). `gmailfilter` takes care of iterating over the messages in your inbox, and will run your rules over any new messages that arrive. 

You can use `gmailfilter` to achieve the following:

 * Automatically move mailing list messages to a separate folder.
 * Automatically delete spam messages from automated services such as jenkins.
 * Move messages that are older than a certain age to a different folder.
 * ...much much more!

 Rules are written in python, so you can do pretty much whatever you want!


 ## Architecture Notes:

These are not intended to be comprehensive - rather a rough brain dump of my intentions.

The user facing side of gmailfilter is simple: a single file in ~/.config/gmailfilter/ named 'rules' or 'rules.py' that specifies:
 * User credentials to connect to their imap server.
 * A table of filtering rules.

The filtering rules are processed in order: rules at the top of the table will be run before rules lower in the table. Each rule contains two parts:

 1. A test that will be run against each email, and may or may not match. For example: Subject contains 'foo'.
 2. One or more actions to be executed when the test portion of the rule matches.

 More information on tests and actions are listed below:

 ### Tests:

The important criteria for designing the test API is that:

 * Tests are easy to read & understand by the user. While we're asking users to program, we should make it as easy as possible.
 * Tests are easy to extend. I almost certainly won't be able to write every required test, so I'll let users write their own, and maybe even contribute them back to the project.
 * Complex tests can be made from several simple tests using boolean operations (which are themselves tests).

A simple test might look like: `SubjectContains("foo")` or `MessageOlderThan("10 days")` or even `HeaderPresent("X-List-Info")`.
Complex Tests can be made up of simple tests, like so: `And(From("someone@somewhere.com"), SubjectContains("Hello"))` - this example test would match only when the sender of the message was 'someone@somewhere.com' *and* the message subject contained the string 'Hello'.


### Actions:

Actions define what to do when we found a message that matches our tests. The criteria for the actions API is identical to that for the messages API.

Simple Rules look like: `Delete()`, `MoveToFolder("Archive/Old Messages")`, `MarkAsRead()`.

Like tests, more than one action can be specified, but unlike tests, no boolean logic can be applied. Instead, we simply list the actions we want in a sequence: `(MarkAsRead(), MoveToFolder("Foo"))` is an action sequence that would mark the message as read, and then move the message to the specified folder.

### Rules:

Rules could simply be a 2-tuple of Test, Action, which would make them look like this:

(SubjectContains("Foo"), Delete())

-or-

(MessageOlderThan("10 days"), (MarkAsRead(), MoveToFolder("Archive")))

-or-

(Or(SubjectContains("Code Import"), MessageOlderThan("10 days")), Delete())


Rules are simply a list of these 2-tuples:

[
	(SubjectContains("Foo"), Delete()),
	(MessageOlderThan("10 days"), (MarkAsRead(), MoveToFolder("Archive"))),
	(Or(SubjectContains("Code Import"), MessageOlderThan("10 days")), Delete()),
]


For each message, processing stops when the first test portion of the first rule matches. For this reason in the above example, messages that are older than 10 days old will match the second rule, and the third rule will never be tested.


## Implementation Notes: Tests

While the API design listed above is reasonably simple for users, there's a problem: gmailfilter is designed to be a long-running process, and I want to avoid repeatedly scanning the users inbox (this is slow, and uses a fair amount of bandwidth). When gmailfilter starts, we do a complete inbox scan, applying the rules to each message. Once the initial scan is compete, we put our imap connection into 'idle mode', and get notifications from the server of any new messages that arrive.

This design should suffice for 90% of the time. The problem arises when the user is using tests which are dependant on things other than the message itself. For example: `MessageOlderThan("10 days")` may not match a given message on the first folder scan, but might match 30 minutes later. 

The idea I have for solving this is that each test may return a 'retest hint' object to gmailfilter. The retest hint object tells gmailfilter when it should try the test again. For example, if a message is 8 days old, and the rule is `MessageOlderThan("10 days")` the test object would  return a hint that the message should be tested again in 2 days time.

There are problems with this approach:

1) These hints need to be stored somewhere. If we store them in memory, will we possibly use too much?
2) Any time we successfully process a message, we need to find the corresponding retest hint (if any) and delete it.
3) Similarly, any time a message is deleted from the inbox we need to find the corresponding retest hint (if any) and delete it
4) We need to constrain the user from creating tests that would require frequent re-tests. testing for message age in days is a good example, allowing 'minutes' or 'seconds' is probably not going to work that well.

In any case, we should re-scan the inbox periodically anyway.


## Implementation notes: Metadata retrieval

One issue with the imap protocol is that you need to decide what bits of the message you want to retrieve. Retrieving just the message id is cheap, retrieving the envelope is more expensive, etc. etc. Ideally, we'd retrieve only the parts of the message that are required to match it to a rule, and we'd know which parts those are from the start. I have several ideas here:

1) Just do the simple thing - fetch the message uid and the envelope, then lazily fetch anything else the tests need.

2) Parse all the tests in the users rules.py file, and have Test objects declare which parts of the message they're interested in, so that when we actually fetch the message we know which bits to get.

3) When we run through all the rules, record which bits of the message we retrieve, and save that information in a .cache file. Subsequent runs can use this information to optimise the fetching process.

Then again, maybe the simple solution is the best one.


# Other ideas:

 - watch rules file for changes, re-scan inbox when we see that the rule file has changed.

 - Do we support filtering on more than one imap account? What about more than one folder? If so, how?

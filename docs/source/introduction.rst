Introduction
############

What is this, and who is it for?
================================

`gmailfilter` is a tool to help you manage high volumes of email. It is especially useful for developers, or anyone who gets a large number of automated email messages from services such as github or launchpad. Filtering messages outside of any particular email client allows you to change clients without having to move your filter rules.

`gmailfilter` expresses filte rules in Python, so this tool is aimed primarily at developers. Using python to express the filter rules allows us a huge amount of power to filter email in a large variety of different senarios. It also means that users are not locked into the specific tests and actions (more on those later) that `gmailfilter` provides - they can write their own, and even contribute those back to the `gmailfilter` project.
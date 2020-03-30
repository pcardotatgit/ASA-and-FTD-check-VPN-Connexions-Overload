# ASA-and-FTD-check-VPN-Connexions-Overload

## Introduction

This project is a proof of concept.

This is an example of how to browse a list which contains ASA and FTD Device IP addresses and admin credential, and for each device in the list, the tool collects the result of a **show vpn-sessiondb**, extracts Key VPN indicators and store them into a SQLite Database.

If on one device in the list the VPN Load exceeds 70%, then an alert is sent on a Monitored Webex Team Room
If on one device in the list the average VPN Load exceeds every day for more thant 10%, during 5 days, then an alert is sent on a Monitored Webex Team Room

## CODE IS UNDER DEVELOPMENT

The code is going to come very soon

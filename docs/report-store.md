# report-store

A web app used for ingesting, searching, and displaying test reports.

## Local environment

* Create a virtualenv, install base (`requirements.txt`) and dev (`requirements-dev.txt`) dependencies.

* Start Mongo server:

        make mongo-server

    To connect to it via Mongo shell, run:

        make mongo-client

* Start the web server:

Will run the flask app and will serve the prebuilt UI from the
`compiled-ui` directory. 

        make run

* Work on the UI

For working on the UI you want to start the Flask dev server and the UI dev server.
Using the UI dev server enables automatic reload of the source code.
The node dev server that serves the UI is configured via `package.json/proxy` option to 
forward backend calls to the Flask server. So you will need to start both the node dev server
and the Flask dev server. This can be achieved with: 

        make dev-ui

## Publish a new version of the UI

When you are done modifying your UI you can publish a new version by running

        make update-ui

This will remove the old `/compiled-ui` directory, will build the new UI and will copy it
in a new `/compiled-ui` directory.

**NOTE:** It is strongly recommended to create a new commit containing only the changes from a 
`make update-ui` there will be a lot of files removed and created in this commit that need no review
so do **NOT** mix it with normal PRs and commits.

The recommended procedure is:

* Change the UI and potentially  on a branch, create a PR with your changes leaving the old 
compiled-ui directory as is.   
* Merge the PR in main
* On main or on a separate branch run `make update-ui` and commit and push the changes without any 
other modification (these changes will need no review).
* If changes were made on a branch merge it into main


## Load test data

Run this command to upload some test data:

    python load_data.py

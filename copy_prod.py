"""
This script copies production data into the local mongo db instance
It copies the production data using the report-store endpoint

In order to access the report-store endpoint you need to proxy into it

     kubectl port-forward service/report-store 5000:80

after that you can get the two collections by calling the /api/reports endpoint
specifying type=regular or type=sdk

localhost:5800/api/reports?type=regular
localhost:5800/api/reports?type=sdk

This will return a list of documents that can be inserted in the local mongodb

"""



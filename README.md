# Personal finances

Fetch personal finance data from Google Sheets and generate a set of summary HTML
reports.

## Getting started

Setup NPM:
```
$ wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
...
$ npm install 20
...
$ npm install
...
```

Setup environment:
```
$ make install
$ make test
```

Fetch data from spreadsheets, eg:
```
$ make fetch-all
$ make fetch-latest
```

Run a server to view the HTML:
```
$ make serve
```

Read all pickled data and generate the HTML report:
```
$ python main.py
```

## Google sheets API access

Access data held in Google Sheets using the ``gspread`` Python package.

Setup API access using these instructions for OAuth2:

https://docs.gspread.org/en/latest/oauth2.html#enable-api-access-for-a-project

Or as a service user (sidesteps issues with expiring keys and making the app
public):

https://docs.gspread.org/en/latest/oauth2.html#for-bots-using-service-account

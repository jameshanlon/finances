# Personal finances

Fetch personal finance data from Google Sheets and generate a set of summary HTML
reports.

## Getting started

Setup Python:
```
$ python -m venv env
$ source env/bin/activate
$ pip install -r requirements.txt
...
$ pre-commit install
```

Setup NPM:
```
$ wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
$ nvm install 20
$ npm install
```

Webpack:
```
$ nvm use 20
$ npm run build
```

Fetch data from spreadsheets (individually to avoid rate limiting), eg:
```
$ python main.py --fetch 2024
```

Read all pickled data and generate the HTML report:
```
$ python main.py
```

Run a server to view the HTML:
```
$ python -m http.server 12345
```

## Google sheets API access

Access data held in Google Sheets using the ``gspread`` Python package.

Setup API access using these instructions for OAuth2:

https://docs.gspread.org/en/latest/oauth2.html#enable-api-access-for-a-project

Or as a service user (sidesteps issues with expiring keys and making the app
public):

https://docs.gspread.org/en/latest/oauth2.html#for-bots-using-service-account

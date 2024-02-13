# finances

Steps to get going:

Setup Python
```
$ python -m venv env
$ source env/bin/activate
$ pip install -r requirements.txt
...
$ pre-commit install
```
Setup NPM
```
$ wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
$ nvm install 20
$ npm install
```

Access data held in Google Sheets using gspread Python package.

Setup API access using these instructions for OAuth2:

https://docs.gspread.org/en/latest/oauth2.html#enable-api-access-for-a-project

Or as a service user (sidesteps issues with expiring keys and making the app
public):

https://docs.gspread.org/en/latest/oauth2.html#for-bots-using-service-account

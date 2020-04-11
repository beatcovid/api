# beatcovid19 now API


## Deployment Steps

Migrate outstanding migrations:

```sh
$ python manage.py migrate
```

Load countries fixture:

```sh
$ python manage.py update_countries_plus
```

Load languages fixture

```sh
$ python manage.py loaddata languages_data.json.gz
```

 

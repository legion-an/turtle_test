# Turtle test application

## Setup & Run

The first thing to do is to clone the repository:

```sh
$ git clone https://github.com/legion-an/turtle_test
$ cd turtle_test
```

### Define your Github access_token:
You can define token in file `configs/dev.env`

OR

You create file `turtle_test/settings_local.py` which will not be added in git repository

```sh
GITHUB_ACCESS_TOKEN=YOUR_TOKEN_HERE
```


### Start
Use docker to launch application
```sh
docker-compose up
```

### Swagger
You can use swagger to check API endpoints
```
localhost:8000/swagger/
```

### API
There is only 1 endpoint now.

URL
```
GET /authors/
```

QUERY PARAMS:
```yaml
repository: string  # name of repository on github
owner: string # username of owner of this repository
author: string  # Optional, username of author of a commit
since: string # Optional, ex. 2020-04-20
until: string # Optional, ex. 2020-05-30
```

RESPONSE schema:
```yaml
authors: [
  {
    id: int, # author id
    commits: {  # dictionary of commits
      `date_of_commit`: [ # date of a group of commits with list of detailed information for each commit
        {
          sha: string
          data: {
            message: string # comment for this comment
            url: string # url to this comment on github          
          }   
        },
        ...
      ],
      ...
    },
    username: string, # unique name of this user
    email: string 
  },
  ...
],
dates: [] # sorted dates of existing commits
```


RESPONSE example:
```yaml
"authors": [
    {
      "id": 1,  # author id
      "commits": {  # object of commits, dates as keys and list of commits as values     
        "2019-07-03": [
          {
            "sha": "873860dcb86898564a69428c9f73fa6e4f7472f4",
            "data": {
              "message": "Merge pull request #2 from EugeneKovalev/feature/EXT-1\n\nfeature/EXT-1",
              "url": "https://api.github.com/repos/legion-an/django-models-logging/commits/873860dcb86898564a69428c9f73fa6e4f7472f4"
            }
          }
        ]
      },
      "username": "legion-an",
      "email": "legion.andrey.89@gmail.com"
    },
    ...
] # list of authors with commits for each of them
"dates": [
    ...
    "2019-02-28",
    "2019-05-16",
    "2019-07-03"
    ...
] # sorted dates of existing commits
```


### Tests
To launch tests use this command
```sh
docker-compose exec api python manage.py test
```

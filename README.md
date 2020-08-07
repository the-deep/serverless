# deep-util-services ![CI](https://github.com/the-deep/deep-util-services/workflows/CI/badge.svg)
Services for DEEP Utilities that run in serverless framework.

## Project structure
```
.
├── package.json
├── package-lock.json
├── README.md
├── requirements.txt
├── scripts
│   └── <helper script>
├── secrets
│   └── <stage>.json
├── serverless.yml
└── src
    ├── authorizer
    ├── common
    │   └── <shared code>
    ├── functions
    │   └── <function1>
```

## Requirements Install
```bash
# Install serverless dependencies
yarn install

# Install python requirements
mkdir .python-venv
./scripts/requirements-install.sh
```

## Envionment configuration
The configuration are stored in `secrets` directory. Copy `secrets/sample.json` to `secrets/<stage>.json` and provide the required value.


## Offline
```
# Start local lambda server
# TODO: hot reload not working
PYTHONPATH=.python-venv npx sls offline


# Unit tests
PYTHONPATH=.python-venv pytest **/*test.py
```

## Deploying
Add AWS account to your ~/.aws/credentials
```
[deep-serverless]
region = us-east-1
aws_access_key_id = XXXXXXXXXXXXXXXXXXXX
aws_secret_access_key = XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

For deploying local stage
```
AWS_PROFILE=deep-serverless npx sls deploy --stage local
```

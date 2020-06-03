# deep-util-services
Services for DEEP Utilities that run in serverless framework.


## Usage
Each lambda service is stored in it's corresponding directory along with a `lambda_config.json`. Sample file:
```
# lambda_config.json

{
    "function_name": "webInfoExtract",
    "function_file": "main.py",
    "requirements": [
        "readability-lxml==0.7",
        "requests==2.21.0",
        "beautifulsoup4==4.7.1",
        "tldextract==2.2.0",
        "PyJWT==1.7.1"
    ],
    "project_root": "/home/bibek/projects/togglecorp/thedeep/deeper/server",
    "requirements_file": null,
    "extra_modules": [
        "utils"
    ]
}
```
The following are the parameters:
- **function_name**: The function name in aws.
- **function_file**: The main function file that is located inside the service directory. In this case it's `main.py` inside `web_info_extract`.
- **requirements**: Requirements for the function
- **project_root**: Absolute path of the deep server root. This is used to extract some of the internal modules. [This needs to be more configuruable though.]
- **requirements_file**: Path to requirements file if any. Use this if you don't want to use **requirements** config.
- **extra_modules**: Modules within deep to include. The modules are appended with `project_root`. Nested modules are '/' separated. for example: `utils/web_info_extract` if you just want `web_info_extract` module.


## Building Zip
The bundling of lambda function code into zip is done by `prepare_lambda_zip.py` script. 

`python prepare_lambda_zip.py <service directory>`  
For example in this case: `python prepare_lambda_zip.py web_info_extract`.

This creates a function.zip file inside the service directory which can then be pushed to lambda.

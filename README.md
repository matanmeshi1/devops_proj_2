# devops_proj_2
This project is a demonstration on how to wrk with s3 using boto3
- It demonstrates how to create and delete buckets
- How to Upload, copy, and delete files
- How to change bucket configuration

## Local run
1. Create an IAM user with AmazonS3FullAccess policy and programatic access
2. Configure credentials on your local machine in ~/.aws/credentials
```
[default]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
```
3. Install Python 3.4 or later
4. install project dependencies
```
pip install -r requirements.txt
```
5. run
```
python3 __main__.py
```

import boto3
import uuid


def create_bucket_name(bucket_prefix):
    """
    generate a bucket name
    :param bucket_prefix: the prefix for the bucket name
    :return: a random bucket name
    """
    return ''.join([bucket_prefix, str(uuid.uuid4())])


def create_bucket(bucket_prefix, s3_connection):
    """
    :author @matan-meshi
    :param bucket_prefix: bucket name prefix
    :param s3_connection: s3_client or s3_resource
    :return: bucket_name:the name of the generated bucket
    :return: bucket_response:boto3 response for creating the bucket
    """
    session = boto3.session.Session()
    current_region = session.region_name
    bucket_name = create_bucket_name(bucket_prefix)
    bucket_response = s3_connection.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={
            'LocationConstraint': current_region})
    print(bucket_name, current_region)
    return bucket_name, bucket_response


def create_temp_file(size, file_name, file_content):
    """
    create a temporary file in working dir
    :param size: number of times content is duplicated
    :param file_name: file name
    :param file_content: file content
    :return: file name
    """
    random_file_name = ''.join([str(uuid.uuid4().hex[:6]), file_name])
    with open(random_file_name, 'w') as f:
        f.write(str(file_content) * size)
    return random_file_name


def copy_to_bucket(bucket_from_name, bucket_to_name, file_name):
    """
    copy a file from source bucket to a destination bucket
    :param bucket_from_name: source bucket
    :param bucket_to_name: destination bucket
    :param file_name: file to copy
    :return: true if success, false if not
    """
    copy_source = {
        'Bucket': bucket_from_name,
        'Key': file_name
    }
    try:
        s3_resource.Object(bucket_to_name, file_name).copy(copy_source)
        return True
    except Exception as ex:
        print('unable to copy file {} error {}'.format(file_name, ex))
        return False


def enable_bucket_versioning(bucket_name):
    """
    enable versioning for an existing bucket
    :param bucket_name: bucket to enable versioning for
    :return: true if success, false if not
    """
    try:
        bkt_versioning = s3_resource.BucketVersioning(bucket_name)
        bkt_versioning.enable()
        print(bkt_versioning.status)
        return True
    except Exception as ex:
        print('unable to enable versioning bucket {} error {}'.format(bucket_name, ex))
        return False


def delete_all_objects(bucket_name):
    """
    clears all objects from a bucket
    :param bucket_name: name of a bucket to clear
    :return: None
    """
    res = []
    bucket = s3_resource.Bucket(bucket_name)
    for obj_version in bucket.object_versions.all():
        res.append({'Key': obj_version.object_key,
                    'VersionId': obj_version.id})
    print(res)
    bucket.delete_objects(Delete={'Objects': res})


if __name__ == '__main__':
    s3_client = boto3.client('s3')
    s3_resource = boto3.resource('s3')
    try:
        # Creating buckets
        first_bucket_name, first_response = create_bucket(
            bucket_prefix='firstpythonbucket',
            s3_connection=s3_resource.meta.client)
        print('bucket 1 name is: {}'.format(first_bucket_name))
        print('bucket 1 response is: {}'.format(first_response))

        second_bucket_name, second_response = create_bucket(
            bucket_prefix='secondpythonbucket',
            s3_connection=s3_resource)
        print('bucket 2 name is: {}'.format(second_bucket_name))
        print('bucket 2 response is: {}'.format(second_response))

        # Upload a file
        first_file_name = create_temp_file(300, 'firstfile.txt', 'f')
        first_object = s3_resource.Object(
            bucket_name=first_bucket_name, key=first_file_name)
        first_object.upload_file(first_file_name)

        # Download a file
        first_object.download_file(f'/tmp/{first_file_name}')

        # Copy file between buckets
        copy_to_bucket(first_bucket_name, second_bucket_name, first_file_name)

        # Delete file from second bucket
        s3_resource.Object(second_bucket_name, first_file_name).delete()

        # Upload a public file
        second_file_name = create_temp_file(400, 'secondfile.txt', 's')
        second_object = s3_resource.Object(first_bucket_name, second_file_name)
        second_object.upload_file(second_file_name, ExtraArgs={
            'ACL': 'public-read'})
        second_object_acl = second_object.Acl()
        print('second file grants: {}'.format(second_object_acl.grants))

        # Upload an encrypted file
        third_file_name = create_temp_file(300, 'thirdfile.txt', 't')
        third_object = s3_resource.Object(first_bucket_name, third_file_name)
        third_object.upload_file(third_file_name, ExtraArgs={
            'ServerSideEncryption': 'AES256'})
        print('third file encryption type: {}'.format(third_object.server_side_encryption))

        # Upload an encrypted file - 'STANDARD_IA'
        third_object.upload_file(third_file_name, ExtraArgs={
            'ServerSideEncryption': 'AES256',
            'StorageClass': 'STANDARD_IA'})
        third_object.reload()
        print('third file new storage class: {}'.format(third_object.storage_class))

        # Versioning
        enable_bucket_versioning(first_bucket_name)
        s3_resource.Object(first_bucket_name, first_file_name).upload_file(
            first_file_name)
        s3_resource.Object(first_bucket_name, first_file_name).upload_file(
            third_file_name)
        s3_resource.Object(first_bucket_name, second_file_name).upload_file(
            second_file_name)
        print('current version ID: {}'.format(s3_resource.Object(first_bucket_name, first_file_name).version_id))

        # Bucket Traversal
        for bucket in s3_resource.buckets.all():
            print(bucket.name)
        for bucket_dict in s3_resource.meta.client.list_buckets().get('Buckets'):
            print(bucket_dict['Name'])

        # Object Traversal
        first_bucket = s3_resource.Bucket(name=first_bucket_name)
        for obj in first_bucket.objects.all():
            subsrc = obj.Object()
            print(obj.key, obj.storage_class, obj.last_modified, subsrc.version_id, subsrc.metadata)

        # Delete versioned objects
        delete_all_objects(first_bucket_name)

        # Delete non-versioned objects
        s3_resource.Object(second_bucket_name, first_file_name).upload_file(first_file_name)
        delete_all_objects(second_bucket_name)

        # Delete all buckets
        s3_resource.Bucket(first_bucket_name).delete()
        s3_resource.Bucket(second_bucket_name).delete()
    except Exception as ex:
        print('unable to complete. error {}'.format(ex))
    finally:
        s3_client.close()



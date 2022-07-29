# Copyright (c) 2022 SUSE LLC
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, contact SUSE LLC.
#
# To contact SUSE about this file by physical or electronic mail,
# you may find current contact information at www.suse.com

import boto3
import json
import os


aws_s3_bucket = None
aws_s3_bucket_region = None
aws_s3_bucket_name = None
aws_session = None
aws_s3_service = None


def get_environ_or_bust(key_name):
    assert key_name in os.environ, 'Environment variable %s is required.' % (
        key_name)
    return os.environ.get(key_name)


def get_aws_session():
    global aws_session

    if aws_session is None:
        aws_session = boto3.Session(
            aws_access_key_id=get_environ_or_bust('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=get_environ_or_bust('AWS_SECRET_ACCESS_KEY'))
    return aws_session


def get_aws_s3_service():
    global aws_s3_service

    if aws_s3_service is None:
        aws_s3_service = get_aws_session().resource('s3')
    return aws_s3_service


def get_aws_s3_bucket_name():
    global aws_s3_bucket_name

    if aws_s3_bucket_name is None:
        aws_s3_bucket_name = os.environ.get('AWS_S3_BUCKET_NAME',
                                            'pint-ng-overflow')
    return aws_s3_bucket_name


def get_aws_s3_bucket_region():
    global aws_s3_bucket_region

    if aws_s3_bucket_region is None:
        aws_s3_bucket_region = get_aws_session().client(
            's3').get_bucket_location(
                Bucket=get_aws_s3_bucket_name())['LocationConstraint']
    return aws_s3_bucket_region


def get_aws_s3_bucket():
    global aws_s3_bucket

    if aws_s3_bucket is None:
        aws_s3_bucket = get_aws_s3_service.Bucket(get_aws_s3_bucket_name())
    return aws_s3_bucket


def store_file_to_bucket(filename, content):
    # TODO(gyee): may need to optimize this a bit by storing the file
    # checksum along with the file into the S3 bucket. We can than compare
    # the checksums and overwrite only when necessary.

    s3_object = get_aws_s3_service().Object(
        get_aws_s3_bucket_name(), filename)
    result = s3_object.put(Body=content)
    if result['ResponseMetadata']['HTTPStatusCode'] not in [200, 201]:
        raise Exception('Unable to store %s into S3 bucket %s' % (
            filename, get_aws_s3_bucket_name()))
    http_uri = 'https://%s.s3.%s.amazonaws.com/%s' % (
        get_aws_s3_bucket_name(), get_aws_s3_bucket_region(), filename)
    return http_uri

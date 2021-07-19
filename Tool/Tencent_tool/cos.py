from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from django.conf import settings
from sts.sts import Sts
from qcloud_cos.cos_exception import CosServiceError


def create_bucket(bucket, region='ap-shanghai'):
    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY)
    client = CosS3Client(config)
    client.create_bucket(
        Bucket=bucket,
        ACL="public-read"
    )
    #添加COS跨域设置
    cors_config = {
        'CORSRule': [
            {
                'AllowedOrigin': '*',
                'AllowedMethod': ['GET', 'PUT', 'HEAD', 'POST', 'DELETE'],
                'AllowedHeader': '*',
                'ExposeHeader': '*',
                'MaxAgeSeconds': 500
            }
        ]
    }
    response = client.put_bucket_cors(
        Bucket=bucket,
        CORSConfiguration=cors_config
    )
    print(response)


def upload_file(bucket, region, file_object, key):
    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY)
    client = CosS3Client(config)
    response = client.upload_file_from_buffer(
        Bucket=bucket,
        Body=file_object,
        Key=key
    )

    return "https://{}.cos.{}.myqcloud.com/{}".format(bucket, region, key)


def delete_file(bucket, region, key):
    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY)
    client = CosS3Client(config)
    client.delete_object(
        Bucket=bucket,
        Key=key
    )


def delete_file_list(bucket, region, key_list):
    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY)
    client = CosS3Client(config)
    objects = {
        "Quiet": "true",
        "Object": key_list
    }
    client.delete_objects(
        Bucket=bucket,
        Delete=objects
    )


def credential(bucket, region):
    config = {
        # 'url': 'https://sts.tencentcloudapi.com/',
        # 'domain': 'sts.tencentcloudapi.com',
        # 临时密钥有效时长，单位是秒
        'duration_seconds': 1800,
        'secret_id': settings.TENCENT_COS_ID,
        # 固定密钥
        'secret_key': settings.TENCENT_COS_KEY,

        'bucket': bucket,
        # 换成 bucket 所在地区
        'region': region,
        # 这里改成允许的路径前缀，可以根据自己网站的用户登录态判断允许上传的具体路径
        # 例子： a.jpg 或者 a/* 或者 * (使用通配符*存在重大安全风险, 请谨慎评估使用)
        'allow_prefix': '*',
        # 密钥的权限列表。简单上传和分片需要以下的权限，其他权限列表请看 https://cloud.tencent.com/document/product/436/31923
        'allow_actions': [
            # 简单上传
            'name/cos:PutObject',
            # 'name/cos:PostObject',
            # # 分片上传
            # 'name/cos:InitiateMultipartUpload',
            # 'name/cos:ListMultipartUploads',
            # 'name/cos:ListParts',
            # 'name/cos:UploadPart',
            # 'name/cos:CompleteMultipartUpload'
        ],
    }

    try:
        sts = Sts(config)
        result_dict = sts.get_credential()
        return result_dict
    except Exception as e:
        print(e)


def check_file(bucket, region, key):
    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY)
    client = CosS3Client(config)
    response = client.head_object(
        Bucket=bucket,
        Key=key
    )

    return response


def delete_bucket(bucket, region,):
    """
    1、删除桶里所有文件
    2、删除桶里所有碎片文件
    3、删除空桶
    """
    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY)
    client = CosS3Client(config)
    try:
        #找到所有文件并删除
        while True:
            part_objects = client.list_objects(bucket)
            # print(part_objects)
            #如果获取不到Contents的值代表桶里没有文件了
            contents = part_objects.get('Contents')
            # print(contents)
            if not contents:
                break

            #批量删除
            objects = {
                "Quiet": "true",
                "Object": [{'Key': item["Key"]} for item in contents],
            }
            client.delete_objects(bucket, objects)

            if part_objects['IsTruncated'] == 'false':
                break

        #找到所有碎片文件并删除
        while True:
            part_uploads = client.list_multipart_uploads(bucket)
            # print(part_uploads)
            uploads = part_uploads.get('Upload')
            if not uploads:
                break
            for item in uploads:
                client.abort_multipart_upload(bucket, item['Key'], item['UploadId'])
            if part_uploads['IsTruncated'] == 'false':
                break

        client.delete_bucket(bucket)
    except CosServiceError as e:
        print(e)


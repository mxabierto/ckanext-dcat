import os
import logging
from slugify import slugify

log = logging.getLogger(__name__)


def dcat_to_ckan(dcat_dict):

    package_dict = {}

    package_dict['title'] = dcat_dict.get('title')
    package_dict['notes'] = dcat_dict.get('description')
    package_dict['url'] = dcat_dict.get('landingPage')


    package_dict['tags'] = []
    for keyword in dcat_dict.get('keyword', []):
        keyword = keyword.replace("'", "").replace('(', "").replace(')',"").replace(',', '').replace('.', '').replace(';', '')
        package_dict['tags'].append({'name': keyword})

     # Nivel de gobierno por medio del vocabulario
    if dcat_dict.get('govType', False):
        package_dict['tags'].append({
            'name': dcat_dict.get('govType').capitalize(),
            'vocabulary_id': os.environ.get('VOCABULARY_GOV_TYPE_ID', '910b5e72-2723-466d-a892-4be1e4129120')
        })

    package_dict['gov_type'] = dcat_dict.get('govType').capitalize()

    package_dict['extras'] = []
    for key in ['issued', 'modified']:
        package_dict['extras'].append({'key': 'dcat_{0}'.format(key), 'value': dcat_dict.get(key)})

    package_dict['extras'].append({'key': 'guid', 'value': dcat_dict.get('identifier')})

    dcat_publisher = dcat_dict.get('publisher')
    if isinstance(dcat_publisher, basestring):
        package_dict['owner_org'] = slugify(dcat_publisher, max_length=100)
        package_dict['extras'].append({'key': 'dcat_publisher_name', 'value': dcat_publisher})
    elif isinstance(dcat_publisher, dict) and dcat_publisher.get('name'):
        package_dict['owner_org'] = slugify(dcat_publisher.get('name'), max_length=100)
        package_dict['extras'].append({'key': 'dcat_publisher_name', 'value': dcat_publisher.get('name')})
        package_dict['extras'].append({'key': 'dcat_publisher_email', 'value': dcat_publisher.get('mbox')})
        package_dict['extras'].append({'key': 'publisher_type', 'value': dcat_publisher.get('position')})

    if dcat_dict.get('theme'):
        package_dict['extras'].append({
            'key': 'theme', 'value': dcat_dict.get('theme').title()
        })

    package_dict['extras'].append({
        'key': 'frequency', 'value': dcat_dict.get('accrualPeriodicity', '')
    })

    if dcat_dict.get('temporal'):
        start, end = dcat_dict.get('temporal').split('/')
        package_dict['extras'].append({
            'key': 'temporal_start', 'value': start
        })
        package_dict['extras'].append({
            'key': 'temporal_end', 'value': end
        })

    if dcat_dict.get('spatial'):
        package_dict['extras'].append({
            'key': 'spatial_text',
            'value': dcat_dict.get('spatial')
        })

    if dcat_dict.get('comments'):
        package_dict['extras'].append({
            'key': 'version_notes',
            'value': dcat_dict.get('comments')
        })

    if dcat_dict.get('dataDictionary'):
        package_dict['extras'].append({
            'key': 'dataDictionary',
            'value': dcat_dict.get('dataDictionary')
        })

    if dcat_dict.get('quality'):
        package_dict['extras'].append({
            'key': 'quality',
            'value': dcat_dict.get('quality')
        })

    package_dict['extras'].append({
        'key': 'language',
        'value': dcat_dict.get('language', [])
    })

    package_dict['resources'] = []
    for distribution in dcat_dict.get('distribution', []):
        mt = distribution.get('mediaType')
        fr = mt.split('/')[-1] if hasattr(mt, 'split') else ''
        resource = {
            'name': distribution.get('title'),
            'description': distribution.get('description'),
            'url': distribution.get('downloadURL') or distribution.get('accessURL'),
            'format': fr
        }

        if distribution.get('byteSize'):
            try:
                resource['size'] = int(distribution.get('byteSize'))
            except ValueError:
                pass
        package_dict['resources'].append(resource)

    # print package_dict
    return package_dict


def ckan_to_dcat(package_dict):

    dcat_dict = {}

    dcat_dict['title'] = package_dict.get('title')
    dcat_dict['description'] = package_dict.get('notes')
    dcat_dict['landingPage'] = package_dict.get('url')


    dcat_dict['keyword'] = []
    for tag in package_dict.get('tags', []):
        dcat_dict['keyword'].append(tag['name'])


    dcat_dict['publisher'] = {}

    for extra in package_dict.get('extras', []):
        if extra['key'] in ['dcat_issued', 'dcat_modified']:
            dcat_dict[extra['key'].replace('dcat_', '')] = extra['value']

        elif extra['key'] == 'language':
            dcat_dict['language'] = extra['value'].split(',')

        elif extra['key'] == 'dcat_publisher_name':
            dcat_dict['publisher']['name'] = extra['value']

        elif extra['key'] == 'dcat_publisher_email':
            dcat_dict['publisher']['mbox'] = extra['value']

        elif extra['key'] == 'guid':
            dcat_dict['identifier'] = extra['value']

    if not dcat_dict['publisher'].get('name') and package_dict.get('maintainer'):
        dcat_dict['publisher']['name'] = package_dict.get('maintainer')
        if package_dict.get('maintainer_email'):
            dcat_dict['publisher']['mbox'] = package_dict.get('maintainer_email')

    dcat_dict['distribution'] = []
    for resource in package_dict.get('resources', []):
        distribution = {
            'title': resource.get('name'),
            'description': resource.get('description'),
            'format': resource.get('format'),
            'byteSize': resource.get('size'),
            # TODO: downloadURL or accessURL depending on resource type?
            'accessURL': resource.get('url'),
        }
        dcat_dict['distribution'].append(distribution)

    return dcat_dict

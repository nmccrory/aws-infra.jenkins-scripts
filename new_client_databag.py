import random
import string
import sys
import click
from collections import OrderedDict
import hvac
import os
import requests.packages.urllib3

file_name = "vault_token.txt"

def get_vault_client():
    """
    Return a vault client if possible.
    """
    # Disable warnings for the insecure calls
    requests.packages.urllib3.disable_warnings()
    token_type = "GITHUB|SANCTUARY"
    vault_addr = os.getenv("VAULT_ADDR", "https://vault.drud.com:8200")
    sanctuary_token_path = os.path.join('/var/jenkins_home/workspace/ops-create-sanctuary-token/', file_name)
    if os.path.exists(sanctuary_token_path):
        with open(sanctuary_token_path, 'r') as fp:
            vault_token = fp.read().strip()
            token_type = "SANCTUARY"
    else:
        vault_token = os.getenv("GITHUB_TOKEN")
        token_type = "GITHUB"

    if not vault_addr or not vault_token:
        print "You must provide a GITHUB_TOKEN environment variables."
        print "(Have you authenticated with drud using `drud auth github` to create your GITHUB_TOKEN?)"
        sys.exit(1)

    if token_type == "SANCTUARY":
        vault_client = hvac.Client(url=vault_addr, token=vault_token, verify=False)
    elif token_type == "GITHUB":
        vault_client = hvac.Client(url=vault_addr, verify=False)
        vault_client.auth_github(vault_token)
    else: # The token value was not overridden
        print "Something went wrong."
        sys.exit(1)

    if vault_client.is_initialized() and vault_client.is_sealed():
        print "Vault is initialized but sealed."
        sys.exit(1)

    if not vault_client.is_authenticated():
        print "Could not get auth."
        sys.exit(1)

    print "Using {t_type} for authentication.".format(t_type=token_type.lower())
    return vault_client

def to_boolean(x):
    return x.lower() == 'true'

def rand_string(num_digits=16, string_type=string.hexdigits):
    if string_type == "base64":
        string_type = string.ascii_letters + string.digits + "+" + "/"
    return ''.join([random.choice(string_type) for _ in range(num_digits)])

# sitename = sys.argv[4]
# site_type = sys.argv[5]
# db_server_local = sys.argv[6]
# db_server_staging = sys.argv[7]
# db_server_production = sys.argv[8]
# admin_username = sys.argv[9]
# #production_domain = sys.argv[10]
# new_site = to_boolean(sys.argv[10])
# wp_active_theme = sys.argv[14]
# wp_multisite = to_boolean(sys.argv[13])

@click.command()
@click.option('--sitename', type=click.STRING)
@click.option('--site-type', type=click.Choice(['wp', 'd7', 'd8', 'none']))
@click.option('--db-server-local', type=click.STRING)
@click.option('--db-server-staging', type=click.STRING)
@click.option('--db-server-production', type=click.STRING)
@click.option('--admin-username', type=click.STRING)
@click.option('--new-site', type=click.BOOL)
@click.option('--wp-active-theme', type=click.STRING)
@click.option('--wp-multisite', type=click.BOOL)
@click.option('--staging-url', type=click.STRING)
@click.option('--production-url', type=click.STRING)
@click.option('--admin-mail', type=click.STRING)
@click.option('--github-org', type=click.STRING)
def create_bag(sitename,
    site_type,
    db_server_local,
    db_server_staging,
    db_server_production,
    admin_username,
    new_site,
    wp_active_theme,
    wp_multisite,
    staging_url,
    production_url,
    admin_mail,
    github_org):

    if site_type == 'd7' or site_type == 'd8':
        site_type = 'drupal'

    # values that are consistent across environment and platform
    common = {
        'sitename': sitename,
        'site_type': site_type,
        'apache_owner': 'nginx',
        'apache_group': 'nginx',
        'admin_mail': admin_mail,
        'db_name': sitename,
        'db_username': sitename + '_db',
        'php': {
            'version': "5.6"
        },
        'docroot': '/var/www/' + sitename + '/current/docroot'
    }

    # values that are different per environment
    default = {
        'admin_username': admin_username,
        'admin_password': rand_string(),
        'repository': 'git@github.com:{org}/{site}.git'.format(org=github_org, site=sitename),
        'revision': 'staging',
        'db_host': db_server_local,
        'db_user_password': rand_string(),
        'server_aliases': [
            "localhost"
        ],
        'hosts': [
            "localhost"
        ]
    }
    staging = {
        'admin_username': admin_username,
        'admin_password': rand_string(),
        'repository': 'git@github.com:{org}/{site}.git'.format(org=github_org, site=sitename),
        'revision': 'staging',
        'db_host': db_server_staging,
        'db_user_password': rand_string(),
        'search_replace': [
            'http://localhost:1025',
        ],
        'server_aliases': [
            staging_url
        ]
    }
    production = {
        'admin_username': admin_username,
        'admin_password': rand_string(),
        'repository': 'git@github.com:{org}/{site}.git'.format(org=github_org, site=sitename),
        'revision': 'master',
        'db_host': db_server_production,
        'db_user_password': rand_string(),
        'search_replace': [
            'http://'+staging_url,
            'https://'+staging_url
        ],
        'server_aliases': [
            production_url
        ]
    }
    client_metadata = {
        'company_legal_name': '',
        'company_city': '',
        'company_state': '',
        'primary_contact': {
            'name': '',
            'phone_number': '',
            'email_address': ''
        },
        'production_url': '',
        'we_are_hosting': True,
        'transactional_email': {
            'provider': '',
            'username': '',
            'password': ''
        },
        'dns': {
            'provider': '',
            'username': '',
            'password': ''
        },
        'ssl': {
            'provider': '',
            'username': '',
            'password': ''
        },
        'theme_license': {
            'item_title': '',
            'item_url': '',
            'item_purchase_code': '',
            'purchase_date': ''
        }
    }


    # new site
    if new_site:
        new_site = {
            'new_site': True,
            'install_profile': sitename
        }
    else:
        new_site = {}


    # Need to set new_site in all envs - add to common
    common = dict(common.items() + new_site.items())

    # values that are different per platform
    if site_type == 'wp':
        type_keys_default = {
            'auth_key': rand_string(48, 'base64'),
            'secure_auth_key': rand_string(48, 'base64'),
            'logged_in_key': rand_string(48, 'base64'),
            'nonce_key': rand_string(48, 'base64'),
            'auth_salt': rand_string(48, 'base64'),
            'secure_auth_salt': rand_string(48, 'base64'),
            'logged_in_salt': rand_string(48, 'base64'),
            'nonce_salt': rand_string(48, 'base64'),
            'url': 'http://localhost:1025',
            'active_theme': wp_active_theme,
            'multisite': wp_multisite
        }
        type_keys_staging = {
            'auth_key': rand_string(48, 'base64'),
            'secure_auth_key': rand_string(48, 'base64'),
            'logged_in_key': rand_string(48, 'base64'),
            'nonce_key': rand_string(48, 'base64'),
            'auth_salt': rand_string(48, 'base64'),
            'secure_auth_salt': rand_string(48, 'base64'),
            'logged_in_salt': rand_string(48, 'base64'),
            'nonce_salt': rand_string(48, 'base64'),
            'url': 'https://' + staging_url,
            'active_theme': wp_active_theme,
            'multisite': wp_multisite
        }
        type_keys_production = {
            'auth_key': rand_string(48, 'base64'),
            'secure_auth_key': rand_string(48, 'base64'),
            'logged_in_key': rand_string(48, 'base64'),
            'nonce_key': rand_string(48, 'base64'),
            'auth_salt': rand_string(48, 'base64'),
            'secure_auth_salt': rand_string(48, 'base64'),
            'logged_in_salt': rand_string(48, 'base64'),
            'nonce_salt': rand_string(48, 'base64'),
            'url': 'https://' + production_url,
            'active_theme': wp_active_theme,
            'multisite': wp_multisite
        }
    elif site_type == 'drupal':
        type_keys_default = {
            'hash_salt': rand_string(48, 'base64'),
            'cmi_sync': '/var/www/' + sitename + '/current/sync',
        }
        type_keys_staging = {
            'hash_salt': rand_string(48, 'base64'),
            'cmi_sync': '/var/www/' + sitename + '/current/sync',
        }
        type_keys_production = {
            'hash_salt': rand_string(48, 'base64'),
            'cmi_sync': '/var/www/' + sitename + '/current/sync',
        }
    else:
        type_keys_default = {}
        type_keys_staging = {}
        type_keys_production = {}


    # # Construct a new data bag
    # bag_item = Chef::DataBagItem.new
    bag_item = OrderedDict()
    # bag_item.data_bag('nmdhosting')
    bag_item['id'] = sitename
    bag_item['_default'] = dict(common.items() + default.items() + type_keys_default.items())
    bag_item['staging'] = dict(common.items() + staging.items() + type_keys_staging.items())
    bag_item['production'] = dict(common.items() + production.items() + type_keys_production.items())
    bag_item['client_metadata'] = client_metadata

    client = get_vault_client()
    is_drud_jenkins = bool(int(os.getenv("IS_DRUD_JENKINS", "0")))
    folder = 'drudhosting' if is_drud_jenkins else 'nmdhosting'
    secret_path = 'secret/databags/{folder}/{site}'.format(folder=folder,site=sitename)
    secret = client.read(secret_path)
    if secret and 'data' in secret:
        raise Exception("A secret already exists at path: {path}. Please run this job again with a new site name.".format(path=secret_path))

    client.write(secret_path, **bag_item)

if __name__ == '__main__':
    create_bag()

import os
import requests
import base64
import time
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

elasticsearch_url = os.getenv("ELASTICSEARCH_URL")
dashboard_uid = os.getenv("GRAFANA_DASHBOARD_UID", "developer-activity-dashboard")

if not elasticsearch_url:
    raise ValueError("Please set the ELASTICSEARCH_URL environment variable")

grafana_api_token_env = os.getenv("GRAFANA_API_TOKEN")
grafana_url = os.getenv("GRAFANA_URL", "http://$GRAFANA_URL/")

if not grafana_url:
    raise ValueError("Please set the GRAFANA_URL environment variable")

# Basic auth variables only needed when token is not provided
grafana_username = os.getenv("GRAFANA_USERNAME")
grafana_password = os.getenv("GRAFANA_PASSWORD")

if not grafana_api_token_env:
    if not grafana_username:
        raise ValueError("Please set the GRAFANA_USERNAME environment variable")
    if not grafana_password:
        raise ValueError("Please set the GRAFANA_PASSWORD environment variable")

# Demo user credentials - can be configured via environment or use defaults
demo_username = os.getenv("DEMO_USER_USERNAME", "demo-user")
demo_password = os.getenv("DEMO_USER_PASSWORD", "dem0-passw0rd")

service_account_name = "sa-for-cpuad"


def poll_for_elasticsearch():
    """
    Polls the Elasticsearch server until it is reachable.

    Raises:
        ValueError: If the Elasticsearch server is not reachable.
    """
    while True:
        try:
            response = requests.get(f"{elasticsearch_url.rstrip('/')}/_cluster/health")
            if response.status_code == 200:
                logging.info("Elasticsearch is up and running.")
                break
        except requests.exceptions.RequestException as e:
            logging.error(f"Elasticsearch is not reachable: {e}")
        time.sleep(5)


def poll_for_grafana():
    """
    Polls the Grafana server until it is reachable.

    Raises:
        ValueError: If the Grafana server is not reachable.
    """
    while True:
        try:
            response = requests.get(f"{grafana_url.rstrip('/')}/api/health")
            if response.status_code == 200:
                # read the response content
                content = response.json()
                logging.info(f"Grafana health status: {content}")

                if content.get("database") != "ok":
                    logging.error("Grafana database is not healthy.")
                    raise ValueError("Grafana database is not healthy.")

                logging.info("Grafana is up and running.")
                break
        except requests.exceptions.RequestException as e:
            logging.error(f"Grafana is not reachable: {e}")
        time.sleep(5)

def safe_request(method, url, headers=None, json=None, max_retries=3, retry_interval=5):
    """General purpose HTTP request handler with retries"""
    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, headers=headers, json=json)
            if response.status_code in [200,201,404]:
                return response
            else:
                logging.error(f"Request failed with status code {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Request exception: {e}")
        time.sleep(retry_interval)
    raise ValueError(f"Unable to complete request after {max_retries} retries: {url}")

def get_existing_grafana_service_account_id(headers):
    """
    Retrieves the existing Grafana service account.

    Returns:
        The service account ID if it exists, None otherwise.
    """
    result = safe_request(
        "GET",
        f"{grafana_url.rstrip('/')}/api/serviceaccounts/search?query={service_account_name}",
        headers=headers,
    )
    # time.sleep(1)  # Add a 1-second delay

    if result.status_code != 200:
        logging.error(
            f"Failed to retrieve service accounts: {result.status_code} - {result.text}"
        )
        raise ValueError(
            f"Failed to retrieve service accounts - {result.status_code} - {result.text}"
        )

    service_accounts = result.json().get("serviceAccounts", [])

    if not service_accounts:
        logging.info("No existing service accounts found.")
        return None

    for account in service_accounts:
        if account.get("name") == service_account_name:
            logging.info(f"Service account {service_account_name} already exists.")
            return account.get("id")

    logging.info(f"Service account {service_account_name} not found.")
    return None


def delete_existing_grafana_service_account(headers, service_account_id):
    """
    Deletes the existing Grafana service account.

    Args:
        service_account_id: The ID of the service account to delete.
    """
    result = requests.delete(
        f"{grafana_url.rstrip('/')}/api/serviceaccounts/{service_account_id}",
        headers=headers,
    )
    time.sleep(1)  # Add a 1-second delay

    if result.status_code != 200:
        logging.error(
            f"Failed to delete service account: {result.status_code} - {result.text}"
        )
        raise ValueError(
            f"Failed to delete service account - {result.status_code} - {result.text}"
        )
    logging.info("Service account deleted successfully.")


def setup_grafana_service_account():
    """
    Creates a Grafana service account using basic authentication.

    Returns:
        A dictionary containing the headers for the request.
    """
    headers = get_grafana_basic_credentials_headers()

    # Check if the service account already exists
    existing_service_account_id = get_existing_grafana_service_account_id(
        headers=headers
    )

    if existing_service_account_id:
        delete_existing_grafana_service_account(
            headers=headers, service_account_id=existing_service_account_id
        )

    service_account_id = create_service_account(headers=headers)

    grafana_api_token = create_grafana_access_token(
        headers=headers, service_account_id=service_account_id
    )

    return grafana_api_token


def create_grafana_access_token(headers, service_account_id):
    result = safe_request(
        "POST",
        f"{grafana_url.rstrip('/')}/api/serviceaccounts/{service_account_id}/tokens",
        headers=headers,
        json={"name": "sa-for-cpuad-key", "secondsToLive": 0},
    )

    if result.status_code != 200:
        logging.error(
            f"Failed to create Grafana API token: {result.status_code} - {result.text}"
        )
        raise ValueError("Failed to create Grafana API token")

    logging.info("Grafana API token created successfully.")

    grafana_api_token = result.json().get("key")

    if not grafana_api_token:
        logging.error("Failed to retrieve Grafana API token")
        raise ValueError("Failed to retrieve Grafana API token")

    return grafana_api_token


def get_grafana_headers(grafana_token=None):
    """
    Get headers for Grafana API calls, using either token or basic auth.
    
    Args:
        grafana_token: API token if available, otherwise uses basic auth
    
    Returns:
        Dictionary of headers for API requests
    """
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    
    if grafana_token:
        headers["Authorization"] = f"Bearer {grafana_token}"
    else:
        # Use basic auth as fallback
        credentials = f"{grafana_username}:{grafana_password}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        headers["Authorization"] = f"Basic {encoded_credentials}"
    
    return headers


def get_grafana_basic_credentials_headers():
    credentials = f"{grafana_username}:{grafana_password}"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_credentials}",
    }

    return headers


def create_service_account(headers):
    result = safe_request(
        "POST",
        f"{grafana_url.rstrip('/')}/api/serviceaccounts",
        headers=headers,
        json={"name": service_account_name, "role": "Admin", "isDisabled": False},
    )
    # time.sleep(1)  # Add a 1-second delay

    if result.status_code != 201:
        logging.error(
            f"Failed to create service account: {result.status_code} - {result.text}"
        )
        raise ValueError(
            f"Failed to create service account - {result.status_code} - {result.text}"
        )

    logging.info(f"Service account {result.json().get('name')} created successfully.")

    service_account_id = result.json().get("id")
    return service_account_id


def add_grafana_data_sources(grafana_token, max_retries=3, retry_interval=5):
    headers = get_grafana_headers(grafana_token)

    # Data sources to add
    data_sources = [
        {
            "name": "elasticsearch-breakdown",
            "index": "copilot_usage_breakdown",
        },
        {
            "name": "elasticsearch-breakdown-chat",
            "index": "copilot_usage_breakdown_chat",
        },
        {
            "name": "elasticsearch-total",
            "index": "copilot_usage_total",
        },
        {
            "name": "elasticsearch-seat-info-settings",
            "index": "copilot_seat_info_settings",
        },
        {
            "name": "elasticsearch-seat-assignments",
            "index": "copilot_seat_assignments",
        },
        {
            "name": "elasticsearch-user-metrics",
            "index": "copilot_user_metrics",
        },
        {
            "name": "elasticsearch-user-metrics-top-by-day",
            "index": os.getenv("INDEX_USER_METRICS_TOP_BY_DAY", "copilot_user_metrics_top_by_day"),
        },
        {
            "name": "elasticsearch-user-metrics-summary",
            "index": "copilot_user_metrics_summary",
        },
        {
            "name": "elasticsearch-user-adoption",
            "index": "copilot_user_adoption",
        },
        {
            "name": "elasticsearch-developer-activity",
            "index": os.getenv("INDEX_DEVELOPER_ACTIVITY", "developer_activity"),
        },
    ]

    # Template for the payload
    def create_payload(name, index):
        # Use appropriate timeField based on the index
        if index == "copilot_user_adoption":
            # Use @timestamp for adoption index to align with Grafana time filtering
            time_field = "@timestamp"
        elif index == "copilot_user_metrics_summary":
            time_field = "@timestamp"
        else:
            time_field = "day"
        
        # Use the data source name as a stable UID for easier dashboard provisioning
        stable_uid = name
        
        return {
            "name": name,
            "uid": stable_uid,
            "type": "elasticsearch",
            "access": "proxy",
            "url": f"{elasticsearch_url.rstrip('/')}",
            "basicAuth": False,
            "withCredentials": False,
            "isDefault": False,
            "jsonData": {
                "includeFrozen": False,
                "index": index,
                "logLevelField": "",
                "logMessageField": "",
                "timeField": time_field,
                "timeInterval": "1d",
            },
        }

    # Add each data source
    for ds in data_sources:
        logging.info(f"Checking if data source {ds['name']} already exists...")
        check_resp = safe_request(
            "GET",
            f"{grafana_url.rstrip('/')}/api/datasources/name/{ds['name']}",
            headers=headers
        )
        payload = create_payload(ds["name"], ds["index"])

        if check_resp.status_code == 200:
            ds_details = check_resp.json()
            payload["id"] = ds_details["id"]
            # Keep our stable UID, don't use the existing random one
            logging.info(f"Updating data source: {ds['name']}...")
            safe_request(
                "PUT",
                f"{grafana_url.rstrip('/')}/api/datasources/{ds_details['id']}",
                headers=headers,
                json=payload,
                max_retries=max_retries,
                retry_interval=retry_interval,
            )
        else:
            logging.info(f"Creating data source: {ds['name']}...")
            safe_request(
                "POST",
                f"{grafana_url.rstrip('/')}/api/datasources",
                headers=headers,
                json=payload,
                max_retries=max_retries,
                retry_interval=retry_interval,
            )

        verify_resp = safe_request(
            "GET",
            f"{grafana_url.rstrip('/')}/api/datasources/name/{ds['name']}",
            headers=headers,
            max_retries=max_retries,
            retry_interval=retry_interval,
        )

        if verify_resp.status_code == 200:
            logging.info(f"Data source verified: {ds['name']}")
        else:
            raise ValueError(f"Data source verification failed: {ds['name']}")


def create_demo_user(grafana_token=None):
    """
    Creates a demo user with read-only (Viewer) access.
    The user will have access to all dashboards in read-only mode.
    
    Credentials are read from environment variables:
    - DEMO_USER_USERNAME (default: demo-user)
    - DEMO_USER_PASSWORD (default: dem0-passw0rd)
    """
    headers = get_grafana_headers(grafana_token)
    
    logging.info(f"Creating/updating demo user: {demo_username}")
    
    # Check if user already exists
    check_resp = safe_request(
        "GET",
        f"{grafana_url.rstrip('/')}/api/users/lookup?loginOrEmail={demo_username}",
        headers=headers
    )
    
    if check_resp.status_code == 200:
        logging.info(f"User {demo_username} already exists. Updating password...")
        user_data = check_resp.json()
        user_id = user_data.get("id")
        
        # Update password
        update_resp = safe_request(
            "PUT",
            f"{grafana_url.rstrip('/')}/api/admin/users/{user_id}/password",
            headers=headers,
            json={"password": demo_password}
        )
        
        if update_resp.status_code == 200:
            logging.info(f"Password updated for user {demo_username}")
        else:
            logging.warning(f"Failed to update password for user {demo_username}")
            
    else:
        # Create new user
        logging.info(f"Creating demo user: {demo_username}")
        create_resp = safe_request(
            "POST",
            f"{grafana_url.rstrip('/')}/api/admin/users",
            headers=headers,
            json={
                "name": "Demo User",
                "login": demo_username,
                "password": demo_password,
                "email": "demo-user@example.com",
                "role": "Viewer"  # Viewer role provides read-only access
            }
        )
        
        if create_resp.status_code in [200, 201]:
            logging.info(f"Successfully created demo user: {demo_username}")
        else:
            logging.error(f"Failed to create demo user: {create_resp.status_code} - {create_resp.text}")
            return False
    
    return True


def import_static_dashboards(dashboards_dir, grafana_token):
    """
    Imports all dashboard JSON files from a directory.
    
    Args:
        dashboards_dir: Path to directory containing dashboard JSON files
        grafana_token: Grafana API token for authentication
    """
    import pathlib
    
    if not os.path.exists(dashboards_dir):
        logging.info(f"Dashboards directory not found: {dashboards_dir}")
        return False
    
    dashboard_files = list(pathlib.Path(dashboards_dir).glob("*.json"))
    
    if not dashboard_files:
        logging.info(f"No dashboard JSON files found in {dashboards_dir}")
        return False
    
    headers = get_grafana_headers(grafana_token)
    
    imported_count = 0
    for dashboard_file in dashboard_files:
        try:
            with open(dashboard_file, 'r') as f:
                dashboard_content = f.read()
            
            dashboard_obj = json.loads(dashboard_content)
            
            # Handle export format with "dashboard" key
            if "dashboard" in dashboard_obj:
                api_payload = {
                    "dashboard": dashboard_obj["dashboard"],
                    "folderId": 0,
                    "overwrite": True,
                    "message": f"Dashboard imported from {dashboard_file.name}"
                }
            else:
                # Handle direct dashboard format
                api_payload = {
                    "dashboard": dashboard_obj,
                    "folderId": 0,
                    "overwrite": True,
                    "message": f"Dashboard imported from {dashboard_file.name}"
                }
            
            response = requests.post(
                f"{grafana_url.rstrip('/')}/api/dashboards/db",
                headers=headers,
                json=api_payload,
            )
            
            if response.status_code == 200:
                logging.info(f"Successfully imported dashboard: {dashboard_file.name}")
                imported_count += 1
            else:
                logging.error(f"Failed to import dashboard {dashboard_file.name}: {response.status_code} - {response.text}")
        
        except Exception as e:
            logging.error(f"Error importing dashboard {dashboard_file.name}: {e}")
    
    return imported_count > 0


if __name__ == "__main__":

    poll_for_grafana()

    # Prefer using an existing API token if provided (no password required)
    if grafana_api_token_env:
        logging.info("Using provided Grafana API token from environment.")
        grafana_token = grafana_api_token_env
    else:
        logging.info("No Grafana API token provided; attempting to use basic auth credentials.")
        try:
            # Try to create a service account for better security
            grafana_token = setup_grafana_service_account()
            logging.info("Successfully created Grafana service account and token.")
        except Exception as e:
            logging.warning(f"Failed to create service account: {e}")
            logging.info("Falling back to basic auth for API calls.")
            # Fallback: we'll use basic auth headers directly in API calls
            grafana_token = None

    logging.info("Adding Grafana data sources...")

    add_grafana_data_sources(grafana_token=grafana_token)

    logging.info("Successfully added Grafana data sources.")

    logging.info("Creating demo user with read-only access...")
    
    create_demo_user(grafana_token=grafana_token)
    
    logging.info("Successfully created or updated demo user.")

    logging.info("Importing static dashboards from provisioning directory...")
    
    # Import dashboards from provisioning directory
    # This handles both local (docker-compose) and deployed scenarios
    dashboard_sources = [
        "/app/grafana-provisioning/dashboards",  # Where they're copied in the container image
        "/var/lib/grafana/dashboards",  # Where Grafana mounts them in Azure
        "grafana-provisioning/dashboards",  # Relative path from working directory
        "../../../grafana-provisioning/dashboards",  # Relative path in container
    ]
    
    dashboards_imported = False
    for dashboard_dir in dashboard_sources:
        if import_static_dashboards(dashboard_dir, grafana_token):
            logging.info(f"Successfully imported dashboards from: {dashboard_dir}")
            dashboards_imported = True
            break
    
    if not dashboards_imported:
        logging.warning("No static dashboards were found or imported.")


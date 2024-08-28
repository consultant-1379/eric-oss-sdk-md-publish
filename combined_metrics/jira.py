import os
from msdevops_metrics.jira.jira_to_elk import main_function
print("calling jira main function")
functional_user_username = os.environ.get('FUNCTIONAL_USER_USERNAME', None)
functional_user_password = os.environ.get('FUNCTIONAL_USER_PASSWORD', None)
print(functional_user_username)
main_function()

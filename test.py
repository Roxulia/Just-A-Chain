import requests
import json

data = {'node' : 'http://192.168.0.2:4000', 'node_id': '12346'}
response = requests.post('https://www.ywangancoffee.com/seed_node.php?action=register_node',data=data)
print(response.json())
requests.get('https://www.ywangancoffee.com/seed_node.php?action=check_node')
response = requests.get('https://www.ywangancoffee.com/seed_node.php?action=get_all_nodes')
print(response.json())
from socket import *
import json
import os

# serve config
serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))

# create avatars directory
if not os.path.exists('avatars'):
    os.makedirs('avatars')

# list of valid users
users = {
    'A': {'username': 'A', 'password': 'A', 'lives': 2, 'sword': -1, 'shield': -1, 
          'slaying_potion': -1, 'healing_potion': -1},
    'B': {'username': 'B', 'password': 'B', 'lives': 2, 'sword': -1, 'shield': -1, 
          'slaying_potion': -1, 'healing_potion': -1},
    'C': {'username': 'C', 'password': 'C', 'lives': 2, 'sword': -1, 'shield': -1, 
          'slaying_potion': -1, 'healing_potion': -1},
    'D': {'username': 'D', 'password': 'D', 'lives': 2, 'sword': -1, 'shield': -1, 
          'slaying_potion': -1, 'healing_potion': -1}
}

# list of confirmed fights
confirmed_fights = []

# check if gamer is active (has lives > 0 and sword != -1)
def is_active(gamer):
    return gamer['lives'] > 0 and gamer['sword'] != -1

# get list of active gamers
def get_active_gamers():
    return [username for username, gamer in users.items() if is_active(gamer)]

# apply fight rules and update gamers states
def apply_fight_rules(requester, boss, fighting_item, fighting_item_strength):
    requester_gamer = users[requester]
    boss_gamer = users[boss]
    
    if fighting_item == 'sword':
        requester_strength = fighting_item_strength
        boss_strength = boss_gamer['shield']
        
        if boss_strength == requester_strength:
            # equal strength: both lose 1 life
            requester_gamer['lives'] -= 1
            boss_gamer['lives'] -= 1
            requester_gamer['sword'] -= 2
            boss_gamer['shield'] -= 2
            winner = 'none'
        elif boss_strength < requester_strength:
            # requester wins: requester gains 1 life, boss loses 1 life
            requester_gamer['lives'] += 1
            boss_gamer['lives'] -= 1
            requester_gamer['sword'] -= (requester_strength - boss_strength)
            boss_gamer['shield'] -= boss_strength
            winner = 'requester'
        else:  # boss_strength > requester_strength
            # boss wins: requester loses 1 life, boss gains 1 life
            requester_gamer['lives'] -= 1
            boss_gamer['lives'] += 1
            requester_gamer['sword'] -= requester_strength
            boss_gamer['shield'] -= (boss_strength - requester_strength)
            winner = 'boss'
            
        # ensure values don't go below 0
        requester_gamer['sword'] = max(0, requester_gamer['sword'])
        boss_gamer['shield'] = max(0, boss_gamer['shield'])
        
    elif fighting_item == 'slaying_potion':
        requester_strength = fighting_item_strength
        boss_strength = boss_gamer['healing_potion']
        
        if boss_strength == requester_strength:
            # equal strength: both lose 1 life
            requester_gamer['lives'] -= 1
            boss_gamer['lives'] -= 1
            requester_gamer['slaying_potion'] -= 2
            boss_gamer['healing_potion'] -= 2
            winner = 'none'
        elif boss_strength < requester_strength:
            # requester wins: requester gains 1 life, boss loses 1 life
            requester_gamer['lives'] += 1
            boss_gamer['lives'] -= 1
            requester_gamer['slaying_potion'] -= (requester_strength - boss_strength)
            boss_gamer['healing_potion'] -= boss_strength
            winner = 'requester'
        else:  # boss_strength > requester_strength
            # boss wins: requester loses 1 life, boss gains 1 life
            requester_gamer['lives'] -= 1
            boss_gamer['lives'] += 1
            requester_gamer['slaying_potion'] -= requester_strength
            boss_gamer['healing_potion'] -= (boss_strength - requester_strength)
            winner = 'boss'
            
        # values dont go below 0
        requester_gamer['slaying_potion'] = max(0, requester_gamer['slaying_potion'])
        boss_gamer['healing_potion'] = max(0, boss_gamer['healing_potion'])
    
    # lives dont go below 0
    requester_gamer['lives'] = max(0, requester_gamer['lives'])
    boss_gamer['lives'] = max(0, boss_gamer['lives'])
    
    return winner

print('The server is ready to receive')

# main loop
while True:
    try:
        message, clientAddress = serverSocket.recvfrom(4096)
        data = json.loads(message.decode())
        action = data.get('action')
        
        # login
        if action == 'login':
            username = data.get('username')
            password = data.get('password')
            print(f'Received a login request from user {username}')
            
            if username in users and users[username]['password'] == password:
                print(f'User {username} is authenticated')
                gamer = users[username]
                
                if gamer['lives'] == 0:
                    response = {'status': 'game_over', 'message': 'Game is over for this gamer'}
                else:
                    response = {
                        'status': 'success',
                        'gamer_state': {
                            'username': gamer['username'],
                            'lives': gamer['lives'],
                            'sword': gamer['sword'],
                            'shield': gamer['shield'],
                            'slaying_potion': gamer['slaying_potion'],
                            'healing_potion': gamer['healing_potion']
                        }
                    }
            else:
                print(f'Login rejected for user {username}')
                response = {'status': 'rejected', 'message': 'Invalid username or password'}
            
            serverSocket.sendto(json.dumps(response).encode(), clientAddress)
            
        # upload avatar
        elif action == 'upload_avatar':
            username = data.get('username')
            avatar_hex = data.get('avatar_data')
            filename = data.get('filename')
            print(f'Received avatar upload request from user {username}')
            
            try:
                # Convert hex string back to bytes
                avatar_data = bytes.fromhex(avatar_hex)
                
                avatar_path = os.path.join('avatars', f'{username}.jpg')
                with open(avatar_path, 'wb') as f:
                    f.write(avatar_data)
                
                print(f'Avatar uploaded for user {username} as {username}.jpg')
                response = {'status': 'success', 'message': 'Avatar uploaded successfully'}
            except Exception as e:
                print(f'Error uploading avatar: {e}')
                response = {'status': 'error', 'message': f'Error uploading avatar: {str(e)}'}
            
            serverSocket.sendto(json.dumps(response).encode(), clientAddress)
            
        # update state
        elif action == 'update_state':
            username = data.get('username')
            gamer_state = data.get('gamer_state')
            print(f'Received state update from user {username}')
            
            if username in users:
                users[username].update({
                    'sword': gamer_state['sword'],
                    'shield': gamer_state['shield'],
                    'slaying_potion': gamer_state['slaying_potion'],
                    'healing_potion': gamer_state['healing_potion']
                })
                print(f'State updated for user {username}')
                response = {'status': 'success'}
            else:
                response = {'status': 'error', 'message': 'User not found'}
            
            serverSocket.sendto(json.dumps(response).encode(), clientAddress)
            
        # get active gamers
        elif action == 'get_active_gamers':
            username = data.get('username')
            print(f'Received request for active gamers list from user {username}')
            
            active_usernames = get_active_gamers()
            # Remove the requesting user from the list
            active_usernames = [u for u in active_usernames if u != username]
            
            if not active_usernames:
                response = {'status': 'empty', 'gamers': []}
            else:
                response = {'status': 'success', 'gamers': active_usernames}
            
            print(f'Sent list of {len(active_usernames)} active gamers to user {username}')
            serverSocket.sendto(json.dumps(response).encode(), clientAddress)
            
        #download avatar
        elif action == 'download_avatar':
            username = data.get('username')
            target_username = data.get('target_username')
            print(f'Received avatar download request from user {username} for {target_username}')
            
            avatar_path = os.path.join('avatars', f'{target_username}.jpg')
            if os.path.exists(avatar_path):
                with open(avatar_path, 'rb') as f:
                    avatar_data = f.read()
                
                response = {
                    'status': 'success',
                    'avatar_data': avatar_data.hex(),
                    'filename': f'{target_username}.jpg'
                }
                print(f'Sent avatar file for {target_username} to user {username}')
            else:
                response = {'status': 'error', 'message': 'Avatar not found'}
                print(f'Avatar not found for {target_username}')
            
            serverSocket.sendto(json.dumps(response).encode(), clientAddress)
        # get confirmed fights  
        elif action == 'get_confirmed_fights':
            username = data.get('username')
            print(f'Received request for confirmed fights list from user {username}')
            
            response = {'status': 'success', 'fights': confirmed_fights}
            print(f'Sent list of {len(confirmed_fights)} confirmed fights to user {username}')
            serverSocket.sendto(json.dumps(response).encode(), clientAddress)
        
        # send fight request
        elif action == 'send_fight_request':
            requester = data.get('requester')
            boss = data.get('boss')
            fighting_item = data.get('fighting_item')
            fighting_item_strength = data.get('fighting_item_strength')
            print(f'Received fight request from user {requester} to fight {boss} with {fighting_item} strength {fighting_item_strength}')
            
            # Validate request
            if requester not in users or boss not in users:
                response = {'status': 'error', 'message': 'Invalid user'}
            elif requester == boss:
                response = {'status': 'error', 'message': 'Cannot fight yourself'}
            elif not is_active(users[requester]) or not is_active(users[boss]):
                response = {'status': 'error', 'message': 'One or both gamers are inactive'}
            else:
                requester_gamer = users[requester]
                
                # Check if requester has enough strength
                if fighting_item == 'sword':
                    if requester_gamer['sword'] < fighting_item_strength:
                        response = {'status': 'error', 'message': 'Insufficient sword strength'}
                        serverSocket.sendto(json.dumps(response).encode(), clientAddress)
                        continue
                elif fighting_item == 'slaying_potion':
                    if requester_gamer['slaying_potion'] < fighting_item_strength:
                        response = {'status': 'error', 'message': 'Insufficient slaying potion strength'}
                        serverSocket.sendto(json.dumps(response).encode(), clientAddress)
                        continue
                else:
                    response = {'status': 'error', 'message': 'Invalid fighting item'}
                    serverSocket.sendto(json.dumps(response).encode(), clientAddress)
                    continue
                
                # Server validates and confirms the request
                print(f'Confirmed fight request for user {requester}')
                
                # Apply fight rules
                winner = apply_fight_rules(requester, boss, fighting_item, fighting_item_strength)
                
                # Create fight request record
                fight_request = {
                    'requester': requester,
                    'boss': boss,
                    'fighting_item': fighting_item,
                    'fighting_item_strength': fighting_item_strength,
                    'winner': winner
                }
                
                confirmed_fights.append(fight_request)
                
                # Send updated state to requester
                requester_gamer = users[requester]
                response = {
                    'status': 'success',
                    'gamer_state': {
                        'username': requester_gamer['username'],
                        'lives': requester_gamer['lives'],
                        'sword': requester_gamer['sword'],
                        'shield': requester_gamer['shield'],
                        'slaying_potion': requester_gamer['slaying_potion'],
                        'healing_potion': requester_gamer['healing_potion']
                    },
                    'winner': winner
                }
                print(f'Fight completed. Winner: {winner}')
            
            serverSocket.sendto(json.dumps(response).encode(), clientAddress)
        
        # get all active gamers state
        elif action == 'get_all_active_gamers_state':
            username = data.get('username')
            print(f'Received request for all active gamers state from user {username}')
            
            active_gamers = []
            for uname, gamer in users.items():
                if is_active(gamer):
                    active_gamers.append({
                        'username': gamer['username'],
                        'lives': gamer['lives'],
                        'sword': gamer['sword'],
                        'shield': gamer['shield'],
                        'slaying_potion': gamer['slaying_potion'],
                        'healing_potion': gamer['healing_potion']
                    })
            
            response = {'status': 'success', 'gamers': active_gamers}
            print(f'Sent all active gamers state to user {username}')
            serverSocket.sendto(json.dumps(response).encode(), clientAddress)
            
    # simple error handling
    except json.JSONDecodeError:
        response = {'status': 'error', 'message': 'Invalid JSON'}
        serverSocket.sendto(json.dumps(response).encode(), clientAddress)
    except Exception as e:
        print(f'Error: {e}')
        response = {'status': 'error', 'message': str(e)}
        serverSocket.sendto(json.dumps(response).encode(), clientAddress)

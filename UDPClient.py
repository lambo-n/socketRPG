from socket import *
import json
import os
import socket as sock_module

# Client configuration
serverName = 'localhost'
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.settimeout(5.0)  # Set timeout for receiving responses

def send_request(action, data=None):
    """Send request to server and receive response"""
    if data is None:
        data = {}
    data['action'] = action
    message = json.dumps(data)
    clientSocket.sendto(message.encode(), (serverName, serverPort))
    
    try:
        response, serverAddress = clientSocket.recvfrom(4096)
        return json.loads(response.decode())
    except sock_module.timeout:
        print("Timeout: Server did not respond")
        return {'status': 'error', 'message': 'Timeout'}
    except json.JSONDecodeError:
        print("Error: Invalid response from server")
        return {'status': 'error', 'message': 'Invalid response'}

def display_gamer_state(gamer_state):
    """Display gamer state in a formatted way"""
    print("\n" + "="*50)
    print("YOUR GAMER STATE")
    print("="*50)
    print(f"Username: {gamer_state['username']}")
    print(f"Lives: {gamer_state['lives']}")
    
    sword = "unassigned" if gamer_state['sword'] == -1 else str(gamer_state['sword'])
    shield = "unassigned" if gamer_state['shield'] == -1 else str(gamer_state['shield'])
    slaying = "unassigned" if gamer_state['slaying_potion'] == -1 else str(gamer_state['slaying_potion'])
    healing = "unassigned" if gamer_state['healing_potion'] == -1 else str(gamer_state['healing_potion'])
    
    print(f"Sword: {sword}")
    print(f"Shield: {shield}")
    print(f"Slaying-potion: {slaying}")
    print(f"Healing-potion: {healing}")
    print("="*50 + "\n")

def display_fight_requests_table(fights):
    """Display confirmed fight requests as a structured table"""
    if not fights:
        print("\nNo confirmed fight requests yet.\n")
        return
    
    print("\n" + "="*80)
    print("CONFIRMED FIGHT REQUESTS")
    print("="*80)
    print(f"{'Requester':<12} {'Boss':<12} {'Fighting Item':<20} {'Strength':<12} {'Winner':<12}")
    print("-"*80)
    
    for fight in fights:
        requester = fight.get('requester', 'N/A')
        boss = fight.get('boss', 'N/A')
        fighting_item = fight.get('fighting_item', 'N/A').replace('_', '-')
        strength = str(fight.get('fighting_item_strength', 'N/A'))
        winner = fight.get('winner', 'N/A')
        
        print(f"{requester:<12} {boss:<12} {fighting_item:<20} {strength:<12} {winner:<12}")
    
    print("="*80 + "\n")

def display_active_gamers_table(gamers):
    """Display active gamers with their states as a structured table"""
    if not gamers:
        print("\nNo active gamers.\n")
        return
    
    print("\n" + "="*80)
    print("ACTIVE GAMERS")
    print("="*80)
    
    # Header
    print(f"{'Username':<12} {'Lives':<8} {'Sword':<8} {'Shield':<8} {'Slaying':<10} {'Healing':<10}")
    print("-"*80)
    
    for gamer in gamers:
        username = gamer.get('username', 'N/A')
        lives = str(gamer.get('lives', 'N/A'))
        sword = str(gamer.get('sword', 'N/A'))
        shield = str(gamer.get('shield', 'N/A'))
        slaying = str(gamer.get('slaying_potion', 'N/A'))
        healing = str(gamer.get('healing_potion', 'N/A'))
        
        print(f"{username:<12} {lives:<8} {sword:<8} {shield:<8} {slaying:<10} {healing:<10}")
    
    print("="*80 + "\n")
# validate strenght assignment
def validate_strength_assignment(sword, shield, slaying, healing):
    # check if all values are in range [0-3]
    if not all(0 <= val <= 3 for val in [sword, shield, slaying, healing]):
        return False, "All values must be in range [0-3]"
    
    # check if total is 10
    total = sword + shield + slaying + healing
    if total != 10:
        return False, f"Total strengths must be 10. Current total: {total}"
    
    return True, "Valid"

# handle user login
def login():
    while True:
        username = input("Enter username: ").strip()
        password = input("Enter password: ").strip()
        
        response = send_request('login', {'username': username, 'password': password})
        
        if response.get('status') == 'success':
            print(f"\nLogin successful! Welcome {username}!")
            return username, response.get('gamer_state')
        elif response.get('status') == 'game_over':
            print(f"\n{response.get('message', 'Game is over for this gamer')}")
            return None, None
        else:
            print(f"\nLogin failed: {response.get('message', 'Invalid credentials')}")
            choice = input("Choose an option:\n1. Try again\n2. Quit\nEnter choice (1 or 2): ").strip()
            if choice == '2':
                return None, None

# handle avatar upload
def upload_avatar(username):
    choice = input("\nDo you want to upload an avatar file? (y/n): ").strip().lower()
    if choice != 'y':
        return
    
    filename = input("Enter the name of the jpg file (must exist in current folder): ").strip()
    
    if not filename.endswith('.jpg'):
        filename += '.jpg'
    
    if not os.path.exists(filename):
        print(f"Error: File {filename} not found in current folder.")
        return
    
    try:
        with open(filename, 'rb') as f:
            avatar_data = f.read()
        
        # Convert to hex for JSON transmission
        avatar_hex = avatar_data.hex()
        
        response = send_request('upload_avatar', {
            'username': username,
            'avatar_data': avatar_hex,
            'filename': filename
        })
        
        if response.get('status') == 'success':
            print(f"Avatar uploaded successfully as {username}.jpg")
        else:
            print(f"Error uploading avatar: {response.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"Error reading file: {e}")

# handle first-time strength assignment
def assign_strengths():
    print("\nYou are given 10 strengths.")
    print("You need to assign them to your 4 properties (sword, shield, slaying-potion, healing-potion).")
    print("Each property can have a strength value in range [0-3].")
    print("The total of all 4 strengths must equal 10.\n")
    
    while True:
        try:
            sword = int(input("Enter sword strength [0-3]: "))
            shield = int(input("Enter shield strength [0-3]: "))
            slaying = int(input("Enter slaying-potion strength [0-3]: "))
            healing = int(input("Enter healing-potion strength [0-3]: "))
            
            is_valid, message = validate_strength_assignment(sword, shield, slaying, healing)
            
            if is_valid:
                return {
                    'sword': sword,
                    'shield': shield,
                    'slaying_potion': slaying,
                    'healing_potion': healing
                }
            else:
                print(f"\n{message}. Please try again.\n")
        except ValueError:
            print("\nInvalid input. Please enter numbers only.\n")

# main function
def main():
    print("="*60)
    print("WELCOME TO THE RPG GAME")
    print("="*60)
    
    #1- login
    username, gamer_state = login()
    if username is None:
        print("Goodbye!")
        clientSocket.close()
        return
    
    #2 - display gamer state
    display_gamer_state(gamer_state)
    
    #3 - upload avatar
    upload_avatar(username)
    
    #4 - first-time strength assignment if needed
    if gamer_state['sword'] == -1:
        print("\nThis is your first time playing the game.")
        new_state = assign_strengths()
        
        # Send state update to server
        response = send_request('update_state', {
            'username': username,
            'gamer_state': new_state
        })
        
        if response.get('status') == 'success':
            print("Strengths assigned successfully!")
            gamer_state.update(new_state)
            display_gamer_state(gamer_state)
    
    # main game loop
    while True:
        #5 - get list of active gamers
        choice = input("\nDo you want to get a list of other active gamers? (y/n): ").strip().lower()
        if choice != 'y':
            print("Goodbye!")
            break
        
        response = send_request('get_active_gamers', {'username': username})
        
        if response.get('status') == 'empty' or not response.get('gamers'):
            print("No other active gamers available. Game ending.")
            break
        
        active_gamers = response.get('gamers', [])
        print(f"\nActive gamers: {', '.join(active_gamers)}")
        
        #6- download avatar
        choice = input("\nDo you want to download another gamer's avatar? (y/n): ").strip().lower()
        if choice == 'y':
            target_username = input(f"Enter the username of the gamer whose avatar you want to download ({', '.join(active_gamers)}): ").strip()
            
            if target_username in active_gamers:
                response = send_request('download_avatar', {
                    'username': username,
                    'target_username': target_username
                })
                
                if response.get('status') == 'success':
                    avatar_hex = response.get('avatar_data')
                    filename = response.get('filename', f'{target_username}.jpg')
                    
                    try:
                        avatar_data = bytes.fromhex(avatar_hex)
                        with open(filename, 'wb') as f:
                            f.write(avatar_data)
                        print(f"Avatar downloaded successfully as {filename}")
                    except Exception as e:
                        print(f"Error saving avatar: {e}")
                else:
                    print(f"Error downloading avatar: {response.get('message', 'Unknown error')}")
            else:
                print("Invalid username.")
        
        # Step 7: View confirmed fight requests
        choice = input("\nDo you want to view confirmed fight requests? (y/n): ").strip().lower()
        if choice == 'y':
            response = send_request('get_confirmed_fights', {'username': username})
            if response.get('status') == 'success':
                display_fight_requests_table(response.get('fights', []))
        
        # Step 8: Send fight request
        while True:
            choice = input("Do you want to send a fight request? (y/n): ").strip().lower()
            if choice != 'y':
                break
            
            print(f"\nAvailable gamers to fight: {', '.join(active_gamers)}")
            boss = input("Enter the username of the gamer you want to fight: ").strip()
            
            if boss not in active_gamers:
                print("Invalid username. Please try again.")
                continue
            
            print("\nChoose fighting item:")
            print("1. Sword")
            print("2. Slaying-potion")
            item_choice = input("Enter choice (1 or 2): ").strip()
            
            if item_choice == '1':
                fighting_item = 'sword'
            elif item_choice == '2':
                fighting_item = 'slaying_potion'
            else:
                print("Invalid choice.")
                continue
            
            try:
                strength = int(input("Enter the strength you want to use [0-3]: "))
                if not (0 <= strength <= 3):
                    print("Strength must be in range [0-3].")
                    continue
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue
            
            # Get current state to check if user has enough strength
            current_state = gamer_state
            if fighting_item == 'sword' and current_state['sword'] < strength:
                print(f"Error: You don't have enough sword strength. Your current sword strength is {current_state['sword']}.")
                continue
            elif fighting_item == 'slaying_potion' and current_state['slaying_potion'] < strength:
                print(f"Error: You don't have enough slaying-potion strength. Your current slaying-potion strength is {current_state['slaying_potion']}.")
                continue
            
            response = send_request('send_fight_request', {
                'requester': username,
                'boss': boss,
                'fighting_item': fighting_item,
                'fighting_item_strength': strength
            })
            
            if response.get('status') == 'success':
                print("\nFight request confirmed!")
                winner = response.get('winner', 'none')
                if winner == 'requester':
                    print(f"You won! You gained 1 life.")
                elif winner == 'boss':
                    print(f"You lost! You lost 1 life.")
                else:
                    print("It's a tie! Both lost 1 life.")
                
                # Update gamer state
                gamer_state = response.get('gamer_state', gamer_state)
                display_gamer_state(gamer_state)
                
                # Check if game over
                if gamer_state['lives'] == 0:
                    print("Game over! You have no lives left.")
                    break
            else:
                print(f"Error: {response.get('message', 'Unknown error')}")
            
            choice = input("\nDo you want to send a new fight request? (y/n): ").strip().lower()
            if choice != 'y':
                break
        
        # Step 9: Get all active gamers state
        choice = input("\nDo you want to get a list of all active gamers and their current state? (y/n): ").strip().lower()
        if choice == 'y':
            response = send_request('get_all_active_gamers_state', {'username': username})
            if response.get('status') == 'success':
                display_active_gamers_table(response.get('gamers', []))
        
        print("\nGame ending. Goodbye!")
        break
    
    clientSocket.close()

if __name__ == '__main__':
    main()

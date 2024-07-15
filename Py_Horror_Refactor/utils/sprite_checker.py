import os

def check_sprite_existence():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    sprites_dir = os.path.join(project_root, 'assets', 'sprites')
    
    sprite_files = [
        'player.png', 'zombie.png', 'tracker.png', 'bat.png', 'boss.png',
        'coin.png', 'house1.png', 'house2.png', 'house3.png', 'house4.png', 'house5.png',
        'mansion.png', 'dirt_road.png', 'grass.png', 'floor.png',
        'table.png', 'chair.png', 'bookshelf.png', 'bed.png', 'cabinet.png',
        'headstone.png', 'graveyard_floor.png', 'graveyard_entrance.png'
    ]
    
    print(f"Checking for sprite files in: {sprites_dir}")
    for file in sprite_files:
        path = os.path.join(sprites_dir, file)
        if os.path.exists(path):
            print(f"Found: {file}")
        else:
            print(f"Missing: {file}")

if __name__ == "__main__":
    check_sprite_existence()
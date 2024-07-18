import pygame
from game import Game

def main():
    pygame.init()
    print(f"Pygame initialized. Display driver: {pygame.display.get_driver()}")
    print(f"Pygame version: {pygame.version.ver}")
    
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
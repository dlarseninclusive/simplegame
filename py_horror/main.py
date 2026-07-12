# horror_game was previously named game.py; renamed because it shadowed the
# wrapper's `game` package when this directory is on sys.path.
from horror_game import Game

def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
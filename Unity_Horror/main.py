import pygame
from settings import WIDTH, HEIGHT
from game_state import GameState

def main():
    # Initialize Pygame
    pygame.init()
    
    # Fonts
    font = pygame.font.Font(None, 36)
    dialog_font = pygame.font.Font(None, 24)
    
    clock = pygame.time.Clock()
    game_state = GameState(font, dialog_font)
    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    game_state.switch_character()
                elif event.key == pygame.K_r:
                    game_state = GameState(font, dialog_font)
                elif event.key == pygame.K_e:
                    if not game_state.dialog_active:
                        for door in game_state.scenes[game_state.scene]["doors"]:
                            if game_state.get_active_character().rect.colliderect(door.rect):
                                game_state.change_scene(door.target_scene)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if game_state.dialog_active and game_state.exit_button_rect and game_state.exit_button_rect.collidepoint(event.pos):
                        game_state.handle_dialog_exit()
                    elif game_state.dialog_active and game_state.continue_button_rect and game_state.continue_button_rect.collidepoint(event.pos):
                        game_state.handle_dialog_continue()
                    elif not game_state.dialog_active:
                        active_character = game_state.get_active_character()
                        active_character.target_pos = (mouse_pos[0] + game_state.camera.camera.x, mouse_pos[1] + game_state.camera.camera.y)

        game_state.update()
        game_state.draw(game_state.screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()

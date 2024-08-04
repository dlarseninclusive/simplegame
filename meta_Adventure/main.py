import pygame
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *

# Initialize Pygame
pygame.init()

# Set up some constants
WIDTH, HEIGHT = 640, 480

# Set up the display
pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL|pygame.DOUBLEBUF)

# Set up the player
player = [0, 0, 0]

# Set up the enemies
enemies = [[1, 1, 1], [2, 2, 2]]

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Move the player
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        player[2] += 0.1
    if keys[pygame.K_DOWN]:
        player[2] -= 0.1
    if keys[pygame.K_LEFT]:
        player[0] -= 0.1
    if keys[pygame.K_RIGHT]:
        player[0] += 0.1

    # Check for collisions with enemies
    for enemy in enemies:
        if player[0] == enemy[0] and player[2] == enemy[2]:
            print("Fight!")

    # Draw everything
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(player[0], player[1], player[2], 0, 0, 0, 0, 1, 0)

    # Draw the player
    glPushMatrix()
    glTranslatef(player[0], player[1], player[2])
    glRotatef(90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 0.5, 0.5, 1, 10, 10)
    glPopMatrix()

    # Draw the enemies
    for enemy in enemies:
        glPushMatrix()
        glTranslatef(enemy[0], enemy[1], enemy[2])
        glRotatef(90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), 0.5, 0.5, 1, 10, 10)
        glPopMatrix()

    # Update the display
    pygame.display.flip()

    # Cap the frame rate
    pygame.time.Clock().tick(60)
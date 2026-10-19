import pygame

pygame.init()
screen = pygame.display.set_mode((1000, 700))
font = pygame.font.Font(None, 24)
label = font.render("Hub A", True, (220, 225, 235))
running = True
clock = pygame.time.Clock()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill((22, 22, 32))
    pygame.draw.circle(screen, (80, 160, 220), (500, 350), 20)
    screen.blit(label, (475, 380))
    pygame.display.flip()
    clock.tick(60)
pygame.quit()

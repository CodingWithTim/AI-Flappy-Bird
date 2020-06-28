
import pygame
import neat
import os
import random
import time

# global values
WIDTH = 600
HEIGHT = 800

WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AI Plays Flappy Bird")

CLOCK = pygame.time.Clock()

pipe_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")).convert_alpha())
bg_img = pygame.transform.scale(pygame.image.load(os.path.join("imgs","bg.png")).convert_alpha(), (600, 900))
bird_images = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird" + str(x) + ".png"))) for x in range(1,4)]
base_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")).convert_alpha())

PIPE_WIDTH = pipe_img.get_width()
PIPE_GAP = 180
BASE_Y = HEIGHT - base_img.get_height() + 100

class Bird:
    IMGS = bird_images

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vel_y = 0
        self.tick = 0

        self.rotation = 0
        self.counter = 0

        self.img_index = 0
        self.img = self.IMGS[0]

    def move(self):

        self.tick += 1

        # for downward acceleration
        displacement = self.vel_y * (self.tick) + 0.5 * (3) * (self.tick) ** 3  # calculate displacement

        # terminal velocity
        if displacement >= 30:
            displacement = (displacement / abs(displacement)) * 30

        if displacement < 0:
            displacement -= 2

        self.y = self.y + displacement

        if displacement < 0:
            self.rotation = 25
        else:
            if self.rotation > -90:
                self.rotation -= 20

    def pipe_collision(self, pipes):
        for pipe in pipes:

            xPos = int(self.x + self.img.get_width())
            yPos = int(self.y + self.img.get_height())

            if xPos >= pipe.x and xPos <= pipe.x + PIPE_GAP:
                # check top pipe
                if self.y <= pipe.y1:
                    return True
                #check lower pipe
                if yPos >= pipe.y2:
                    return True

        return False

    def top_collision(self):
        if self.y <= 0:
            return True
        return False

    def base_collision(self):
        if self.y >= BASE_Y:
            return True
        return False

    def jump(self):
        self.vel_y = -20
        self.tick = 0

    def draw(self):
        self.img_index += 1

        if self.img_index <= 5:
            self.img = self.IMGS[0]
        elif self.img_index <= 10:
            self.img = self.IMGS[1]
        elif self.img_index <= 15:
            self.img = self.IMGS[2]
        elif self.img_index <= 20:
            self.img = self.IMGS[1]
        else:
            self.img = self.IMGS[0]
            self.img_index = 0

        blitRotateCenter(WINDOW, self.img, (self.x, self.y), self.rotation)
        # pygame.draw.circle(WINDOW, self.color, (int(self.x), int(self.y)), int(self.radius))


class Pipe:

    def __init__(self):
        self.x = WIDTH + 100
        self.y1 = random.randint(70, 420)
        self.y2 = self.y1 + PIPE_GAP

        self.UPPER_PIPE = pygame.transform.flip(pipe_img, False, True)
        self.LOWER_PIPE = pipe_img

    def move(self):
        self.x -= 20

    def draw(self):
        #draw top pipe
        WINDOW.blit(self.UPPER_PIPE, (self.x, self.y1 - self.UPPER_PIPE.get_height()))
        # pygame.draw.rect(WINDOW, self.color, (self.x, 0, PIPE_WIDTH, self.y1), 0)

        #draw lower pipe
        WINDOW.blit(self.LOWER_PIPE, (self.x, self.y2))
        # pygame.draw.rect(WINDOW, self.color, (self.x, self.y2, PIPE_WIDTH, HEIGHT - self.y2), 0)

    def disappear(self):
        if self.x < 0:
            return True
        return False






def update(birds, pipes, nets, genomes, current_pipe):

    for index, bird in enumerate(birds):

        bird.move()

        distance_to_top = abs(bird.y - pipes[current_pipe].y1)
        distance_to_lower = abs(bird.y - pipes[current_pipe].y2)

        output = nets[index].activate((bird.y, distance_to_top, distance_to_lower))

        # using tanh: if greater than 0.5 then jump
        if output[0] > 0.5:
            bird.jump()

    for pipe in pipes:
        pipe.move()

    if pipes[0].disappear == True:
        del pipes[0]

def blitRotateCenter(surf, image, topleft, angle):
    """
    Rotate a surface and blit it to the window
    :param surf: the surface to blit to
    :param image: the image surface to rotate
    :param topLeft: the top left position of the image
    :param angle: a float value for angle
    :return: None
    """
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center = image.get_rect(topleft = topleft).center)

    surf.blit(rotated_image, new_rect.topleft)

def draw_screen(birds, pipes, base_x):
    WINDOW.blit(bg_img, (0, 0))

    for bird in birds:
        bird.draw()

    for pipe in pipes:
        pipe.draw()

    WINDOW.blit(base_img, (base_x, BASE_Y))
    WINDOW.blit(base_img, (base_x + WIDTH, BASE_Y))

    pygame.display.update()

def main(genomes, config):
    birds = []
    neural_networks = []
    birds_genomes = []
    pipes = []
    pipes_passed = 0

    for id, genome in genomes:
        genome.fitness = 0
        neural_network = neat.nn.FeedForwardNetwork.create(genome, config)
        neural_networks.append(neural_network)
        birds.append(Bird(300, HEIGHT / 2))
        birds_genomes.append(genome)

    pipes.append(Pipe())
    counter = 0
    base_x = 0
    finished = False

    while not finished:
        CLOCK.tick(60)
        pygame.time.wait(10)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                finished = True
                pygame.quit()
                quit()
                break


        update(birds, pipes, neural_networks, birds_genomes, pipes_passed)

        if counter >= 25:
            pipes.append(Pipe())
            counter = 0

        if base_x <= -WIDTH:
            base_x = 0

        draw_screen(birds, pipes, base_x)

        base_x -= 20

        #manage bird deaths
        for bird in birds:
            if bird.pipe_collision(pipes) or bird.base_collision():
                del neural_networks[birds.index(bird)]
                del birds_genomes[birds.index(bird)]
                del birds[birds.index(bird)]
            else:
                birds_genomes[birds.index(bird)].fitness += 0.1

        if len(birds) <= 0:
            finished = True

        # give rewards
        passed = False
        for bird in birds:
            if bird.x > pipes[pipes_passed].x + PIPE_WIDTH:
                birds_genomes[birds.index(bird)].fitness += 5
                passed = True

        if passed and pipes_passed < (len(pipes) - 1):
            pipes_passed += 1

        counter += 1

def run(config_file):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_file)

    p = neat.Population(config)

    p.add_reporter(neat.StdOutReporter(True))
    p.add_reporter(neat.StatisticsReporter())

    winner = p.run(main, 50)

    # show final stats
    print('\nBest genome:\n{!s}'.format(winner))

    pygame.quit()
    quit()

if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)
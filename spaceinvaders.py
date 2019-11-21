#!/usr/bin/env python

# Space Invaders - 2-Playered
# Adapted by Simon Mendelsohn (from code by Lee Robinson)

from pygame import *
import sys
from os.path import abspath, dirname
import random

# Paths
BASE_PATH = abspath(dirname(__file__))
FONT_PATH = BASE_PATH + '/fonts/'
IMAGE_PATH = BASE_PATH + '/images/'
SOUND_PATH = BASE_PATH + '/sounds/'

# Colors (R, G, B)
WHITE = (255, 255, 255)
GREEN = (78, 255, 87)
YELLOW = (241, 255, 0)
BLUE = (80, 255, 239)
PURPLE = (203, 0, 255)
RED = (237, 28, 36)

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
SCREEN = display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
FONT = FONT_PATH + 'space_invaders.ttf'
IMG_NAMES = ['ship', 'other', 'mystery',
             'enemy1_1', 'enemy1_2',
             'enemy2_1', 'enemy2_2',
             'enemy3_1', 'enemy3_2',
             'explosionblue', 'explosiongreen', 'explosionpurple',
             'laser', 'enemylaser']
IMAGES = {name: image.load(IMAGE_PATH + '{}.png'.format(name)).convert_alpha() for name in IMG_NAMES}

BLOCKERS_POSITION = 450
ENEMY_DEFAULT_POSITION = 65
ENEMY_MOVE_DOWN = 35


class Ship(sprite.Sprite):
    def __init__(self, human=True):
        sprite.Sprite.__init__(self)
        self.human = human
        self.image = IMAGES['ship']
        self.direction = -1
        if not human:
            self.image = IMAGES['other']
        if self.human:
            self.rect = self.image.get_rect(topleft=(200, 540))
        else:
            self.rect = self.image.get_rect(topleft=(600, 540))
        self.speed = 5

    def update(self, keys, *args):
        left, right = K_LEFT, K_RIGHT
        if not self.human:
            left, right = K_a, K_d
        if keys[left] and self.rect.x > 10:
            self.rect.x -= self.speed
        if keys[right] and self.rect.x < 740:
            self.rect.x += self.speed
        game.screen.blit(self.image, self.rect)


class Bullet(sprite.Sprite):
    def __init__(self, xpos, ypos, direction, speed, filename, side):
        sprite.Sprite.__init__(self)
        self.image = IMAGES[filename]
        self.rect = self.image.get_rect(topleft=(xpos, ypos))
        self.speed = speed
        self.direction = direction

    def update(self, keys, *args):
        game.screen.blit(self.image, self.rect)
        self.rect.y += self.speed * self.direction
        if self.rect.y < 15 or self.rect.y > 600:
            self.kill()


class Enemy(sprite.Sprite):
    def __init__(self, row, column):
        sprite.Sprite.__init__(self)
        self.row = row
        self.column = column
        self.images = []
        self.load_images()
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()

    def toggle_image(self):
        self.index += 1
        if self.index >= len(self.images):
            self.index = 0
        self.image = self.images[self.index]

    def update(self, *args):
        game.screen.blit(self.image, self.rect)

    def load_images(self):
        images = {0: ['1_2', '1_1'],
                  1: ['2_2', '2_1'],
                  2: ['2_2', '2_1'],
                  3: ['3_1', '3_2'],
                  4: ['3_1', '3_2'],
                  }
        img1, img2 = (IMAGES['enemy{}'.format(img_num)] for img_num in images[self.row])
        self.images.append(transform.scale(img1, (40, 35)))
        self.images.append(transform.scale(img2, (40, 35)))


class EnemiesGroup(sprite.Group):
    def __init__(self, columns, rows):
        sprite.Group.__init__(self)
        self.enemies = [[None] * columns for _ in range(rows)]
        self.columns = columns
        self.rows = rows
        # self.leftAddMove = 0
        '''
        could be used to make the enemies go all the way across if a column is destroyed; 
        see original code if you want to re-implement (there would be other changes below)
        '''
        # self.rightAddMove = 0
        self.moveTime = 600
        self.direction = 1
        self.moves = 15  # number of moves before turning
        self.moveNumber = 0  # number of moves done already
        self.timer = time.get_ticks()
        self.bottom = game.enemyPosition + ((rows - 1) * 45) + 35
        self._aliveColumns = list(range(columns))
        self.leftAliveColumn = 0
        self.rightAliveColumn = columns - 1

    def update(self, current_time):
        if current_time - self.timer > self.moveTime:
            if self.moveNumber >= self.moves:
                self.direction *= -1
                self.moveNumber = 0
                self.bottom = 0
                for enemy in self:
                    enemy.rect.y += ENEMY_MOVE_DOWN
                    enemy.toggle_image()
                    if self.bottom < enemy.rect.y + 35:
                        self.bottom = enemy.rect.y + 35
            else:
                for enemy in self:
                    enemy.rect.x += (10 * self.direction)
                    enemy.toggle_image()
                self.moveNumber += 1

            self.timer += self.moveTime

    def add_internal(self, *sprites):
        super(EnemiesGroup, self).add_internal(*sprites)
        for s in sprites:
            self.enemies[s.row][s.column] = s

    def remove_internal(self, *sprites):
        super(EnemiesGroup, self).remove_internal(*sprites)
        for s in sprites:
            self.kill(s)
        self.update_speed()

    def is_column_dead(self, column):
        return not any(self.enemies[row][column]
                       for row in range(self.rows))

    def random_bottom(self):
        col = random.choice(self._aliveColumns)
        col_enemies = (self.enemies[row - 1][col]
                       for row in range(self.rows, 0, -1))
        return next((en for en in col_enemies if en is not None), None)

    def update_speed(self):
        if len(self) == 1:
            self.moveTime = 200
        elif len(self) <= 10:
            self.moveTime = 400

    def kill(self, enemy):
        self.enemies[enemy.row][enemy.column] = None
        is_column_dead = self.is_column_dead(enemy.column)
        if is_column_dead:
            self._aliveColumns.remove(enemy.column)

        if enemy.column == self.rightAliveColumn:
            while self.rightAliveColumn > 0 and is_column_dead:
                self.rightAliveColumn -= 1
                # self.rightAddMove += 5
                is_column_dead = self.is_column_dead(self.rightAliveColumn)

        elif enemy.column == self.leftAliveColumn:
            while self.leftAliveColumn < self.columns and is_column_dead:
                self.leftAliveColumn += 1
                # self.leftAddMove += 5
                is_column_dead = self.is_column_dead(self.leftAliveColumn)


class Blocker(sprite.Sprite):
    def __init__(self, size, color, row, column):
        sprite.Sprite.__init__(self)
        self.height = size
        self.width = size
        self.color = color
        self.image = Surface((self.width, self.height))
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.row = row
        self.column = column

    def update(self, keys, *args):
        game.screen.blit(self.image, self.rect)


class Mystery(sprite.Sprite):
    def __init__(self):
        sprite.Sprite.__init__(self)
        self.image = IMAGES['mystery']
        self.image = transform.scale(self.image, (75, 35))
        self.rect = self.image.get_rect(topleft=(-80, 45))
        self.row = 5
        self.moveTime = 25000
        self.direction = 1
        self.timer = time.get_ticks()
        self.mysteryEntered = mixer.Sound(SOUND_PATH + 'mysteryentered.wav')
        self.mysteryEntered.set_volume(0.3)
        self.playSound = True

    def update(self, keys, currentTime, *args):
        resetTimer = False
        passed = currentTime - self.timer
        if passed > self.moveTime:
            if (self.rect.x < 0 or self.rect.x > 800) and self.playSound:
                self.mysteryEntered.play()
                self.playSound = False
            if self.rect.x < 840 and self.direction == 1:
                self.mysteryEntered.fadeout(4000)
                self.rect.x += 2
                game.screen.blit(self.image, self.rect)
            if self.rect.x > -100 and self.direction == -1:
                self.mysteryEntered.fadeout(4000)
                self.rect.x -= 2
                game.screen.blit(self.image, self.rect)

        if self.rect.x > 830:
            self.playSound = True
            self.direction = -1
            resetTimer = True
        if self.rect.x < -90:
            self.playSound = True
            self.direction = 1
            resetTimer = True
        if passed > self.moveTime and resetTimer:
            self.timer = currentTime


class EnemyExplosion(sprite.Sprite):
    def __init__(self, enemy, *groups):
        super(EnemyExplosion, self).__init__(*groups)
        self.image = transform.scale(self.get_image(enemy.row), (40, 35))
        self.image2 = transform.scale(self.get_image(enemy.row), (50, 45))
        self.rect = self.image.get_rect(topleft=(enemy.rect.x, enemy.rect.y))
        self.timer = time.get_ticks()

    @staticmethod
    def get_image(row):
        img_colors = ['purple', 'blue', 'blue', 'green', 'green']
        return IMAGES['explosion{}'.format(img_colors[row])]

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if passed <= 100:
            game.screen.blit(self.image, self.rect)
        elif passed <= 200:
            game.screen.blit(self.image2, (self.rect.x - 6, self.rect.y - 6))
        elif 400 < passed:
            self.kill()


class MysteryExplosion(sprite.Sprite):
    def __init__(self, mystery, score, *groups):
        super(MysteryExplosion, self).__init__(*groups)
        self.text = Text(FONT, 20, str(score), WHITE,
                         mystery.rect.x + 20, mystery.rect.y + 6)
        self.timer = time.get_ticks()

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if passed <= 200 or 400 < passed <= 600:
            self.text.draw(game.screen)
        elif 600 < passed:
            self.kill()


class ShipExplosion(sprite.Sprite):
    def __init__(self, ship, *groups):
        super(ShipExplosion, self).__init__(*groups)
        self.image = IMAGES['ship']
        self.rect = self.image.get_rect(topleft=(ship.rect.x, ship.rect.y))
        self.timer = time.get_ticks()

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if 300 < passed <= 600:
            game.screen.blit(self.image, self.rect)
        elif 900 < passed:
            self.kill()


class Life(sprite.Sprite):
    def __init__(self, xpos, ypos):
        sprite.Sprite.__init__(self)
        self.image = IMAGES['ship']
        self.image = transform.scale(self.image, (23, 23))
        self.rect = self.image.get_rect(topleft=(xpos, ypos))

    def update(self, *args):
        game.screen.blit(self.image, self.rect)


class Text(object):
    def __init__(self, textFont, size, message, color, xpos, ypos):
        self.font = font.Font(textFont, size)
        self.surface = self.font.render(message, True, color)
        self.rect = self.surface.get_rect(topleft=(xpos, ypos))

    def draw(self, surface):
        surface.blit(self.surface, self.rect)

def updateAI(ai, enemies, enemyBullets, cooperate):
    rightEnemy = leftEnemy = 0
    for enemy in enemies:
        if enemy.rect.x > rightEnemy:
            rightEnemy = enemy.rect.x
        if enemy.rect.x < leftEnemy:
            leftEnemy = enemy.rect.x

    leftWall = 10
    if not cooperate:
        leftWall = 410

    # dodge
    moveLeft = moveRight = True
    hit = False
    for bullet in enemyBullets:
        if bullet.rect.y < 300:
            continue
        diff = bullet.rect.x - ai.rect.x
        if (diff > -30 and diff < -1):
            moveLeft = False
        if diff >= -1 and diff <= 50:
            hit = True
        if (diff > 50 and diff < 80):
            moveRight = False

    if ai.rect.x < 10:
        ai.direction = 1
    elif ai.rect.x > 740:
        ai.direction = -1

    if moveLeft and moveRight and hit:
        ai.rect.x += ai.direction * ai.speed
    elif ai.rect.x > 10 and moveLeft and hit:
        ai.rect.x -= ai.speed
    elif ai.rect.x < 740 and moveRight and hit:
        ai.rect.x += ai.speed
    elif ai.rect.x > rightEnemy and moveLeft and ai.rect.x > leftWall:
        ai.rect.x -= ai.speed
    elif ai.rect.x < rightEnemy - 10 and moveRight:
        ai.rect.x += ai.speed



class SpaceInvaders(object):
    def __init__(self):
        # It seems, in Linux buffersize=512 is not enough, use 4096 to prevent:
        #   ALSA lib pcm.c:7963:(snd_pcm_recover) underrun occurred
        mixer.pre_init(44100, -16, 1, 4096)  # for audio I think
        init()  # pygame.init()
        self.clock = time.Clock()
        self.caption = display.set_caption('Space Invaders')
        self.screen = SCREEN
        self.background = image.load(IMAGE_PATH + 'background.jpg').convert()
        self.startGame = False
        self.mainScreen = True
        self.gameOver = False
        # Counter for enemy starting position (increased each new round)
        self.enemyPosition = ENEMY_DEFAULT_POSITION
        self.titleText = Text(FONT, 50, 'Space Invaders', WHITE, 164, 155)
        self.titleText2 = Text(FONT, 25, 'Press any key to continue', WHITE,
                               201, 225)
        #self.gameOverText = Text(FONT, 50, 'Game Over', WHITE, 250, 270)
        self.nextRoundText = Text(FONT, 50, 'Next Round', WHITE, 240, 270)
        self.enemy1Text = Text(FONT, 25, '   =   10 pts', GREEN, 368, 270)
        self.enemy2Text = Text(FONT, 25, '   =  20 pts', BLUE, 368, 320)
        self.enemy3Text = Text(FONT, 25, '   =  30 pts', PURPLE, 368, 370)
        self.enemy4Text = Text(FONT, 25, '   =  ?????', RED, 368, 420)
        self.scoreText = Text(FONT, 20, 'Score', WHITE, 5, 5)
        self.scoreTextO = Text(FONT, 20, 'Score', WHITE, 405, 5)

        self.livesTextPlayer = Text(FONT, 20, 'Lives ', WHITE, 240, 5)
        self.lifePlayer1 = Life(315, 3)
        self.lifePlayer2 = Life(342, 3)
        self.lifePlayer3 = Life(369, 3)

        self.livesTextOther = Text(FONT, 20, 'Lives ', WHITE, 640, 5)
        self.lifeOther1 = Life(715, 3)
        self.lifeOther2 = Life(742, 3)
        self.lifeOther3 = Life(769, 3)
        self.livesGroup = sprite.Group(self.lifePlayer1, self.lifePlayer2, self.lifePlayer3, self.lifeOther1, self.lifeOther2, self.lifeOther3)

    def reset(self, player_score, other_score):
        self.player = Ship(True)
        self.other = Ship(False)
        self.playerGroup = sprite.Group(self.player, self.other)
        self.explosionsGroup = sprite.Group()
        self.bullets = sprite.Group()
        self.mysteryShip = Mystery()
        self.mysteryGroup = sprite.Group(self.mysteryShip)
        self.enemyBullets = sprite.Group()
        self.make_enemies()
        self.allSprites = sprite.Group(self.player, self.enemies,
                                       self.livesGroup, self.mysteryShip, self.other)
        self.keys = key.get_pressed()

        self.timer = time.get_ticks()
        self.noteTimer = time.get_ticks()
        self.shipTimer = time.get_ticks()
        self.player_score = player_score
        self.other_score = other_score
        self.create_audio()
        self.makeNewPlayer = False
        self.makeNewOther = False

    def make_blockers(self, number):
        blockerGroup = sprite.Group()
        for row in range(4):
            for column in range(9):
                blocker = Blocker(10, GREEN, row, column)
                blocker.rect.x = 50 + (200 * number) + (column * blocker.width)
                blocker.rect.y = BLOCKERS_POSITION + (row * blocker.height)
                blockerGroup.add(blocker)
        return blockerGroup

    def create_audio(self):
        self.sounds = {}
        for sound_name in ['shoot', 'shoot2', 'invaderkilled', 'mysterykilled',
                           'shipexplosion']:
            self.sounds[sound_name] = mixer.Sound(
                SOUND_PATH + '{}.wav'.format(sound_name))
            self.sounds[sound_name].set_volume(0.2)

        self.musicNotes = [mixer.Sound(SOUND_PATH + '{}.wav'.format(i)) for i
                           in range(4)]
        for sound in self.musicNotes:
            sound.set_volume(0.5)

        self.noteIndex = 0

    def play_main_music(self, currentTime):
        if currentTime - self.noteTimer > self.enemies.moveTime:
            self.note = self.musicNotes[self.noteIndex]
            if self.noteIndex < 3:
                self.noteIndex += 1
            else:
                self.noteIndex = 0

            self.note.play()
            self.noteTimer += self.enemies.moveTime

    @staticmethod
    def should_exit(evt):
        # type: (pygame.event.EventType) -> bool
        return evt.type == QUIT or (evt.type == KEYUP and evt.key == K_ESCAPE)

    def check_input(self):

        if self.lifeOther1.alive():
            if len(self.bullets) == 0:
                bullet = Bullet(self.other.rect.x + 23,
                                self.other.rect.y + 5, -1,
                                15, 'laser', 'center')
                self.bullets.add(bullet)
                self.allSprites.add(self.bullets)
                self.sounds['shoot'].play()

        self.keys = key.get_pressed()
        for e in event.get():
            if self.should_exit(e):
                sys.exit()
            if e.type == KEYDOWN:
                if e.key == K_SPACE and self.lifePlayer1.alive():
                    if len(self.bullets) < 2:
                        bullet = Bullet(self.player.rect.x + 23,
                                        self.player.rect.y + 5, -1,
                                        15, 'laser', 'center')
                        #self.myBullets.add(bullet)
                        self.bullets.add(bullet)
                        self.allSprites.add(self.bullets)
                        self.sounds['shoot'].play()

    def make_enemies(self):
        enemies = EnemiesGroup(10, 5)
        for row in range(5):
            for column in range(5):
                enemy = Enemy(row, column)
                enemy.rect.x = (column * 50)
                enemy.rect.y = self.enemyPosition + (row * 45)
                enemies.add(enemy)

            for column in range(5,10):
                enemy = Enemy(row, column)
                enemy.rect.x = 400 + ((column - 5) * 50)
                enemy.rect.y = self.enemyPosition + (row * 45)
                enemies.add(enemy)

        self.enemies = enemies

    def make_enemies_shoot(self):
        if (time.get_ticks() - self.timer) > 700 and self.enemies:
            enemy = self.enemies.random_bottom()
            self.enemyBullets.add(
                Bullet(enemy.rect.x + 14, enemy.rect.y + 20, 1, 5,
                       'enemylaser', 'center'))
            self.allSprites.add(self.enemyBullets)
            self.timer = time.get_ticks()

    def calculate_score(self, row, column):
        scores = {0: 30,
                  1: 20,
                  2: 20,
                  3: 10,
                  4: 10,
                  5: random.choice([50, 100, 150, 300])
                  }

        score = scores[row]
        if row == 5:
            column = column // 80
        if column < 5:
            self.player_score += score
        else:
            self.other_score += score
        return score

    def create_main_menu(self):
        self.enemy1 = IMAGES['enemy3_1']
        self.enemy1 = transform.scale(self.enemy1, (40, 40))
        self.enemy2 = IMAGES['enemy2_2']
        self.enemy2 = transform.scale(self.enemy2, (40, 40))
        self.enemy3 = IMAGES['enemy1_2']
        self.enemy3 = transform.scale(self.enemy3, (40, 40))
        self.enemy4 = IMAGES['mystery']
        self.enemy4 = transform.scale(self.enemy4, (80, 40))
        self.screen.blit(self.enemy1, (318, 270))
        self.screen.blit(self.enemy2, (318, 320))
        self.screen.blit(self.enemy3, (318, 370))
        self.screen.blit(self.enemy4, (299, 420))

    def check_collisions(self):
        sprite.groupcollide(self.bullets, self.enemyBullets, True, True)

        for enemy in sprite.groupcollide(self.enemies, self.bullets,
                                         True, True).keys():
            self.sounds['invaderkilled'].play()
            self.calculate_score(enemy.row, enemy.column)
            EnemyExplosion(enemy, self.explosionsGroup)
            self.gameTimer = time.get_ticks()

        for mystery in sprite.groupcollide(self.mysteryGroup, self.bullets,
                                           True, True).keys():
            mystery.mysteryEntered.stop()
            self.sounds['mysterykilled'].play()
            score = self.calculate_score(mystery.row, mystery.rect.x)
            MysteryExplosion(mystery, score, self.explosionsGroup)
            newShip = Mystery()
            self.allSprites.add(newShip)
            self.mysteryGroup.add(newShip)

        for player in sprite.groupcollide(self.playerGroup, self.enemyBullets,
                                          True, True).keys():
            if player.human:
                if self.lifePlayer3.alive():
                    self.lifePlayer3.kill()
                elif self.lifePlayer2.alive():
                    self.lifePlayer2.kill()
                elif self.lifePlayer1.alive():
                    self.lifePlayer1.kill()
                    if not self.lifeOther1.alive():
                        self.gameOver = True
                        self.startGame = False
            else:
                if self.lifeOther3.alive():
                    self.lifeOther3.kill()
                elif self.lifeOther2.alive():
                    self.lifeOther2.kill()
                elif self.lifeOther1.alive():
                    self.lifeOther1.kill()
                    if not self.lifePlayer1.alive():
                        self.gameOver = True
                        self.startGame = False

            self.sounds['shipexplosion'].play()
            ShipExplosion(player, self.explosionsGroup)
            if player.human and self.lifePlayer1.alive():
                self.makeNewPlayer = True
            elif not player.human and self.lifeOther1.alive():
                self.makeNewOther = True
            self.shipTimer = time.get_ticks()

        if self.enemies.bottom >= 540:
            for player in sprite.groupcollide(self.playerGroup, self.enemies, True, True).keys():
                if player.human:
                    self.lifePlayer3.kill()
                    self.lifePlayer2.kill()
                    self.lifePlayer1.kill()
                else:
                    self.lifeOther3.kill()
                    self.lifeOther2.kill()
                    self.lifeOther1.kill()

            if self.enemies.bottom >= 600:
                #print(self.enemies.bottom)
                if self.enemies.leftAliveColumn < 5:
                    self.player.kill()
                    self.lifePlayer3.kill()
                    self.lifePlayer2.kill()
                    self.lifePlayer1.kill()
                if self.enemies.rightAliveColumn >= 5:
                    self.other.kill()
                    self.lifeOther3.kill()
                    self.lifeOther2.kill()
                    self.lifeOther1.kill()

            if (not self.player.alive() and not self.other.alive()):
                self.gameOver = True
                self.startGame = False

        # sprite.groupcollide(self.bullets, self.allBlockers, True, True)
        # sprite.groupcollide(self.enemyBullets, self.allBlockers, True, True)
        # if self.enemies.bottom >= BLOCKERS_POSITION:
        #     sprite.groupcollide(self.enemies, self.allBlockers, False, True)

    def create_new_ship(self, createShip, currentTime, human):
        if createShip and (currentTime - self.shipTimer > 900):
            if human:
                self.player = Ship(human)
                self.allSprites.add(self.player)
                self.playerGroup.add(self.player)
                self.makeNewPlayer = False
            else:
                self.other = Ship(human)
                self.allSprites.add(self.other)
                self.playerGroup.add(self.other)
                self.makeNewOther = False

    def create_game_over(self, currentTime, win=False):
        self.screen.blit(self.background, (0, 0))
        passed = currentTime - self.timer
        if passed < 10000:
            self.screen.blit(self.background, (0, 0))
            if win:
                Text(FONT, 50, 'Enemies Destroyed!', WHITE, 100, 270).draw(self.screen)
            else:
                Text(FONT, 50, 'Game Over!', WHITE, 250, 270).draw(self.screen)

            Text(FONT, 30, 'Player Score:', WHITE, 100, 400).draw(self.screen)
            Text(FONT, 30, str(self.player_score), GREEN, 100, 450).draw(self.screen)
            Text(FONT, 30, 'AI Score:', WHITE, 500, 400).draw(self.screen)
            Text(FONT, 30, str(self.other_score), GREEN, 500, 450).draw(self.screen)
        elif passed > 10000:
            self.mainScreen = True

        for e in event.get():
            if self.should_exit(e):
                sys.exit()

    def main(self):
        while True:
            if self.mainScreen:
                self.screen.blit(self.background, (0, 0))
                self.titleText.draw(self.screen)
                self.titleText2.draw(self.screen)
                self.enemy1Text.draw(self.screen)
                self.enemy2Text.draw(self.screen)
                self.enemy3Text.draw(self.screen)
                self.enemy4Text.draw(self.screen)
                self.create_main_menu()
                for e in event.get():
                    if self.should_exit(e):
                        sys.exit()
                    if e.type == KEYUP:
                        # Only create blockers on a new game, not a new round
                        # self.allBlockers = sprite.Group(self.make_blockers(0),
                        #                                 self.make_blockers(1),
                        #                                 self.make_blockers(2),
                        #                                 self.make_blockers(3))
                        self.livesGroup.add(self.lifePlayer1, self.lifePlayer2, self.lifePlayer3, self.lifeOther1, self.lifeOther2, self.lifeOther3)
                        self.reset(0, 0)
                        self.startGame = True
                        self.mainScreen = False

            elif self.startGame:
                if not self.enemies and not self.explosionsGroup:
                    currentTime = time.get_ticks()
                    # Reset enemy starting position
                    self.enemyPosition = ENEMY_DEFAULT_POSITION
                    self.create_game_over(currentTime, win=True)
                else:
                    currentTime = time.get_ticks()
                    self.play_main_music(currentTime)
                    self.screen.blit(self.background, (0, 0))
                    #self.allBlockers.update(self.screen)
                    self.scoreText2 = Text(FONT, 20, str(self.player_score), GREEN,
                                           85, 5)
                    self.scoreText.draw(self.screen)
                    self.scoreText2.draw(self.screen)
                    self.scoreTextO2 = Text(FONT, 20, str(self.other_score), GREEN,
                                           485, 5)
                    self.scoreTextO.draw(self.screen)
                    self.scoreTextO2.draw(self.screen)
                    self.livesTextPlayer.draw(self.screen)
                    self.livesTextOther.draw(self.screen)
                    draw.line(self.screen, WHITE, (400, 0), (400, 600), 1)  # middle line
                    self.check_input()
                    self.enemies.update(currentTime)
                    self.allSprites.update(self.keys, currentTime)
                    cooperate = False
                    if len(sys.argv) > 1 and sys.argv[1] == "c":
                            cooperate = True
                    updateAI(self.other, self.enemies, self.enemyBullets, cooperate=cooperate)
                    self.explosionsGroup.update(currentTime)
                    self.check_collisions()
                    self.create_new_ship(self.makeNewPlayer, currentTime, human=True)
                    self.create_new_ship(self.makeNewOther, currentTime, human=False)
                    self.make_enemies_shoot()

            elif self.gameOver:
                currentTime = time.get_ticks()
                # Reset enemy starting position
                self.enemyPosition = ENEMY_DEFAULT_POSITION
                self.create_game_over(currentTime)

            display.update()
            self.clock.tick(60)


if __name__ == '__main__':
    game = SpaceInvaders()
    game.main()

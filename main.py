import math
import random

ANIMATION_INTERVAL = 6

WIDTH = 980
HEIGHT = 720

PLAYER_ANIMATION_FRAMES = {'idleLeft': ['player_idle_1l', 'player_idle_2l'], 'idleRight': ['player_idle_1r', 'player_idle_2r'], 'hurtLeft': ['player_hurtl'], 'hurtRight': ['player_hurtr'], 'walkLeft': [
    'player_walk_1l', 'player_walk_2l', 'player_walk_3l'], 'walkRight': ['player_walk_1r', 'player_walk_2r', 'player_walk_3r'], 'deadLeft': ['player_deadl'], 'deadRight': ['player_deadr']}
CATERPILLAR_ANIMATION_FRAMES = {'idleLeft': ['enemy1_idle_1l', 'enemy1_idle_2l'], 'idleRight': ['enemy1_idle_1r', 'enemy1_idle_2r'], 'hurtLeft': ['enemy1_hurtl'], 'hurtRight': ['enemy1_hurtr'], 'walkLeft': [
    'enemy1_walk_1l', 'enemy1_walk_2l', 'enemy1_walk_3l'], 'walkRight': ['enemy1_walk_1r', 'enemy1_walk_2r', 'enemy1_walk_3r'], 'deadLeft': ['enemy1_deadl'], 'deadRight': ['enemy1_deadr']}
WASP_ANIMATION_FRAMES = {'idleLeft': ['enemy2_idle_1l', 'enemy2_idle_2l'], 'idleRight': ['enemy2_idle_1r', 'enemy2_idle_2r'], 'hurtLeft': ['enemy2_hurtl'], 'hurtRight': ['enemy2_hurtr'], 'walkLeft': [
    'enemy2_walk_1l', 'enemy2_walk_2l', 'enemy2_walk_3l'], 'walkRight': ['enemy2_walk_1r', 'enemy2_walk_2r', 'enemy2_walk_3r'], 'deadLeft': ['enemy2_deadl'], 'deadRight': ['enemy2_deadr']}
CAT_ANIMATION_FRAMES = {'idleLeft': ['enemy3_idle_1l', 'enemy3_idle_2l'], 'idleRight': ['enemy3_idle_1r', 'enemy3_idle_2r'], 'hurtLeft': ['enemy3_hurtl'], 'hurtRight': ['enemy3_hurtr'], 'walkLeft': [
    'enemy3_walk_1l', 'enemy3_walk_2l', 'enemy3_walk_3l'], 'walkRight': ['enemy3_walk_1r', 'enemy3_walk_2r', 'enemy3_walk_3r'], 'deadLeft': ['enemy3_deadl'], 'deadRight': ['enemy3_deadr']}

WAVE_PROPERTIES = {1: {'amount': 15, 'upgrade chance': 5, 'spawn delay': 2}, 2: {'amount': 20, 'upgrade chance': 50, 'spawn delay': 2}, 3: {
    'amount': 30, 'upgrade chance': 10, 'spawn delay': 1}, 4: {'amount': 30, 'upgrade chance': 50, 'spawn delay': 2}, 5: {'amount': 50, 'upgrade chance': 50, 'spawn delay': 1}}

HITBOXES = {'small': 12, 'medium': 15, 'big': 20}
SPEED = {'slow': 1, 'medium': 2, 'fast': 3, 'very fast': 5, 'projectile': 7}
HEALTH = {'frail': 1, 'normal': 2, 'tough': 3, 'very tough': 5}
DAMAGE = {'weak': 1, 'strong': 2}


class Entity(Actor):
    def __init__(self, image, position, movespeed=1, frames={}, maxHealth=1, hitbox=0, hurtSound=None):
        super().__init__(image, position)
        self.movespeed = movespeed
        self.frames = frames
        self.maxHealth = maxHealth
        self.currentHealth = maxHealth
        self.isHurt = False
        self.isMoving = False
        self.direction = [0, 0]
        self.facingDirection = 1
        self.hitboxSize = hitbox
        self.hurtSound = hurtSound

        self.currentFrame = 0
        self.frameId = 0

    def updateAnimation(self):
        animationState = self.getCurrentAnimationState()

        if self.direction[0] < 0:
            self.facingDirection = 0
        elif self.direction[0] > 0:
            self.facingDirection = 1

        self.currentFrame += 1
        # we update the animation every couple of frames to control its speed
        if self.currentFrame % ANIMATION_INTERVAL == 0:
            self.frameId += 1
        if self.frameId >= len(self.frames[animationState]):
            self.frameId = 0
        self.image = self.frames[animationState][self.frameId]

    def getCurrentAnimationState(self):
        if self.currentHealth <= 0:
            if self.facingDirection:
                return 'deadRight'
            return 'deadLeft'
        if self.isHurt:
            if self.facingDirection:
                return 'hurtRight'
            return 'hurtLeft'
        if self.isMoving:
            if self.facingDirection:
                return 'walkRight'
            return 'walkLeft'
        if self.facingDirection:
            return 'idleRight'
        return 'idleLeft'

    def changeCurrentHealth(self, amount):
        self.currentHealth += amount
        if amount < 0:
            self.isHurt = True
            getattr(sounds, self.hurtSound).play()
            clock.schedule(self.setCharacterNormal, 0.2)

    def setCharacterNormal(self):
        self.isHurt = False

    def move(self):
        # get the directional magnitude to normalize the speed in diagonal directions
        magnitude = math.hypot(self.direction[0], self.direction[1])

        if magnitude == 0:
            self.isMoving = False
            return

        self.isMoving = True

        self.x += (self.direction[0] / magnitude) * self.movespeed
        self.y += (self.direction[1] / magnitude) * self.movespeed

    def checkIfLeftScreen(self, list):
        if self.left > WIDTH or self.right < 0 or self.bottom < 0 or self.top > HEIGHT:
            list.remove(self)


class Projectile(Entity):
    def __init__(self, image, position, movespeed, hitbox, direction, damage):
        super().__init__(image, position, movespeed, hitbox=hitbox)
        self.direction = direction
        self.damage = damage

    def playSound(self):
        soundId = random.randint(1, 3)
        getattr(sounds, f'shoot{soundId}').play()


class Player(Entity):
    def __init__(self, image, position, movespeed, frames, maxHealth, hitbox, hurtSound):
        super().__init__(image, position, movespeed, frames, maxHealth, hitbox, hurtSound)
        self.isInvulnerable = False
        self.invulnerabilityTime = .5
        self.shootingCooldown = .8
        self.canShoot = True

    def updateShooting(self):
        global projectiles
        if self.canShoot:
            projectile = Projectile('player_projectile', self.pos,
                                    SPEED['projectile'], HITBOXES['small'], self.getMouseDirection(), DAMAGE['weak'])
            projectiles.append(projectile)
            projectile.playSound()
            self.canShoot = False
            clock.schedule(self.reload, self.shootingCooldown)

    def reload(self):
        self.canShoot = True

    def getMouseDirection(self):
        radiansToMouse = math.atan2(mousePos[1] - self.y, mousePos[0] - self.x)

        xDirection = math.cos(radiansToMouse)
        yDirection = math.sin(radiansToMouse)
        return [xDirection, yDirection]

    def activateInvulnerability(self):
        self.isInvulnerable = True
        clock.schedule(self.deactivateInvulnerability,
                       self.invulnerabilityTime)

    def deactivateInvulnerability(self):
        self.isInvulnerable = False

    def updatePressedDirection(self):
        self.direction = [0, 0]

        if keyboard[keys.A] or keyboard[keys.LEFT]:
            self.direction[0] = -1
        if keyboard[keys.D] or keyboard[keys.RIGHT]:
            self.direction[0] = 1

        if keyboard[keys.W] or keyboard[keys.UP]:
            self.direction[1] = -1
        if keyboard[keys.S] or keyboard[keys.DOWN]:
            self.direction[1] = 1


class Enemy(Entity):
    def __init__(self, image, position, movespeed, frames, maxHealth, hitbox, damage, hurtSound):
        super().__init__(image, position, movespeed, frames, maxHealth, hitbox, hurtSound)
        self.damage = damage
        self.removalTime = 1

    def checkPlayerCollision(self, player):
        distanceToPlayer = self.distance_to(player)
        if distanceToPlayer < self.hitboxSize + player.hitboxSize and player.isInvulnerable == False:
            player.changeCurrentHealth(-self.damage)
            print(f'Hit player for {self.damage}!')
            player.activateInvulnerability()

    def checkProjectileCollisions(self, projectiles):
        for projectile in projectiles:
            if projectile:
                distanceToProjectile = self.distance_to(projectile)
                if distanceToProjectile < self.hitboxSize + projectile.hitboxSize:
                    self.changeCurrentHealth(-projectile.damage)
                    if self.currentHealth <= 0:
                        clock.schedule(self.removeSelf, self.removalTime)
                    projectiles.remove(projectile)

    def updatePlayerDirection(self, player):
        if player.currentHealth > 0:
            angleTowardsPlayer = self.angle_to(player)
        else:
            self.movespeed = SPEED['slow']
            angleTowardsPlayer = self.angle_to(player) + 180
        radiansTowardsPlayer = math.radians(angleTowardsPlayer)

        xDirection = math.cos(radiansTowardsPlayer)
        yDirection = -math.sin(radiansTowardsPlayer)

        self.direction = [xDirection, yDirection]

    def removeSelf(self):
        global enemies
        enemies.remove(self)


class WaveManager():
    def __init__(self):
        self.currentWave = 1
        self.intermission = False
        self.spawnsRemaining = WAVE_PROPERTIES[self.currentWave]['amount']

        self.waveText = Actor('wave_text', ((WIDTH/2), -50))
        self.waveNumber = Actor(
            f'{self.currentWave}', ((WIDTH/2+34), -50))

    def startWave(self):
        self.spawnEnemies()
        animate(self.waveText, 'out_elastic', pos=((WIDTH/2), 30))
        animate(self.waveNumber, 'out_elastic', pos=((WIDTH/2+34), 30))
        clock.schedule(self.retractWaveText, 3)

    def retractWaveText(self):
        animate(self.waveText, 'accelerate', pos=((WIDTH/2), -50))
        animate(self.waveNumber, 'accelerate', pos=((WIDTH/2+34), -50))

    def spawnEnemies(self):
        # we choose an edge of the screen to spread out enemy spawns
        spawnRegion = random.randint(0, 3)
        OFFSET = 50
        match(spawnRegion):
            case 0:  # top
                posX = random.randint(0, WIDTH)
                posY = -OFFSET
            case 1:  # left
                posX = -OFFSET
                posY = random.randint(0, HEIGHT)
            case 2:  # right
                posX = WIDTH + OFFSET
                posY = random.randint(0, HEIGHT)
            case 3:  # bottom
                posX = random.randint(0, WIDTH)
                posY = HEIGHT + OFFSET
        match(self.getEnemyType()):
            case 'caterpillar':
                enemy = Enemy('enemy1_idle_1r', (posX, posY), SPEED['slow'], CATERPILLAR_ANIMATION_FRAMES,
                              HEALTH['normal'], HITBOXES['medium'], DAMAGE['weak'], 'enemy_hurt')
            case 'wasp':
                enemy = Enemy('enemy2_idle_1r', (posX, posY),
                              SPEED['fast'], WASP_ANIMATION_FRAMES, HEALTH['frail'], HITBOXES['small'], DAMAGE['weak'], 'enemy_hurt')
            case 'cat':
                enemy = Enemy('enemy3_idle_1r', (posX, posY),
                              SPEED['medium'], CAT_ANIMATION_FRAMES, HEALTH['tough'], HITBOXES['big'], DAMAGE['strong'], 'enemy_hurt')
        global enemies
        enemies.append(enemy)
        self.spawnsRemaining -= 1
        if self.spawnsRemaining > 0 and self.intermission == False:
            clock.schedule(self.spawnEnemies,
                           WAVE_PROPERTIES[self.currentWave]['spawn delay'])
        else:
            self.waitForWaveEnd()

    def waitForWaveEnd(self):
        if self.currentWave == 5:
            # end game
            return
        if len(enemies) > 0:
            clock.schedule(self.waitForWaveEnd, 1)
            return
        self.endWave()

    def endWave(self):
        getattr(sounds, 'wave_pass').play()
        self.intermission = True
        self.currentWave += 1
        self.spawnsRemaining = WAVE_PROPERTIES[self.currentWave]['amount']

    def getEnemyType(self):
        # we will roll two 'dice', each with a chance to further upgrade the enemy for difficulty and randomness
        roll = [random.randint(1, 100), random.randint(1, 100)]
        if roll[0] <= WAVE_PROPERTIES[self.currentWave]['upgrade chance']:
            if roll[1] <= WAVE_PROPERTIES[self.currentWave]['upgrade chance']:
                return 'cat'
            return 'wasp'
        return 'caterpillar'


def getBackgroundImage():
    roll = random.randint(1, 4)
    return f'background_{roll}'


player = Player('player_idle_1r', (WIDTH/2, HEIGHT/2),
                SPEED['very fast'], PLAYER_ANIMATION_FRAMES, HEALTH['very tough'], HITBOXES['big'], 'player_hurt')

projectiles = []
enemies = []

waveManager = WaveManager()
waveManager.startWave()

music.play('kim-lightyear-leave-the-world-tonight-chiptune-edit-loop-132102')
music.set_volume(.02)

mousePos = [0, 0]
background = getBackgroundImage()


def on_mouse_move(pos, rel, buttons):
    global mousePos
    mousePos = pos


def draw():
    screen.clear()
    screen.blit(background, (0, 0))
    for enemy in enemies:
        enemy.draw()
    for projectile in projectiles:
        projectile.draw()
    player.draw()
    waveManager.waveText.draw()
    waveManager.waveNumber.draw()


def update():
    player.updateAnimation()
    if player.currentHealth > 0:
        player.updatePressedDirection()
        player.move()
        player.updateShooting()
    for enemy in enemies:
        # enemy.checkIfLeftScreen(enemies)
        if enemy.currentHealth > 0:
            enemy.updatePlayerDirection(player)
            enemy.move()
            enemy.checkProjectileCollisions(projectiles)
            enemy.checkPlayerCollision(player)
        enemy.updateAnimation()
    for projectile in projectiles:
        projectile.checkIfLeftScreen(projectiles)
        projectile.move()

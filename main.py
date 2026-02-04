import math
import random

ANIMATION_INTERVAL = 6

WIDTH = 980
HEIGHT = 720


def make_animation_frames_dict(prefix):
    return {
        "idleLeft": [f"{prefix}_idle_1l", f"{prefix}_idle_2l"],
        "idleRight": [f"{prefix}_idle_1r", f"{prefix}_idle_2r"],
        "hurtLeft": [f"{prefix}_hurtl"],
        "hurtRight": [f"{prefix}_hurtr"],
        "walkLeft": [f"{prefix}_walk_1l", f"{prefix}_walk_2l", f"{prefix}_walk_3l"],
        "walkRight": [f"{prefix}_walk_1r", f"{prefix}_walk_2r", f"{prefix}_walk_3r"],
        "deadLeft": [f"{prefix}_deadl"],
        "deadRight": [f"{prefix}_deadr"],
    }


PLAYER_ANIMATION_FRAMES = make_animation_frames_dict("player")
CATERPILLAR_ANIMATION_FRAMES = make_animation_frames_dict("enemy1")
WASP_ANIMATION_FRAMES = make_animation_frames_dict("enemy2")
CAT_ANIMATION_FRAMES = make_animation_frames_dict("enemy3")


WAVE_PROPERTIES = {
    1: {"amount": 15, "upgrade": 5, "delay": 2},
    2: {"amount": 20, "upgrade": 50, "delay": 2},
    3: {"amount": 30, "upgrade": 10, "delay": 1},
    4: {"amount": 30, "upgrade": 50, "delay": 2},
    5: {"amount": 50, "upgrade": 50, "delay": 1},
}

HITBOXES = {"small": 12, "medium": 15, "big": 20}
SPEED = {"slow": 1, "medium": 2, "fast": 3, "very fast": 5, "projectile": 7}
HEALTH = {"frail": 1, "normal": 2, "tough": 3, "very tough": 5}
DAMAGE = {"weak": 1, "strong": 2}

ENEMY_TYPES = {
    "caterpillar": {
        "image": "enemy1_idle_1r",
        "speed": SPEED["slow"],
        "frames": CATERPILLAR_ANIMATION_FRAMES,
        "health": HEALTH["normal"],
        "hitbox": HITBOXES["medium"],
        "damage": DAMAGE["weak"],
    },
    "wasp": {
        "image": "enemy2_idle_1r",
        "speed": SPEED["fast"],
        "frames": WASP_ANIMATION_FRAMES,
        "health": HEALTH["frail"],
        "hitbox": HITBOXES["small"],
        "damage": DAMAGE["weak"],
    },
    "cat": {
        "image": "enemy3_idle_1r",
        "speed": SPEED["medium"],
        "frames": CAT_ANIMATION_FRAMES,
        "health": HEALTH["tough"],
        "hitbox": HITBOXES["big"],
        "damage": DAMAGE["strong"],
    },
}


class Entity(Actor):
    def __init__(
        self,
        image,
        position,
        movespeed=1,
        frames={},
        max_health=1,
        hitbox=0,
        hurt_sound=None,
    ):
        super().__init__(image, position)
        self.movespeed = movespeed
        self.frames = frames
        self.max_health = max_health
        self.current_health = max_health
        self.is_hurt = False
        self.is_moving = False
        self.direction = [0, 0]
        self.facing_direction = 1
        self.hitbox_size = hitbox
        self.hurt_sound = hurt_sound

        self.current_frame = 0
        self.frame_id = 0

    def update_animation(self):
        animation_state = self.get_current_animation_state()

        if self.direction[0] < 0:
            self.facing_direction = 0
        elif self.direction[0] > 0:
            self.facing_direction = 1

        self.current_frame += 1
        # we update the animation every couple of frames to control its speed
        if self.current_frame % ANIMATION_INTERVAL == 0:
            self.frame_id += 1
        if self.frame_id >= len(self.frames[animation_state]):
            self.frame_id = 0
        self.image = self.frames[animation_state][self.frame_id]

    def get_current_animation_state(self):
        if self.current_health <= 0:
            if self.facing_direction:
                return "deadRight"
            return "deadLeft"
        if self.is_hurt:
            if self.facing_direction:
                return "hurtRight"
            return "hurtLeft"
        if self.is_moving:
            if self.facing_direction:
                return "walkRight"
            return "walkLeft"
        if self.facing_direction:
            return "idleRight"
        return "idleLeft"

    def change_current_health(self, amount):
        self.current_health += amount
        if amount < 0:
            self.is_hurt = True
            if muted == False:
                getattr(sounds, self.hurt_sound).play()
            clock.schedule(self.set_character_normal, 0.2)

    def set_character_normal(self):
        self.is_hurt = False

    def move(self):
        # get the directional magnitude to normalize the speed in diagonal directions
        magnitude = math.hypot(self.direction[0], self.direction[1])

        if magnitude == 0:
            self.is_moving = False
            return

        self.is_moving = True

        self.x += (self.direction[0] / magnitude) * self.movespeed
        self.y += (self.direction[1] / magnitude) * self.movespeed

    def check_if_left_screen(self, entity_list):
        if self.left > WIDTH or self.right < 0 or self.bottom < 0 or self.top > HEIGHT:
            entity_list.remove(self)


class Projectile(Entity):
    def __init__(self, image, position, movespeed, hitbox, direction, damage):
        super().__init__(image, position, movespeed, hitbox=hitbox)
        self.direction = direction
        self.damage = damage

    def play_sound(self):
        sound_id = random.randint(1, 3)
        if muted == False:
            getattr(sounds, f"shoot{sound_id}").play()


class Player(Entity):
    def __init__(
        self, image, position, movespeed, frames, max_health, hitbox, hurt_sound
    ):
        super().__init__(
            image, position, movespeed, frames, max_health, hitbox, hurt_sound
        )
        self.is_invulnerable = False
        self.invulnerability_time = 0.5
        self.shooting_cooldown = 0.8
        self.can_shoot = True

    def update_shooting(self):
        global projectiles
        if self.can_shoot:
            projectile = Projectile(
                "player_projectile",
                self.pos,
                SPEED["projectile"],
                HITBOXES["small"],
                self.get_mouse_direction(),
                DAMAGE["weak"],
            )
            projectiles.append(projectile)
            projectile.play_sound()
            self.can_shoot = False
            clock.schedule(self.reload, self.shooting_cooldown)

    def reload(self):
        self.can_shoot = True

    def get_mouse_direction(self):
        radians_to_mouse = math.atan2(mouse_pos[1] - self.y, mouse_pos[0] - self.x)

        x_direction = math.cos(radians_to_mouse)
        y_direction = math.sin(radians_to_mouse)
        return [x_direction, y_direction]

    def activate_invulnerability(self):
        self.is_invulnerable = True
        clock.schedule(self.deactivate_invulnerability, self.invulnerability_time)

    def deactivate_invulnerability(self):
        self.is_invulnerable = False

    def update_pressed_direction(self):
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
    def __init__(
        self, image, position, movespeed, frames, max_health, hitbox, damage, hurt_sound
    ):
        super().__init__(
            image, position, movespeed, frames, max_health, hitbox, hurt_sound
        )
        self.damage = damage
        self.removal_time = 1

    def check_player_collision(self, player):
        distance_to_player = self.distance_to(player)
        if (
            distance_to_player < self.hitbox_size + player.hitbox_size
            and player.is_invulnerable == False
        ):
            player.change_current_health(-self.damage)
            player.activate_invulnerability()

    def check_projectile_collisions(self, projectiles):
        for projectile in projectiles:
            if projectile:
                distance_to_projectile = self.distance_to(projectile)
                if distance_to_projectile < self.hitbox_size + projectile.hitbox_size:
                    self.change_current_health(-projectile.damage)
                    if self.current_health <= 0:
                        clock.schedule(self.remove_self, self.removal_time)
                    projectiles.remove(projectile)

    def update_player_direction(self, player):
        if player.current_health > 0:
            angle_towards_player = self.angle_to(player)
        else:
            self.movespeed = SPEED["slow"]
            angle_towards_player = self.angle_to(player) + 180
        radians_towards_player = math.radians(angle_towards_player)

        x_direction = math.cos(radians_towards_player)
        y_direction = -math.sin(radians_towards_player)

        self.direction = [x_direction, y_direction]

    def remove_self(self):
        global enemies
        enemies.remove(self)


class WaveManager:
    def __init__(self):
        self.current_wave = 1
        self.intermission = False
        self.spawns_remaining = WAVE_PROPERTIES[self.current_wave]["amount"]

        self.wave_text = Actor("wave_text", ((WIDTH / 2), -50))
        self.wave_number = Actor(f"{self.current_wave}", ((WIDTH / 2 + 34), -50))

    def start_wave(self):
        self.spawn_enemies()
        animate(self.wave_text, "out_elastic", pos=((WIDTH / 2), 30))
        animate(self.wave_number, "out_elastic", pos=((WIDTH / 2 + 34), 30))
        clock.schedule(self.retract_wave_text, 3)

    def retract_wave_text(self):
        animate(self.wave_text, "accelerate", pos=((WIDTH / 2), -50))
        animate(self.wave_number, "accelerate", pos=((WIDTH / 2 + 34), -50))

    def spawn_enemies(self):
        # we choose an edge of the screen to spread out enemy spawns
        spawn_region = random.randint(0, 3)
        OFFSET = 50
        match (spawn_region):
            case 0:  # top
                pos_x = random.randint(0, WIDTH)
                pos_y = -OFFSET
            case 1:  # left
                pos_x = -OFFSET
                pos_y = random.randint(0, HEIGHT)
            case 2:  # right
                pos_x = WIDTH + OFFSET
                pos_y = random.randint(0, HEIGHT)
            case 3:  # bottom
                pos_x = random.randint(0, WIDTH)
                pos_y = HEIGHT + OFFSET
        enemy_type = self.get_enemy_type()
        enemy_data = ENEMY_TYPES[enemy_type]
        enemy = Enemy(
            enemy_data["image"],
            (pos_x, pos_y),
            enemy_data["speed"],
            enemy_data["frames"],
            enemy_data["health"],
            enemy_data["hitbox"],
            enemy_data["damage"],
            "enemy_hurt",
        )
        global enemies
        enemies.append(enemy)
        self.spawns_remaining -= 1
        if self.spawns_remaining > 0 and self.intermission == False:
            clock.schedule(
                self.spawn_enemies, WAVE_PROPERTIES[self.current_wave]["delay"]
            )
        else:
            self.wait_for_wave_end()

    def wait_for_wave_end(self):
        if self.current_wave == 5:
            # end game
            return
        if len(enemies) > 0:
            clock.schedule(self.wait_for_wave_end, 1)
            return
        self.end_wave()

    def end_wave(self):
        if muted == False:
            getattr(sounds, "wave_pass").play()
        self.intermission = True
        self.current_wave += 1
        self.spawns_remaining = WAVE_PROPERTIES[self.current_wave]["amount"]

    def get_enemy_type(self):
        # we will roll two 'dice', each with a chance to further upgrade the enemy for difficulty and randomness
        roll = [random.randint(1, 100), random.randint(1, 100)]
        if roll[0] <= WAVE_PROPERTIES[self.current_wave]["upgrade"]:
            if roll[1] <= WAVE_PROPERTIES[self.current_wave]["upgrade"]:
                return "cat"
            return "wasp"
        return "caterpillar"


def get_background_image():
    roll = random.randint(1, 4)
    return f"background_{roll}"


mouse_pos = [0, 0]
background = None
player = None
wave_manager = None
projectiles = []
enemies = []
game_started = False
muted = False
buttons = []


def main_menu():
    OFFSET = 60
    global buttons, background

    background = "background_0"

    play_game_button = Actor("play", (WIDTH / 2, HEIGHT / 2))
    mute_game_button = Actor(f"mute_{int(muted)}", (WIDTH / 2, HEIGHT / 2 + OFFSET))
    exit_game_button = Actor("exit", (WIDTH / 2, HEIGHT / 2 + 2 * OFFSET))

    buttons.append(play_game_button)
    buttons.append(mute_game_button)
    buttons.append(exit_game_button)


def start_game():
    global player, wave_manager, background
    # global wave_manager
    # global background

    background = get_background_image()

    player = Player(
        "player_idle_1r",
        (WIDTH / 2, HEIGHT / 2),
        SPEED["very fast"],
        PLAYER_ANIMATION_FRAMES,
        HEALTH["very tough"],
        HITBOXES["big"],
        "player_hurt",
    )

    wave_manager = WaveManager()
    wave_manager.start_wave()

    if muted == False:
        music.play("kim-lightyear-leave-the-world-tonight-chiptune-edit-loop-132102")
        music.set_volume(0.02)


main_menu()


def on_mouse_down(pos):
    for i, button in enumerate(buttons):
        if button.collidepoint(pos):
            global muted
            if muted == False:
                getattr(sounds, "shoot3").play()
            if i == 0:  # play
                global game_started
                game_started = True
                start_game()
            elif i == 1:  # mute/unmute
                muted = not muted
                button.image = f"mute_{int(muted)}"
            else:
                exit()


def on_mouse_move(pos, rel, buttons):
    global mouse_pos
    mouse_pos = pos


def draw():
    screen.clear()
    screen.blit(background, (0, 0))
    if game_started:
        for enemy in enemies:
            enemy.draw()
        for projectile in projectiles:
            projectile.draw()
        player.draw()
        wave_manager.wave_text.draw()
        wave_manager.wave_number.draw()
    else:
        screen.blit("logo", (WIDTH / 2 - 144, HEIGHT / 2 - 300))
        for button in buttons:
            button.draw()


def update():
    if game_started:
        player.update_animation()
        if player.current_health > 0:
            player.update_pressed_direction()
            player.move()
            player.update_shooting()
        for enemy in enemies:
            # enemy.check_if_left_screen(enemies)
            if enemy.current_health > 0:
                enemy.update_player_direction(player)
                enemy.move()
                enemy.check_projectile_collisions(projectiles)
                enemy.check_player_collision(player)
            enemy.update_animation()
        for projectile in projectiles:
            projectile.check_if_left_screen(projectiles)
            projectile.move()

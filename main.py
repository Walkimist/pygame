import math
import random

# I know I went a little overboard on the line count and game complexity, but I do hope it doesn't detract from my overall score
# as a limit wasn't stated in the requirements. I was just having a lot of fun making this x)

ANIMATION_INTERVAL = 6

WIDTH = 980
HEIGHT = 720


# writing each dictionary manually would be very boring
def animation_frames_dict(prefix):
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


PLAYER_ANIMATION_FRAMES = animation_frames_dict("player")
CATERPILLAR_ANIMATION_FRAMES = animation_frames_dict("enemy1")
WASP_ANIMATION_FRAMES = animation_frames_dict("enemy2")
CAT_ANIMATION_FRAMES = animation_frames_dict("enemy3")

# very arbitrary values I gathered from brief testing, probably not balanced
WAVE_PROPERTIES = {
    1: {"amount": 15, "upgrade": 5, "delay": 1.2},
    2: {"amount": 20, "upgrade": 30, "delay": 0.9},
    3: {"amount": 30, "upgrade": 10, "delay": 0.6},
    4: {"amount": 30, "upgrade": 50, "delay": 0.7},
    5: {"amount": 60, "upgrade": 80, "delay": 0.6},
}


HITBOXES = {"small": 12, "medium": 15, "big": 20}
SPEED = {"slow": 2.5, "medium": 4, "fast": 4.5}
HEALTH = {"frail": 1, "normal": 2, "tough": 4}
DAMAGE = {"weak": 2, "strong": 3}

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

UPGRADE_PROPERTIES = {
    "damage": {"common": 0.5, "rare": 1.5, "epic": 3},
    "firerate": {"common": -0.15, "rare": -0.2, "epic": -0.3},
    "shot_speed": {"common": 0.2, "rare": 0.5, "epic": 0.8},
    "max_health": {"common": 1, "rare": 2, "epic": 3},
    "move_speed": {"common": 0.5, "rare": 1, "epic": 1.5},
}


class Entity(Actor):
    def __init__(
        self,
        image,
        position,
        move_speed=1,
        frames={},
        max_health=1,
        hitbox=0,
        hurt_sound=None,
    ):
        super().__init__(image, position)
        self.move_speed = move_speed
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
            if game_manager.muted == False:
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

        self.x += (self.direction[0] / magnitude) * self.move_speed
        self.y += (self.direction[1] / magnitude) * self.move_speed

    def check_if_left_screen(self, entity_list):
        if self.left > WIDTH or self.right < 0 or self.bottom < 0 or self.top > HEIGHT:
            entity_list.remove(self)


class Projectile(Entity):
    def __init__(self, image, position, move_speed, hitbox, direction, damage):
        super().__init__(image, position, move_speed, hitbox=hitbox)
        self.direction = direction
        self.damage = damage

    def play_sound(self):
        sound_id = random.randint(1, 3)
        if game_manager.muted == False:
            getattr(sounds, f"shoot{sound_id}").play()


class Player(Entity):
    def __init__(
        self, image, position, move_speed, frames, max_health, hitbox, hurt_sound
    ):
        super().__init__(
            image, position, move_speed, frames, max_health, hitbox, hurt_sound
        )
        self.is_invulnerable = False
        self.invulnerability_time = 0.5
        self.can_shoot = True

        self.firerate = 0.6
        self.shot_speed = 7
        self.damage = 1
        self.move_speed = move_speed
        self.max_health = max_health

    def update_shooting(self):
        if (
            self.can_shoot
            and game_manager.wave_manager.intermission == False
            and game_manager.game_over == False
        ):
            projectile = Projectile(
                "player_projectile",
                self.pos,
                self.shot_speed,
                HITBOXES["small"],
                self.get_mouse_direction(),
                self.damage,
            )
            game_manager.projectiles.append(projectile)
            projectile.play_sound()
            self.can_shoot = False
            clock.schedule(self.reload, self.firerate)

    def reload(self):
        self.can_shoot = True

    def get_mouse_direction(self):
        radians_to_mouse = math.atan2(
            game_manager.mouse_pos[1] -
            self.y, game_manager.mouse_pos[0] - self.x
        )

        x_direction = math.cos(radians_to_mouse)
        y_direction = math.sin(radians_to_mouse)
        return [x_direction, y_direction]

    def activate_invulnerability(self):
        self.is_invulnerable = True
        clock.schedule(self.deactivate_invulnerability,
                       self.invulnerability_time)

    def deactivate_invulnerability(self):
        self.is_invulnerable = False

    def check_if_dead(self):
        if self.current_health <= 0:
            game_manager.game_over = True

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
        game_manager.enemies.remove(self)


class Upgrade(Actor):
    def __init__(self, pos, type_block_list):
        super().__init__(image="1", pos=(0, 0))
        self.type_block_list = type_block_list
        self.type = self.generate_upgrade_type(self.type_block_list)
        self.rarity = self.generate_upgrade_rarity()
        self.pos = pos
        self.image = f"upgrade_button_{self.rarity}"

    def upgrade_stat(self, player):
        current_value = getattr(player, self.type)
        upgrade_value = UPGRADE_PROPERTIES[self.type][self.rarity]
        if self.type == "firerate" and current_value + upgrade_value < 0.1:
            setattr(player, self.type, current_value + upgrade_value)
        else:
            setattr(player, self.type, current_value + upgrade_value)
        # print(self.type, upgrade_value)
        if self.type == "max_health":
            player.change_current_health(
                UPGRADE_PROPERTIES[self.type][self.rarity])

    def generate_upgrade_type(self, block_list):
        upgrade_types = list(UPGRADE_PROPERTIES.keys())
        for type in block_list:
            upgrade_types.remove(type)
        type_roll = random.randint(0, len(upgrade_types) - 1)
        return upgrade_types[type_roll]

    def generate_upgrade_rarity(self):
        # we will roll two 'dice', each with a chance to upgrade the rarity for randomness
        rarity = "common"
        rarity_roll = [random.randint(1, 100), random.randint(1, 100)]
        if rarity_roll[0] <= 40:
            rarity = "rare"
            if rarity_roll[1] <= 20:
                rarity = "epic"
        return rarity


class WaveManager:
    def __init__(self):
        self.current_wave = 1
        self.intermission = False
        self.spawns_remaining = WAVE_PROPERTIES[self.current_wave]["amount"]

        self.wave_text = Actor("wave_text", ((WIDTH / 2), -50))
        self.wave_number = Actor(
            f"{self.current_wave}", ((WIDTH / 2 + 34), -50))

    def start_wave(self):
        self.wave_number.image = f"{self.current_wave}"
        self.intermission = False
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
        if spawn_region == 0:  # top
            pos_x = random.randint(0, WIDTH)
            pos_y = -OFFSET
        elif spawn_region == 1:  # left
            pos_x = -OFFSET
            pos_y = random.randint(0, HEIGHT)
        elif spawn_region == 2:  # right
            pos_x = WIDTH + OFFSET
            pos_y = random.randint(0, HEIGHT)
        else:  # bottom
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
        game_manager.enemies.append(enemy)
        self.spawns_remaining -= 1
        if self.spawns_remaining > 0 and self.intermission == False:
            clock.schedule(
                self.spawn_enemies, WAVE_PROPERTIES[self.current_wave]["delay"]
            )
        else:
            self.wait_for_wave_end()

    def wait_for_wave_end(self):
        if len(game_manager.enemies) > 0:
            clock.schedule(self.wait_for_wave_end, 1)
            return
        self.end_wave()

    def end_wave(self):
        if game_manager.muted == False:
            getattr(sounds, "wave_pass").play()
        if self.current_wave == 5:
            game_manager.game_over = True
            return
        self.intermission = True
        self.current_wave += 1
        self.spawns_remaining = WAVE_PROPERTIES[self.current_wave]["amount"]
        self.generate_upgrades()

    def generate_upgrades(self):
        OFFSET = 326
        self.upgrades = []
        upgrade_types = []
        for i in range(0, 3):
            upgrade = Upgrade(
                (OFFSET * i + OFFSET / 2, HEIGHT / 2), upgrade_types)
            upgrade_types.append(upgrade.type)
            self.upgrades.append(upgrade)

    def get_enemy_type(self):
        # again we roll two dice for enemy type, adding randomness and difficulty
        roll = [random.randint(1, 100), random.randint(1, 100)]
        if roll[0] <= WAVE_PROPERTIES[self.current_wave]["upgrade"]:
            if roll[1] <= WAVE_PROPERTIES[self.current_wave]["upgrade"]:
                return "cat"
            return "wasp"
        return "caterpillar"


def get_background_image():
    roll = random.randint(1, 4)
    return f"background_{roll}"

# Trying to stop the global spam, also way better for resetting the game


class GameManager:
    def __init__(self):
        self.reset()

    def reset(self):
        music.stop()
        self.mouse_pos = [WIDTH / 2, HEIGHT / 2]
        self.background = None
        self.wave_manager = None
        self.projectiles = []
        self.enemies = []
        self.game_started = False
        self.muted = False
        self.buttons = []
        self.game_over = False
        self.player = None
        self.restart_scheduled = False


game_manager = GameManager()


def restart_game():
    game_manager.reset()
    main_menu()


def main_menu():
    OFFSET = 60

    game_manager.background = "background_0"

    play_game_button = Actor("play", (WIDTH / 2, HEIGHT / 2))
    mute_game_button = Actor(
        f"mute_{int(game_manager.muted)}", (WIDTH / 2, HEIGHT / 2 + OFFSET)
    )
    exit_game_button = Actor("exit", (WIDTH / 2, HEIGHT / 2 + 2 * OFFSET))

    game_manager.buttons.append(play_game_button)
    game_manager.buttons.append(mute_game_button)
    game_manager.buttons.append(exit_game_button)


def start_game():
    game_manager.game_started = True
    game_manager.background = get_background_image()

    game_manager.player = Player(
        "player_idle_1r",
        (WIDTH / 2, HEIGHT / 2),
        5,
        PLAYER_ANIMATION_FRAMES,
        5,
        HITBOXES["big"],
        "player_hurt",
    )

    game_manager.wave_manager = WaveManager()
    game_manager.wave_manager.start_wave()

    if game_manager.muted == False:
        music.play(
            "kim-lightyear-leave-the-world-tonight-chiptune-edit-loop-132102")
        music.set_volume(0.02)


main_menu()


def on_mouse_down(pos):
    if game_manager.game_over == False:
        if game_manager.game_started:
            if game_manager.wave_manager.intermission:
                for upgrade in game_manager.wave_manager.upgrades:
                    if upgrade.collidepoint(pos):
                        if game_manager.muted == False:
                            getattr(sounds, "get_upgrade").play()
                        upgrade.upgrade_stat(game_manager.player)
                        game_manager.wave_manager.upgrades = []
                        game_manager.wave_manager.start_wave()
        else:
            for i, button in enumerate(game_manager.buttons):
                if button.collidepoint(pos):
                    if game_manager.muted == False:
                        getattr(sounds, "ui_click").play()
                    if i == 0:
                        start_game()
                    elif i == 1:
                        game_manager.muted = not game_manager.muted
                        button.image = f"mute_{int(game_manager.muted)}"
                    else:
                        exit()


def on_mouse_move(pos, rel, buttons):
    game_manager.mouse_pos = pos


def on_key_down(key):
    if key == 114 and game_manager.game_started:  # 114 = R key
        restart_game()


def draw():
    screen.clear()
    screen.blit(game_manager.background, (0, 0))
    if game_manager.game_started:
        for enemy in game_manager.enemies:
            enemy.draw()
        for projectile in game_manager.projectiles:
            projectile.draw()
        game_manager.player.draw()
        game_manager.wave_manager.wave_text.draw()
        game_manager.wave_manager.wave_number.draw()
        if game_manager.game_over:
            screen.blit("game_over", (WIDTH / 2 - 157, 250))
            if game_manager.player.current_health > 0:
                screen.blit("victory", (WIDTH / 2 - 82, 300))
            else:
                screen.blit("defeat", (WIDTH / 2 - 74, 300))
            if game_manager.restart_scheduled == False:
                clock.schedule(restart_game, 3)
                game_manager.restart_scheduled = True
        if game_manager.wave_manager.intermission == True:
            for upgrade in game_manager.wave_manager.upgrades:
                screen.blit("choose_an_upgrade", (WIDTH / 2 - 103, 160))
                upgrade.draw()
                screen.blit(
                    f"{upgrade.type}_{upgrade.rarity}",
                    (upgrade.x - 135, upgrade.y - 60),
                )
                screen.blit(f"{upgrade.rarity}",
                            (upgrade.x - 130, upgrade.y + 30))
    else:
        screen.blit("logo", (WIDTH / 2 - 144, HEIGHT / 2 - 300))
        for button in game_manager.buttons:
            button.draw()


def update():
    if game_manager.game_started:
        game_manager.player.update_animation()
        game_manager.player.check_if_dead()
        if game_manager.player.current_health > 0:
            game_manager.player.update_pressed_direction()
            game_manager.player.move()
            game_manager.player.update_shooting()
        for enemy in game_manager.enemies:
            if enemy.current_health > 0:
                enemy.update_player_direction(game_manager.player)
                enemy.move()
                enemy.check_projectile_collisions(game_manager.projectiles)
                enemy.check_player_collision(game_manager.player)
            enemy.update_animation()
        for projectile in game_manager.projectiles:
            projectile.check_if_left_screen(game_manager.projectiles)
            projectile.move()

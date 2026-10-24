import math
import random
import sys

import pygame


WIDTH = 960
HEIGHT = 540
GROUND_Y = 430
PLAYER_SPEED = 260
GRAVITY = 1800
JUMP_FORCE = 620
BULLET_SPEED = 700
ENEMY_SPEED = 110
MAX_WORLD_X = 3600


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = 26
        self.h = 46
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.facing = 1
        self.fire_cooldown = 0.0
        self.health = 100
        self.invuln = 0.0

    def update(self, dt, keys):
        self.vx = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vx -= PLAYER_SPEED
            self.facing = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vx += PLAYER_SPEED
            self.facing = 1

        if (keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_SPACE]) and self.on_ground:
            self.vy = -JUMP_FORCE
            self.on_ground = False

        self.vy += GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.y + self.h >= GROUND_Y:
            self.y = GROUND_Y - self.h
            self.vy = 0
            self.on_ground = True
        else:
            self.on_ground = False

        self.x = max(40, min(self.x, MAX_WORLD_X - 40))
        self.fire_cooldown = max(0.0, self.fire_cooldown - dt)
        self.invuln = max(0.0, self.invuln - dt)

    def shoot(self, bullets):
        if self.fire_cooldown > 0:
            return
        self.fire_cooldown = 0.12
        offset_x = self.x + self.w / 2 + self.facing * 18
        offset_y = self.y + self.h / 2 - 8
        bullets.append({
            "x": offset_x,
            "y": offset_y,
            "w": 12,
            "h": 5,
            "vx": self.facing * BULLET_SPEED,
            "vy": 0,
            "life": 1.1,
            "color": (245, 240, 95),
        })

    def draw(self, screen, camera_x):
        px = self.x - camera_x
        rect = pygame.Rect(px, self.y, self.w, self.h)
        if self.invuln > 0 and math.sin(pygame.time.get_ticks() / 50) > 0:
            color = (220, 220, 255)
        else:
            color = (48, 200, 110)
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, (15, 30, 18), (px + 8, self.y + 8, 10, 12))
        pygame.draw.rect(screen, (255, 255, 255), (px + self.w - 6, self.y + 8, 6, 6))


class Enemy:
    def __init__(self, x, y, kind):
        self.x = x
        self.y = y
        self.kind = kind
        self.w = 24 if kind == "walker" else 22
        self.h = 28 if kind == "walker" else 22
        self.vx = -(ENEMY_SPEED + random.random() * 40)
        self.health = 2 if kind == "walker" else 1
        self.bounce = random.random() * math.pi * 2

    def update(self, dt, player):
        if self.kind == "walker":
            self.x += self.vx * dt
            self.y = GROUND_Y - self.h
            if self.x < player.x - 140:
                self.vx = -self.vx
        else:
            self.x += self.vx * dt
            self.y = GROUND_Y - 120 + math.sin(self.bounce + pygame.time.get_ticks() / 180.0) * 26

    def draw(self, screen, camera_x):
        px = self.x - camera_x
        color = (220, 90, 90) if self.kind == "walker" else (220, 150, 80)
        pygame.draw.rect(screen, color, pygame.Rect(px, self.y, self.w, self.h))
        pygame.draw.rect(screen, (50, 20, 20), (px + 6, self.y + 6, 6, 6))
        pygame.draw.rect(screen, (50, 20, 20), (px + self.w - 12, self.y + 6, 6, 6))


class Explosion:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.life = 0.6
        self.particles = []
        for _ in range(12):
            angle = random.random() * math.tau
            speed = random.random() * 130 + 40
            self.particles.append({
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "size": random.randint(2, 5),
            })

    def update(self, dt):
        self.life -= dt
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += 220 * dt

    def draw(self, screen, camera_x):
        for p in self.particles:
            pygame.draw.rect(screen, self.color, (p["x"] - camera_x, p["y"], p["size"], p["size"]))


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pixel Strike")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 30)
        self.big_font = pygame.font.Font(None, 78)
        self.running = True
        self.started = False
        self.game_over = False
        self.score = 0
        self.camera_x = 0

        self.player = Player(120, GROUND_Y - 46)
        self.bullets = []
        self.enemies = []
        self.explosions = []
        self.spawn_timer = 0.7

    def reset(self):
        self.score = 0
        self.player = Player(120, GROUND_Y - 46)
        self.bullets = []
        self.enemies = []
        self.explosions = []
        self.spawn_timer = 0.7
        self.camera_x = 0
        self.game_over = False
        self.started = True

    def spawn_enemy(self):
        kind = random.choice(["walker", "walker", "flyer"])
        x = min(MAX_WORLD_X - 80, self.camera_x + WIDTH + random.randint(30, 180))
        y = GROUND_Y - 30 if kind == "walker" else GROUND_Y - 120
        self.enemies.append(Enemy(x, y, kind))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.type == pygame.KEYDOWN and not self.started:
                self.reset()
            elif event.type == pygame.KEYDOWN and self.game_over and event.key == pygame.K_r:
                self.reset()

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if not self.started:
            return

        if self.game_over:
            return

        self.player.update(dt, keys)
        if keys[pygame.K_j] or keys[pygame.K_k]:
            self.player.shoot(self.bullets)

        self.camera_x = max(0, min(self.player.x - WIDTH * 0.35, MAX_WORLD_X - WIDTH))

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_enemy()
            self.spawn_timer = max(0.5, 1.8 - self.score / 180.0)

        for bullet in self.bullets[:]:
            bullet["x"] += bullet["vx"] * dt
            bullet["y"] += bullet["vy"] * dt
            bullet["life"] -= dt
            if bullet["life"] <= 0 or bullet["x"] < -50 or bullet["x"] > MAX_WORLD_X + 50:
                self.bullets.remove(bullet)

        for enemy in self.enemies[:]:
            enemy.update(dt, self.player)
            if enemy.x < -40:
                self.enemies.remove(enemy)
                continue

            if enemy.x < self.player.x + self.player.w and enemy.x + enemy.w > self.player.x:
                if enemy.y < self.player.y + self.player.h and enemy.y + enemy.h > self.player.y:
                    if self.player.invuln <= 0:
                        self.player.health -= 15
                        self.player.invuln = 1.0
                        self.explosions.append(Explosion(self.player.x + self.player.w / 2, self.player.y + self.player.h / 2, (255, 70, 70)))
                        if self.player.health <= 0:
                            self.game_over = True

        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                if bullet["x"] < enemy.x + enemy.w and bullet["x"] + bullet["w"] > enemy.x:
                    if bullet["y"] < enemy.y + enemy.h and bullet["y"] + bullet["h"] > enemy.y:
                        self.bullets.remove(bullet)
                        enemy.health -= 1
                        self.explosions.append(Explosion(enemy.x + enemy.w / 2, enemy.y + enemy.h / 2, (255, 190, 50)))
                        if enemy.health <= 0:
                            self.enemies.remove(enemy)
                            self.score += 10
                        break

        for explosion in self.explosions[:]:
            explosion.update(dt)
            if explosion.life <= 0:
                self.explosions.remove(explosion)

    def draw_background(self):
        self.screen.fill((12, 18, 32))
        for i in range(0, 5):
            color = (18 + i * 6, 24 + i * 8, 40 + i * 10)
            pygame.draw.rect(self.screen, color, (0, 0, WIDTH, HEIGHT))

        for i in range(12):
            cloud_x = (i * 170 - self.camera_x * 0.2) % (WIDTH + 160) - 80
            cloud_y = 50 + (i % 4) * 30
            pygame.draw.rect(self.screen, (170, 185, 220), (cloud_x, cloud_y, 100, 24))
            pygame.draw.rect(self.screen, (170, 185, 220), (cloud_x + 18, cloud_y - 12, 58, 24))

        for i in range(12):
            hill_offset = (i * 160 - self.camera_x * 0.5) % (WIDTH + 200) - 100
            pygame.draw.polygon(self.screen, (40, 68, 84), [(hill_offset, HEIGHT), (hill_offset + 90, 300), (hill_offset + 200, HEIGHT)])

        ground_top = GROUND_Y
        pygame.draw.rect(self.screen, (34, 58, 44), (0, ground_top, WIDTH, HEIGHT - ground_top))
        for x in range(-10, WIDTH + 20, 24):
            pixel_x = x - (self.camera_x % 24)
            pygame.draw.rect(self.screen, (70, 98, 64), (pixel_x, ground_top + 18, 18, 18))
            pygame.draw.rect(self.screen, (118, 158, 96), (pixel_x, ground_top + 8, 18, 10))

    def draw_hud(self):
        health_bar = pygame.Rect(20, 18, 180, 18)
        pygame.draw.rect(self.screen, (40, 40, 40), health_bar)
        inner = pygame.Rect(20, 18, 180 * max(0, self.player.health / 100), 18)
        pygame.draw.rect(self.screen, (90, 220, 120), inner)
        score_surf = self.font.render(f"SCORE: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_surf, (WIDTH - 170, 20))

    def draw_title_screen(self):
        title = self.big_font.render("PIXEL STRIKE", True, (255, 255, 255))
        subtitle = self.font.render("Press any key to start", True, (220, 220, 220))
        tip = self.font.render("Move: A/D or arrows   Jump: W/Space   Shoot: J/K", True, (180, 200, 255))
        self.screen.blit(title, (WIDTH / 2 - title.get_width() / 2, 150))
        self.screen.blit(subtitle, (WIDTH / 2 - subtitle.get_width() / 2, 260))
        self.screen.blit(tip, (WIDTH / 2 - tip.get_width() / 2, 300))

    def draw_game_over(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((20, 20, 20, 160))
        self.screen.blit(overlay, (0, 0))
        text = self.big_font.render("MISSION FAILED", True, (255, 120, 120))
        help_text = self.font.render("Press R to restart", True, (255, 255, 255))
        self.screen.blit(text, (WIDTH / 2 - text.get_width() / 2, 180))
        self.screen.blit(help_text, (WIDTH / 2 - help_text.get_width() / 2, 260))

    def draw(self):
        self.draw_background()

        if not self.started:
            self.draw_title_screen()
            pygame.display.flip()
            return

        for explosion in self.explosions:
            explosion.draw(self.screen, self.camera_x)

        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera_x)

        for bullet in self.bullets:
            pygame.draw.rect(self.screen, bullet["color"], (bullet["x"] - self.camera_x, bullet["y"], bullet["w"], bullet["h"]))

        self.player.draw(self.screen, self.camera_x)
        self.draw_hud()

        if self.game_over:
            self.draw_game_over()

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()


"""
Classic Contra-inspired side-scroller playground.
"""

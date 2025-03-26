import pygame
import random
import math
import sys

pygame.init()
WIDTH, HEIGHT = 800, 600  
FPS = 60
NODE_RADIUS = 20

PLAYER_COLOR = (0, 255, 0)          # bright green (for reference)
NODE_COLOR = (210, 180, 140)        # tan/cream for nodes (better on brown)
EDGE_COLOR = (80, 80, 80)           # dark gray for edges
HIGHLIGHT_COLOR = (255, 215, 0)     # warm gold for highlighting adjacent rooms
ARROW_COLOR = (255, 255, 0)         # bright yellow for the arrow
BG_COLOR = (80, 40, 20)             # dark brown background (if used)
TEXT_COLOR = (255, 255, 255)        # white text for high contrast


screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Hunt the Wumpus")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 18)
big_font = pygame.font.SysFont("Arial", 48, bold=True)  

#load image assets
background_img = pygame.image.load("assests/cave_background4.jpg").convert()
player_img = pygame.image.load("assests/player2.png").convert_alpha()
arrow_img = pygame.image.load("assests/arrow2.png").convert_alpha()
wumpus_img = pygame.image.load("assests/wumpus.png").convert_alpha()
bat_img = pygame.image.load("assests/batflap.gif").convert_alpha()
pit_img = pygame.image.load("assests/pit1.png").convert_alpha()

pygame.mixer.init()
pygame.mixer.music.load("assests/cave.mp3")
pygame.mixer.music.play(-1) 

player_move_sound = pygame.mixer.Sound("assests/player_move.wav")
won_sound = pygame.mixer.Sound("assests/won.wav")
shoot_sound = pygame.mixer.Sound("assests/shoot.mp3")
wumpus_sound = pygame.mixer.Sound("assests/wumpus.wav")
bat_sound = pygame.mixer.Sound("assests/bat.ogg")
pit_loss_sound = pygame.mixer.Sound("assests/pit_sound.mp3")

# grid parameters
rows, cols = 4, 5
fixed_margin_x, fixed_margin_y = 100, 100

def update_grid_positions():
   
    current_width, current_height = screen.get_size()
    margin_x = fixed_margin_x
    margin_y = fixed_margin_y
    spacing_x = (current_width - 2 * margin_x) / (cols - 1)
    spacing_y = (current_height - 2 * margin_y) / (rows - 1)
    positions = {}
    room_number = 1
    for r in range(rows):
        for c in range(cols):
            x = margin_x + c * spacing_x
            y = margin_y + r * spacing_y
            positions[room_number] = (int(x), int(y))
            room_number += 1
    return positions, (current_width // 2, current_height // 2)

rooms_positions, screen_center = update_grid_positions()

CAVE = {}
for room in range(1, rows * cols + 1):
    neighbors = []
    row = (room - 1) // cols
    col = (room - 1) % cols
    if col > 0:
        neighbors.append(room - 1)
    if col < cols - 1:
        neighbors.append(room + 1)
    if row > 0:
        neighbors.append(room - cols)
    if row < rows - 1:
        neighbors.append(room + cols)
    CAVE[room] = neighbors

def show_home_screen():
    
    home_running = True
    instructions = [
         "HUNT THE WUMPUS",
         "",
         "INSTRUCTIONS:",
         " - Press 'M' to move: click a highlighted adjacent room.",
         " - Press 'S' to shoot: select adjacent rooms for the arrow path, then press Enter.",
         " - Press 'R' to reset the game.",
         "",
         "RULES:",
         " - Avoid hazards:",
         "   * Pits: instant defeat.",
         "   * Bats: 10% chance to drop you into a pit or Wumpus room.",
         "   * Wumpus: entering its room loses the game.",
         " - Extra arrows: 15% chance to find one in safe rooms.",
         "",
         "GOAL:",
         " - Hunt the Wumpus with your arrows before it catches you!",
         "",
         "Press any key to begin..."
    ]
    while home_running:
        current_width, current_height = screen.get_size()
        screen.blit(background_img, (0, 0))
        y_offset = 80
        for line in instructions:
            if line == "HUNT THE WUMPUS":
                line_surface = big_font.render(line, True, (255, 215, 0))
            else:
                line_surface = font.render(line, True, (255, 255, 255))
            line_rect = line_surface.get_rect(center=(current_width // 2, y_offset))
            screen.blit(line_surface, line_rect)
            y_offset += 30
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                home_running = False
        clock.tick(FPS)

class HuntTheWumpusGame:
    def __init__(self):
        self.reset_game()

    def reset_game(self):

        valid_rooms = [r for r in CAVE if r not in (1, 2, 6)] # exclude rooms 1, 2, and 6 for hazards.
        self.wumpus = random.choice(valid_rooms)
        self.pits = random.sample([r for r in CAVE if r not in (1, 2, 6, self.wumpus)], 2)
        remaining = [r for r in CAVE if r not in (1, 2, 6, self.wumpus) and r not in self.pits]
        self.bats = random.sample(remaining, 2)
        
        self.player = 1 # start from room 1
        self.arrows = 2  #has 2 arrows
        self.game_over = False
        self.message = "Welcome! (M)ove or (S)hoot. Click an adjacent room to move."
        self.mode = "MOVE"
        self.shoot_path = []
        self.awaiting_shoot = False

    def draw_cave(self):
        global rooms_positions, screen_center
        rooms_positions, screen_center = update_grid_positions()
        screen.blit(background_img, (0, 0))
        for room, neighbors in CAVE.items():
            for neighbor in neighbors:
                start = rooms_positions[room]
                end = rooms_positions[neighbor]
                pygame.draw.line(screen, EDGE_COLOR, start, end, 2)
        for room, pos in rooms_positions.items():
            pygame.draw.circle(screen, NODE_COLOR, pos, NODE_RADIUS)
            text = font.render(str(room), True, TEXT_COLOR)
            screen.blit(text, (pos[0] - text.get_width() // 2, pos[1] - text.get_height() // 2))
        player_pos = rooms_positions[self.player]
        screen.blit(player_img, (player_pos[0] - player_img.get_width() // 2, player_pos[1] - player_img.get_height() // 2))
        if self.mode == "MOVE":
            for neighbor in CAVE[self.player]:
                pos = rooms_positions[neighbor]
                pygame.draw.circle(screen, HIGHLIGHT_COLOR, pos, NODE_RADIUS, 3)
        if self.mode == "SHOOT" and self.awaiting_shoot:
            for room in self.shoot_path:
                pos = rooms_positions[room]
                pygame.draw.circle(screen, (255, 165, 0), pos, NODE_RADIUS, 3)

    def get_warnings(self):
        warnings = []
        for room in CAVE[self.player]:
            if room == self.wumpus:
                warnings.append("You smell a terrible stench.")
            if room in self.pits:
                warnings.append("A cold wind blows from a pit.")
            if room in self.bats:
                warnings.append("You hear flapping nearby.")
        return list(set(warnings))

    def animate_move(self, start_room, end_room):
        start_pos = rooms_positions[start_room]
        end_pos = rooms_positions[end_room]
        steps = 30
        for i in range(steps):
            t = i / steps
            interp = (int(start_pos[0] + t * (end_pos[0] - start_pos[0])),
                      int(start_pos[1] + t * (end_pos[1] - start_pos[1])))
            screen.blit(background_img, (0, 0))
            self.draw_cave()
            screen.blit(player_img, (interp[0] - player_img.get_width() // 2, interp[1] - player_img.get_height() // 2))
            pygame.display.flip()
            clock.tick(FPS)
        player_move_sound.play()

    def animate_arrow(self, path):
        current_pos = screen_center
        shoot_sound.play()
        for room in path:
            target_pos = rooms_positions[room]
            steps = 20
            for i in range(steps):
                t = i / steps
                interp = (int(current_pos[0] + t * (target_pos[0] - current_pos[0])),
                          int(current_pos[1] + t * (target_pos[1] - current_pos[1])))
                screen.blit(background_img, (0, 0))
                self.draw_cave()
                screen.blit(arrow_img, (interp[0] - arrow_img.get_width() // 2, interp[1] - arrow_img.get_height() // 2))
                pygame.display.flip()
                clock.tick(FPS)
            current_pos = target_pos

    def process_player_move(self, dest):
        if dest not in CAVE[self.player]:
            self.message = "Invalid move! Choose an adjacent room."
            return
        start_room = self.player
        self.animate_move(start_room, dest)
        self.player = dest
        self.check_current_room()

    def check_current_room(self):
        pos = rooms_positions[self.player]
        if self.player == self.wumpus:
            self.message = "Oh no! You encountered the Wumpus! Game Over."
            screen.blit(wumpus_img, (screen_center[0] - wumpus_img.get_width() // 2,
                                     screen_center[1] - wumpus_img.get_height() // 2))
            pygame.display.flip()
            wumpus_sound.play()
            pygame.time.delay(3000)
            self.game_over = True
        elif self.player in self.pits:
            self.message = "You fell into a pit! Game Over."
            screen.blit(pit_img, (pos[0] - pit_img.get_width() // 2, pos[1] - pit_img.get_height() // 2))
            pygame.display.flip()
            pit_loss_sound.play()
            pygame.time.delay(3000)
            self.game_over = True
        elif self.player in self.bats:
            if random.random() < 0.10:  # 10% chance to drop into a hazard
                hazard = random.choice(self.pits + [self.wumpus])
                self.message = "Bats throw you into a hazard!"
                self.animate_move(self.player, hazard)
                self.player = hazard
                self.check_current_room()
            else:
                self.message = "Bats whisk you away!"
                screen.blit(bat_img, (pos[0] - bat_img.get_width() // 2, pos[1] - bat_img.get_height() // 2))
                pygame.display.flip()
                bat_sound.play()
                pygame.time.delay(3000)
                random_room = random.choice(list(CAVE.keys()))
                self.animate_move(self.player, random_room)
                self.player = random_room
                self.check_current_room()
        else:
            self.message = f"You are in room {self.player}. Arrows left: {self.arrows}"
            warnings = self.get_warnings()
            if warnings:
                self.message += " | " + " ".join(warnings)
            if random.random() < 0.15:
                self.arrows += 1
                self.message += " | You found an arrow!"

    def process_shoot(self):
        if self.arrows <= 0:
            self.message = "You're out of arrows!"
            return
        self.arrows -= 1
        self.animate_arrow(self.shoot_path)
        current_room = self.player
        hit = False
        for room in self.shoot_path:
            if room not in CAVE[current_room]:
                room = random.choice(CAVE[current_room])
            current_room = room
            if current_room == self.wumpus:
                hit = True
                break
        if hit:
            self.message = "Your arrow hit the Wumpus! You win the gold!"
            won_sound.play()
            self.game_over = True
        else:
            self.message = "Your arrow missed. The Wumpus is still out there!"
            if random.random() < 0.75:
                self.wumpus = random.choice(list(CAVE.keys()))
                self.message += " The Wumpus has moved!"

    def update(self):
        msg_surface = font.render(self.message, True, TEXT_COLOR)
        rect_width = screen.get_width() - 20
        rect_height = 40
        msg_bg = pygame.Surface((rect_width, rect_height))
        msg_bg.set_alpha(200)
        msg_bg.fill((0, 0, 0))
        screen.blit(msg_bg, (10, screen.get_height() - rect_height - 10))
        screen.blit(msg_surface, (15, screen.get_height() - rect_height))

def main():
    show_home_screen()
    game = HuntTheWumpusGame()
    running = True
    while running:
        screen.blit(background_img, (0, 0))
        game.draw_cave()
        game.update()
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    game.mode = "MOVE"
                    game.message = "Move mode: Click an adjacent highlighted room to move."
                    game.awaiting_shoot = False
                    game.shoot_path = []
                elif event.key == pygame.K_s:
                    game.mode = "SHOOT"
                    game.message = "Shoot mode: Click adjacent rooms to add to arrow path. Press Enter to fire."
                    game.awaiting_shoot = True
                    game.shoot_path = []
                elif event.key == pygame.K_RETURN and game.mode == "SHOOT" and game.awaiting_shoot:
                    if len(game.shoot_path) == 0:
                        game.message = "No rooms selected for shooting."
                    else:
                        game.process_shoot()
                        game.mode = "MOVE"
                        game.awaiting_shoot = False
                        game.shoot_path = []
                elif event.key == pygame.K_r:
                    game.reset_game()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for room, pos in rooms_positions.items():
                    dx = mouse_pos[0] - pos[0]
                    dy = mouse_pos[1] - pos[1]
                    if dx * dx + dy * dy <= NODE_RADIUS ** 2:
                        if game.mode == "MOVE":
                            if room in CAVE[game.player]:
                                game.process_player_move(room)
                            else:
                                game.message = "You can only move to adjacent rooms!"
                        elif game.mode == "SHOOT" and game.awaiting_shoot:
                            if len(game.shoot_path) == 0:
                                valid_adj = CAVE[game.player]
                            else:
                                valid_adj = CAVE[game.shoot_path[-1]]
                            if room in valid_adj:
                                game.shoot_path.append(room)
                                game.message = f"Added room {room} to arrow path. Press Enter when done."
                            else:
                                game.message = "Invalid room for arrow path. Must be adjacent."
        if game.game_over:
            overlay = pygame.Surface((screen.get_width(), screen.get_height()))
            overlay.set_alpha(180)
            overlay.fill((50, 50, 50))
            screen.blit(overlay, (0, 0))
            game_over_text = big_font.render("GAME OVER", True, (255, 0, 0))
            game_over_rect = game_over_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 - 50))
            screen.blit(game_over_text, game_over_rect)
            outcome_text = font.render(game.message, True, (255, 255, 255))
            outcome_rect = outcome_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 10))
            screen.blit(outcome_text, outcome_rect)
            restart_text = font.render("Press R to restart or Q to quit.", True, (255, 255, 255))
            restart_rect = restart_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 50))
            screen.blit(restart_text, restart_rect)
            pygame.display.flip()
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        waiting = False
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            game.reset_game()
                            waiting = False
                        elif event.key == pygame.K_q:
                            waiting = False
                            running = False
                clock.tick(FPS)
        clock.tick(FPS)
    pygame.mixer.music.stop()  # stop music before quitting
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

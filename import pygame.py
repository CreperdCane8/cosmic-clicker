import pygame
import sys
import random
import time
import math

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60
SPECIAL_EVENT_INTERVAL = 420  # 7 minutes in seconds

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 100, 255)
GREEN = (0, 255, 100)
RED = (255, 50, 50)
YELLOW = (255, 255, 0)
PURPLE = (180, 0, 180)
ORANGE = (255, 150, 0)
GRAY = (100, 100, 100) 
PLANET_COLOR = (70, 130, 180)
SPECIAL_ORB_COLOR = (255, 215, 0)

# Game setup
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Cosmic Clicker Deluxe")
clock = pygame.time.Clock()

# Game states
MENU = 0
PLAYING = 1
PAUSED = 2
game_state = MENU

# Game variables
score = 0
click_power = 1
auto_clickers = 0
click_multiplier = 1
crit_chance = 0  # 0-100%
crit_power = 2
time_played = 0
special_orb_active = False
special_orb_pos = (0, 0)
special_orb_timer = 0
particles = []
planet_particles = []
stars = []

# Planet
planet_radius = 50
planet_pos = (WIDTH//2, HEIGHT//2)
special_orb_radius = 30

# Upgrades (name: [base_cost, cost_multiplier, description])
upgrades = {
    "Auto-Clicker": [15, 1.5, "Generates 1 click per second"],
    "Click Power": [50, 1.8, "+1 base click power"],
    "Click Multiplier": [100, 2.0, "Multiply all clicks by 1.5x"],
    "Critical Chance": [75, 1.7, "+5% chance for critical hits"],
    "Critical Power": [150, 2.2, "Critical hits do 3x damage"],
    "Particle Boost": [200, 1.9, "More particles per click"],
    "Time Warp": [300, 2.5, "Auto-clickers work 20% faster"],
    "Lucky Strikes": [250, 2.0, "10% chance for 5x clicks"]
}

# Initialize upgrade tracking
for name in upgrades:
    upgrades[name].extend([0, upgrades[name][0]])  # [owned, current_cost]

def create_stars(count):
    return [{
        "x": random.randint(0, WIDTH),
        "y": random.randint(0, HEIGHT),
        "size": random.randint(1, 3),
        "speed": random.uniform(0.5, 2)
    } for _ in range(count)]

def spawn_particle(x, y, color=None, size=None, life=None):
    particles.append({
        "x": x,
        "y": y,
        "color": color or random.choice([WHITE, BLUE, GREEN, RED, YELLOW, PURPLE, ORANGE]),
        "size": size or random.randint(2, 5),
        "life": life or random.randint(20, 40),
        "dx": random.uniform(-1, 1),
        "dy": random.uniform(-1, 1)
    })

def spawn_planet_particles(x, y, count=15):
    for _ in range(count):
        angle = random.uniform(0, math.pi*2)
        speed = random.uniform(1, 3)
        planet_particles.append({
            "x": x,
            "y": y,
            "dx": math.cos(angle) * speed,
            "dy": math.sin(angle) * speed,
            "color": (random.randint(100, 200), random.randint(100, 200), random.randint(200, 255)),
            "size": random.randint(2, 4),
            "life": random.randint(20, 40)
        })

def draw_button(rect, color, text, text_color=WHITE):
    pygame.draw.rect(screen, color, rect, border_radius=8)
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)

def reset_game():
    global score, click_power, auto_clickers, click_multiplier, crit_chance, time_played
    global special_orb_active, particles, planet_particles
    
    score = 0
    click_power = 1
    auto_clickers = 0
    click_multiplier = 1
    crit_chance = 0
    time_played = 0
    special_orb_active = False
    particles = []
    planet_particles = []
    
    # Reset upgrades
    for name in upgrades:
        upgrades[name][3] = 0  # owned
        upgrades[name][4] = upgrades[name][0]  # reset cost

# Initialize game elements
stars = create_stars(200)
font = pygame.font.SysFont("Arial", 24)
large_font = pygame.font.SysFont("Arial", 48)
title_font = pygame.font.SysFont("Arial", 72)
small_font = pygame.font.SysFont("Arial", 18)

# Main game loop
running = True
last_time = time.time()
last_special_event = 0

while running:
    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time
    
    # Handle window resize while maintaining aspect ratio
    if pygame.display.get_surface().get_size() != (WIDTH, HEIGHT):
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    
    mouse_pos = pygame.mouse.get_pos()
    planet_pos = (WIDTH//2, HEIGHT//2)
    
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                if screen.get_flags() & pygame.FULLSCREEN:
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                else:
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
            elif event.key == pygame.K_p and game_state == PLAYING:
                game_state = PAUSED
            elif event.key == pygame.K_p and game_state == PAUSED:
                game_state = PLAYING
            elif event.key == pygame.K_ESCAPE:
                if game_state == PLAYING:
                    game_state = PAUSED
                elif game_state == PAUSED:
                    game_state = PLAYING
                elif game_state == MENU:
                    running = False
        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game_state == MENU:
                if start_button.collidepoint(mouse_pos):
                    reset_game()
                    game_state = PLAYING
                elif quit_button.collidepoint(mouse_pos):
                    running = False
            
            elif game_state == PLAYING:
                # Check planet click
                if math.dist(mouse_pos, planet_pos) <= planet_radius:
                    base_value = click_power * click_multiplier
                    
                    # Check for critical hit
                    is_critical = random.randint(1, 100) <= crit_chance
                    if is_critical:
                        base_value *= crit_power
                    
                    # Check for lucky strike
                    is_lucky = upgrades["Lucky Strikes"][3] > 0 and random.randint(1, 100) <= 10
                    if is_lucky:
                        base_value *= 5
                    
                    score += base_value
                    spawn_planet_particles(*planet_pos, 10 + upgrades["Particle Boost"][3] * 5)
                    spawn_particle(*mouse_pos)
                
                # Check special orb click
                elif special_orb_active and math.dist(mouse_pos, special_orb_pos) <= special_orb_radius:
                    score += 100 * click_power * click_multiplier
                    special_orb_active = False
                    for _ in range(30):
                        spawn_particle(*special_orb_pos, SPECIAL_ORB_COLOR, 5, 60)
                
                # Check upgrade buttons
                for i, (name, upgrade) in enumerate(upgrades.items()):
                    if upgrade_buttons[i].collidepoint(mouse_pos) and score >= upgrade[4]:
                        score -= upgrade[4]
                        upgrade[3] += 1
                        upgrade[4] = int(upgrade[0] * (upgrade[1] ** upgrade[3]))
                        
                        # Apply upgrade effects
                        if name == "Auto-Clicker":
                            auto_clickers += 1
                        elif name == "Click Power":
                            click_power += 1
                        elif name == "Click Multiplier":
                            click_multiplier *= 1.5
                        elif name == "Critical Chance":
                            crit_chance += 5
                        elif name == "Critical Power":
                            crit_power = 3
                        elif name == "Time Warp":
                            pass  # Handled in auto-clicker calculation
            
            elif game_state == PAUSED:
                if resume_button.collidepoint(mouse_pos):
                    game_state = PLAYING
                elif menu_button.collidepoint(mouse_pos):
                    game_state = MENU
    
    # Game logic
    if game_state == PLAYING:
        time_played += delta_time
        
        # Auto-clickers (with Time Warp boost)
        if auto_clickers > 0:
            time_warp_factor = 1 + (0.2 * upgrades["Time Warp"][3])
            score += auto_clickers * delta_time * click_multiplier * time_warp_factor
        
        # Special orb event
        if not special_orb_active and time_played - last_special_event >= SPECIAL_EVENT_INTERVAL:
            special_orb_active = True
            last_special_event = time_played
            special_orb_pos = (
                random.randint(special_orb_radius, WIDTH - special_orb_radius),
                random.randint(special_orb_radius, HEIGHT - special_orb_radius)
            )
            special_orb_timer = 10  # 10 seconds to click
        
        elif special_orb_active:
            special_orb_timer -= delta_time
            if special_orb_timer <= 0:
                special_orb_active = False
        
        # Update particles
        for particle in particles[:]:
            particle["x"] += particle["dx"]
            particle["y"] += particle["dy"]
            particle["life"] -= 1
            if particle["life"] <= 0:
                particles.remove(particle)
        
        for particle in planet_particles[:]:
            particle["x"] += particle["dx"]
            particle["y"] += particle["dy"]
            particle["life"] -= 1
            if particle["life"] <= 0:
                planet_particles.remove(particle)
        
        # Update stars
        for star in stars:
            star["y"] += star["speed"]
            if star["y"] > HEIGHT:
                star["y"] = 0
                star["x"] = random.randint(0, WIDTH)
    
    # Drawing
    screen.fill(BLACK)
    
    # Draw stars
    for star in stars:
        pygame.draw.circle(screen, WHITE, (int(star["x"]), int(star["y"])), star["size"])
    
    # Draw particles
    for particle in particles:
        alpha = min(255, particle["life"] * 6)
        color = (*particle["color"][:3], alpha) if len(particle["color"]) == 3 else particle["color"]
        particle_surface = pygame.Surface((particle["size"]*2, particle["size"]*2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surface, color, (particle["size"], particle["size"]), particle["size"])
        screen.blit(particle_surface, (particle["x"] - particle["size"], particle["y"] - particle["size"]))
    
    for particle in planet_particles:
        alpha = min(255, particle["life"] * 6)
        color = (*particle["color"], alpha)
        particle_surface = pygame.Surface((particle["size"]*2, particle["size"]*2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surface, color, (particle["size"], particle["size"]), particle["size"])
        screen.blit(particle_surface, (particle["x"] - particle["size"], particle["y"] - particle["size"]))
    
    # Draw game elements based on state
    if game_state == MENU:
        # Title
        title_text = title_font.render("COSMIC CLICKER", True, WHITE)
        screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 100))
        
        # Buttons
        start_button = pygame.Rect(WIDTH//2 - 150, 300, 300, 60)
        quit_button = pygame.Rect(WIDTH//2 - 150, 400, 300, 60)
        
        draw_button(start_button, GREEN, "START GAME")
        draw_button(quit_button, RED, "QUIT")
        
        # Instructions
        instr_text = font.render("Press F11 to toggle fullscreen", True, WHITE)
        screen.blit(instr_text, (WIDTH//2 - instr_text.get_width()//2, 500))
    
    elif game_state == PLAYING or game_state == PAUSED:
        # Draw planet
        pygame.draw.circle(screen, PLANET_COLOR, planet_pos, planet_radius)
        pygame.draw.circle(screen, (100, 180, 255), planet_pos, planet_radius - 15)
        
        # Draw special orb if active
        if special_orb_active:
            pulse = math.sin(time_played * 5) * 5 + 25
            pygame.draw.circle(screen, SPECIAL_ORB_COLOR, special_orb_pos, int(special_orb_radius + pulse))
            timer_text = font.render(f"{int(special_orb_timer)}s", True, WHITE)
            screen.blit(timer_text, (special_orb_pos[0] - timer_text.get_width()//2, 
                                   special_orb_pos[1] - special_orb_radius - 30))
        
        # Game stats
        stats = [
            f"Score: {int(score)}",
            f"Click Power: {click_power} x{click_multiplier:.1f}",
            f"Crit: {crit_chance}% (x{crit_power})",
            f"Auto-Clickers: {auto_clickers}",
            f"Play Time: {int(time_played//60)}m {int(time_played%60)}s"
        ]
        
        for i, stat in enumerate(stats):
            text = font.render(stat, True, WHITE)
            screen.blit(text, (20, 20 + i * 30))
        
        # Upgrade buttons
        upgrade_buttons = []
        for i, (name, upgrade) in enumerate(upgrades.items()):
            button_rect = pygame.Rect(WIDTH - 250 if i < 4 else WIDTH - 250, 
                                    20 + (i % 4) * 100 if i < 4 else 20 + (i % 4) * 100 + 200, 
                                    230, 80)
            upgrade_buttons.append(button_rect)
            
            # Button color based on affordability
            color = GREEN if score >= upgrade[4] else GRAY
            
            # Button text
            lines = [
                f"{name} ({upgrade[4]})",
                f"Owned: {upgrade[3]}",
                upgrade[2]
            ]
            
            # Draw button and text
            pygame.draw.rect(screen, color, button_rect, border_radius=8)
            for j, line in enumerate(lines):
                text = small_font.render(line, True, WHITE)
                screen.blit(text, (button_rect.x + 10, button_rect.y + 5 + j * 20))
        
        # Pause overlay
        if game_state == PAUSED:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            pause_text = large_font.render("PAUSED", True, WHITE)
            screen.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2, HEIGHT//2 - 100))
            
            resume_button = pygame.Rect(WIDTH//2 - 150, HEIGHT//2, 300, 60)
            menu_button = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 100, 300, 60)
            
            draw_button(resume_button, GREEN, "RESUME")
            draw_button(menu_button, BLUE, "MAIN MENU")
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
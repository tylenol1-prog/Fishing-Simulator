import pygame
import random
import math
from enum import Enum

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600

# Colors
WATER_BLUE = (30, 100, 200)
SKY_BLUE = (135, 206, 235)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)

class GameState(Enum):
    IDLE = 1
    CASTING = 2
    WAITING = 3
    HOOK_SET = 4
    REELING = 5

class Fish:
    """Represents a fish in the water"""
    def __init__(self, x, y, species):
        self.x = x
        self.y = y
        self.species = species
        self.size = random.randint(5, 20)
        self.speed = random.uniform(0.5, 3)
        self.direction = random.uniform(0, 2 * math.pi)
        self.bite_chance = random.uniform(0.3, 0.8)
        
        # Species info: (name, color, points)
        self.species_info = {
            "bass": ("Bass", (50, 50, 100), 100),
            "trout": ("Trout", (100, 150, 150), 150),
            "catfish": ("Catfish", (80, 60, 40), 80),
            "goldfish": ("Goldfish", (255, 200, 0), 50),
        }
    
    def update(self):
        """Update fish position"""
        self.x += math.cos(self.direction) * self.speed
        self.y += math.sin(self.direction) * self.speed
        
        # Bounce off water edges
        if self.x < 0 or self.x > SCREEN_WIDTH:
            self.direction = math.pi - self.direction
        if self.y < SCREEN_HEIGHT // 2 or self.y > SCREEN_HEIGHT:
            self.direction = -self.direction
    
    def draw(self, surface):
        """Draw the fish"""
        name, color, _ = self.species_info[self.species]
        pygame.draw.ellipse(surface, color, (self.x - self.size, self.y - self.size//2, self.size * 2, self.size))

class Hook:
    """Represents the fishing hook/bobber"""
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.state = GameState.IDLE
        self.cast_power = 0
        self.target_x = self.x
        self.target_y = self.y
        self.casting_time = 0
        self.wait_time = 0
        self.reel_progress = 0
        self.caught_fish = None
        self.bobber_depth = 0
    
    def update(self, fish_list):
        """Update hook state"""
        if self.state == GameState.CASTING:
            self.casting_time -= 1
            # Move towards target position
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            distance = math.sqrt(dx**2 + dy**2)
            if distance > 5:
                self.x += dx / distance * 8
                self.y += dy / distance * 8
            else:
                self.state = GameState.WAITING
                self.wait_time = 0
        
        elif self.state == GameState.WAITING:
            self.wait_time += 1
            self.bobber_depth = math.sin(self.wait_time / 10) * 5
            
            # Check for fish bites
            for fish in fish_list:
                distance = math.sqrt((fish.x - self.x)**2 + (fish.y - self.y)**2)
                if distance < 40 and random.random() < fish.bite_chance * 0.01:
                    self.state = GameState.HOOK_SET
                    self.caught_fish = fish
                    self.reel_progress = 0
                    break
        
        elif self.state == GameState.REELING:
            self.reel_progress += 2
            # Move hook towards surface
            self.y = max(self.y - 3, 100)
            
            if self.reel_progress >= 100:
                self.state = GameState.IDLE
    
    def cast(self, power, angle):
        """Cast the line"""
        self.cast_power = power
        distance = power * 3
        self.target_x = self.x + math.cos(angle) * distance
        self.target_y = self.y + math.sin(angle) * distance
        
        # Clamp to screen
        self.target_x = max(0, min(SCREEN_WIDTH, self.target_x))
        self.target_y = max(SCREEN_HEIGHT // 2, min(SCREEN_HEIGHT, self.target_y))
        
        self.state = GameState.CASTING
        self.casting_time = 30
    
    def set_hook(self):
        """Set the hook when fish bites"""
        if self.state == GameState.HOOK_SET and self.caught_fish:
            self.state = GameState.REELING
    
    def draw(self, surface):
        """Draw the hook and line"""
        # Draw line from top of screen to hook
        pygame.draw.line(surface, (100, 100, 100), (SCREEN_WIDTH // 2, 20), (self.x, self.y), 2)
        
        # Draw bobber
        pygame.draw.circle(surface, RED, (int(self.x), int(self.y + self.bobber_depth)), 8)
        
        # Draw hook
        pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y + self.bobber_depth + 15)), 4)

class FishingSimulator:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Fishing Simulator")
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.Font(None, 24)
        self.large_font = pygame.font.Font(None, 48)
        
        self.hook = Hook()
        self.fish_list = []
        self.caught_count = 0
        self.total_points = 0
        self.cast_angle = 0
        self.cast_power = 0
        self.casting = False
        
        # Spawn initial fish
        for _ in range(8):
            species = random.choice(["bass", "trout", "catfish", "goldfish"])
            fish = Fish(random.randint(50, SCREEN_WIDTH - 50), 
                       random.randint(SCREEN_HEIGHT // 2 + 50, SCREEN_HEIGHT - 50),
                       species)
            self.fish_list.append(fish)
    
    def handle_input(self):
        """Handle user input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and self.hook.state == GameState.IDLE:
                    self.casting = True
                    self.cast_power = 0
                
                if event.key == pygame.K_SPACE and self.hook.state == GameState.HOOK_SET:
                    self.hook.set_hook()
                
                if event.key == pygame.K_r and self.hook.state == GameState.IDLE:
                    # Reset game
                    self.fish_list.clear()
                    for _ in range(8):
                        species = random.choice(["bass", "trout", "catfish", "goldfish"])
                        fish = Fish(random.randint(50, SCREEN_WIDTH - 50),
                                   random.randint(SCREEN_HEIGHT // 2 + 50, SCREEN_HEIGHT - 50),
                                   species)
                        self.fish_list.append(fish)
            
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE and self.casting:
                    self.casting = False
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    angle = math.atan2(mouse_y - self.hook.y, mouse_x - self.hook.x)
                    self.hook.cast(self.cast_power, angle)
        
        # Increase cast power while holding space
        if self.casting:
            self.cast_power = min(self.cast_power + 1, 100)
    
    def update(self):
        """Update game state"""
        # Update all fish
        for fish in self.fish_list:
            fish.update()
        
        # Update hook
        self.hook.update(self.fish_list)
        
        # Check if fish was caught
        if self.hook.state == GameState.IDLE and self.hook.caught_fish:
            species_info = self.hook.caught_fish.species_info[self.hook.caught_fish.species]
            self.caught_count += 1
            self.total_points += species_info[2]
            
            # Remove caught fish and spawn new one
            if self.hook.caught_fish in self.fish_list:
                self.fish_list.remove(self.hook.caught_fish)
            
            species = random.choice(["bass", "trout", "catfish", "goldfish"])
            new_fish = Fish(random.randint(50, SCREEN_WIDTH - 50),
                           random.randint(SCREEN_HEIGHT // 2 + 50, SCREEN_HEIGHT - 50),
                           species)
            self.fish_list.append(new_fish)
            self.hook.caught_fish = None
    
    def draw(self):
        """Draw everything"""
        # Draw background
        self.screen.fill(SKY_BLUE)
        pygame.draw.rect(self.screen, WATER_BLUE, (0, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
        
        # Draw fish
        for fish in self.fish_list:
            fish.draw(self.screen)
        
        # Draw hook
        self.hook.draw(self.screen)
        
        # Draw UI
        self.draw_ui()
        
        pygame.display.flip()
    
    def draw_ui(self):
        """Draw user interface"""
        # Score
        score_text = self.font.render(f"Fish Caught: {self.caught_count} | Points: {self.total_points}", True, BLACK)
        self.screen.blit(score_text, (10, 10))
        
        # Status
        status_map = {
            GameState.IDLE: "Ready to cast (SPACE + MOUSE)",
            GameState.CASTING: f"Casting... Power: {self.cast_power}%",
            GameState.WAITING: "Waiting for fish...",
            GameState.HOOK_SET: "FISH ON! Press SPACE to reel!",
            GameState.REELING: f"Reeling in... {self.hook.reel_progress}%"
        }
        
        status_text = self.font.render(status_map[self.hook.state], True, WHITE)
        self.screen.blit(status_text, (10, SCREEN_HEIGHT - 30))
        
        # Fish info
        if self.hook.caught_fish:
            species_name = self.hook.caught_fish.species_info[self.hook.caught_fish.species][0]
            fish_text = self.font.render(f"Caught: {species_name}!", True, YELLOW)
            self.screen.blit(fish_text, (SCREEN_WIDTH // 2 - 50, 50))
        
        # Controls info
        controls = self.font.render("R: Reset | ESC: Quit", True, BLACK)
        self.screen.blit(controls, (SCREEN_WIDTH - 200, 10))
    
    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    game = FishingSimulator()
    game.run()

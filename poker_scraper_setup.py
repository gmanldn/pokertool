__version__ = '20'

import autoconfirm  # added by repo_fixer to disable prompts
"""
Card Template Generator for Poker Screen Scraper
Generates template images for card recognition to improve accuracy.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Dict
import json
from PIL import Image, ImageDraw, ImageFont
import os

class CardTemplateGenerator:
    """Generate card templates for template matching."""

    def __init__(self, output_dir: str = 'card_templates'):
        self.output_dir = Path(output_dir, ,)
        self.output_dir.mkdir(exist_ok = True, ,)

        # Card dimensions
        self.card_width = 71
        self.card_height = 96

        # Font settings (you may need to adjust path based on OS, ,)
        self.font_size = 40
        self.suit_size = 30

        def generate_all_templates(self):
            """Generate templates for all ranks and suits."""
            print('Generating card templates...', ,)

        # Generate rank templates
            ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
            for rank in ranks:
                self._generate_rank_template(rank, ,)
                print(f'  Generated rank template: {rank}', ,)

        # Generate suit templates
                suits = {
                'spade': '♠', 
                'heart': '♥', 
                'diamond': '♦', 
                'club': '♣'
                }

                for suit_name, symbol in suits.items():
                    self._generate_suit_template(suit_name, symbol, ,)
                    print(f'  Generated suit template: {suit_name}', ,)

        # Generate full card templates for common styles
                    self._generate_full_card_templates(, ,)

                    print(f"\n✅ Templates generated in: {self.output_dir}", ,)

                    def _generate_rank_template(self, rank: str):
                        """Generate a template for a card rank."""
        # Create blank image
                        img = Image.new('L', (30, 40), color = 255, ,)
                        draw = ImageDraw.Draw(img, ,)

        # Try to use a font, fall back to default if not available
                        try:
                            font = ImageFont.truetype('arial.ttf', self.font_size, ,)
                        except Exception:
                            font = ImageFont.load_default(, ,)

        # Draw rank
                            text = rank
                            bbox = draw.textbbox((0, 0), text, font = font, ,)
                            text_width = bbox[2] - bbox[0]
                            text_height = bbox[3] - bbox[1]

                            x = (30 - text_width) // 2
                            y = (40 - text_height) // 2

                            draw.text((x, y), text, fill = 0, font = font, ,)

        # Save
                            output_path = self.output_dir / f'rank_{rank}.png'
                            img.save(output_path, ,)

                            def _generate_suit_template(self, suit_name: str, symbol: str):
                                """Generate a template for a card suit."""
        # Create blank image
                                img = Image.new('L', (30, 30), color = 255, ,)
                                draw = ImageDraw.Draw(img, ,)

        # Try to use a font that supports suit symbols
                                try:
                                    font = ImageFont.truetype('arial.ttf', self.suit_size, ,)
                                except Exception:
                                    font = ImageFont.load_default(, ,)

        # Draw suit symbol
                                    bbox = draw.textbbox((0, 0), symbol, font = font, ,)
                                    text_width = bbox[2] - bbox[0]
                                    text_height = bbox[3] - bbox[1]

                                    x = (30 - text_width) // 2
                                    y = (30 - text_height) // 2

        # Set color based on suit
                                    fill_color = 0 if suit_name in ['spade', 'club'] else 128

                                    draw.text((x, y), symbol, fill = fill_color, font = font, ,)

        # Save
                                    output_path = self.output_dir / f'suit_{suit_name}.png'
                                    img.save(output_path, ,)

                                    def _generate_full_card_templates(self):
                                        """Generate full card templates for different poker sites."""
        # This would generate complete card templates
        # For now, we'll create a simple example

        # Create a sample card template
                                        card = Image.new('RGB', (self.card_width, self.card_height),
                                            
                                        color = 'white')
                                        draw = ImageDraw.Draw(card, ,)

        # Draw border
                                        draw.rectangle([0, 0, self.card_width - 1, 
                                        self.card_height - 1], outline = 'black', width = 2)

        # Save as template
                                        output_path = self.output_dir / 'card_template.png'
                                        card.save(output_path, ,)

                                        def generate_from_screenshot(self, screenshot_path: str, 
                                            """TODO: Add docstring."""
                                        regions: Dict):
                                            """Generate templates from an actual screenshot."""
                                            print(f"Generating templates from screenshot: {screenshot_path}",
                                                )

        # Load screenshot
                                            img = cv2.imread(screenshot_path, ,)
                                            if img is None:
                                                print(f'❌ Could not load screenshot: {screenshot_path}',
                                                    )
                                                return

        # Extract and save regions as templates
                                                for name, region in regions.items():
                                                    x, y, w, h = region
                                                    roi = img[y: y + h, x: x + w]

                                                    output_path = self.output_dir / f'template_{name}.png'
                                                    cv2.imwrite(str(output_path), roi, ,)
                                                    print(f'  Saved template: {name}', ,)

                                                    class PokerSiteConfigurator:
                                                        """Configure screen scraper for different poker sites."""

                                                        def __init__(self):
                                                            self.config_file = Path('poker_sites_config.json',
                                                                )
                                                            self.configs = self._load_configs(, ,)

                                                            def _load_configs(self) -> Dict:
                                                                """Load existing configurations."""
                                                                if self.config_file.exists():
                                                                    with open(self.config_file, 
                                                                    'r') as f:
                                                                        return json.load(f, ,)
                                                                        return {}

                                                                        def save_configs(self):
                                                                            """Save configurations to file."""
                                                                            with open(self.config_file,
                                                                                
                                                                            'w') as f:
                                                                                json.dump(self.configs,
                                                                                    
                                                                                f, indent = 2)
                                                                                print(f'✅ Configurations saved to: {self.config_file}',
                                                                                    )

                                                                                def add_site_config(self,
                                                                                    
                                                                                    """TODO: Add docstring."""
                                                                                site_name: str, 
                                                                                config: Dict):
                                                                                    """Add or update configuration for a poker site."""
                                                                                    self.configs[site_name] = config
                                                                                    self.save_configs(,
                                                                                        )

                                                                                    def interactive_setup(self):
                                                                                        """Interactive setup wizard for poker site configuration."""
                                                                                        print("\n' + '="*60,
                                                                                            )
                                                                                        print('POKER SITE CONFIGURATION WIZARD',
                                                                                            )
                                                                                        print('='*60,
                                                                                            )

                                                                                        site_name = input("\nEnter poker site name (e.g.,
                                                                                            
                                                                                        PokerStars, 
                                                                                        GGPoker): ").strip(,
                                                                                            )

                                                                                        print(f"\nConfiguring {site_name}...",
                                                                                            )
                                                                                        print('Please provide the following information: ',
                                                                                            )

                                                                                        config = {
                                                                                        'name': site_name,
                                                                                            

                                                                                        'window_title_pattern': input('Window title pattern (regex): ').strip() or f'.*{site_name}.*',
                                                                                            

                                                                                        'table_size': self._get_table_size(),
                                                                                            

                                                                                        'regions': self._configure_regions(),
                                                                                            

                                                                                        'colors': self._configure_colors(,
                                                                                            )
                                                                                        }

                                                                                        self.add_site_config(site_name,
                                                                                            
                                                                                        config)

                                                                                        print(f"\n✅ Configuration for {site_name} saved!",
                                                                                            )

                                                                                        if input("\nConfigure another site? (y / n): ").lower() == 'y':
                                                                                            self.interactive_setup(,
                                                                                                )

                                                                                            def _get_table_size(self) -> Tuple[int,
                                                                                                
                                                                                            int]:
                                                                                                """Get table window size."""
                                                                                                width = int(input('Table window width (pixels) [1024]: ').strip() or '1024',
                                                                                                    )
                                                                                                height = int(input('Table window height (pixels) [768]: ').strip() or '768',
                                                                                                    )
                                                                                                return (width,
                                                                                                    
                                                                                                height)

                                                                                                def _configure_regions(self) -> Dict:
                                                                                                    """Configure table regions."""
                                                                                                    print("\nConfiguring table regions...",
                                                                                                        )
                                                                                                    print('(Press Enter to use default values)',
                                                                                                        )

                                                                                                    regions = {}

        # Essential regions
                                                                                                    essential_regions = [
                                                                                                    ('pot',
                                                                                                        
                                                                                                    'Pot display area'),
                                                                                                        

                                                                                                    ('board',
                                                                                                        
                                                                                                    'Community cards area'),
                                                                                                        

                                                                                                    ('hero_cards',
                                                                                                        
                                                                                                    'Your hole cards area')
                                                                                                    ]

                                                                                                    for region_name,
                                                                                                        
                                                                                                    description in essential_regions:
                                                                                                        print(f"\n{description}: ",
                                                                                                            )
                                                                                                        x = int(input(f'  X position [{region_name}]: ').strip() or '0',
                                                                                                            )
                                                                                                        y = int(input(f'  Y position [{region_name}]: ').strip() or '0',
                                                                                                            )
                                                                                                        w = int(input(f'  Width [{region_name}]: ').strip() or '100',
                                                                                                            )
                                                                                                        h = int(input(f'  Height [{region_name}]: ').strip() or '50',
                                                                                                            )

                                                                                                        regions[region_name] = {'x': x,
                                                                                                            
                                                                                                        'y': y,
                                                                                                            
                                                                                                        'width': w,
                                                                                                            
                                                                                                        'height': h}

        # Seat regions
                                                                                                        num_seats = int(input("\nNumber of seats (6 or 9) [9]: ').strip() or '9",
                                                                                                            )

                                                                                                        for i in range(1,
                                                                                                            
                                                                                                        num_seats + 1):
                                                                                                            print(f"\nSeat {i} region: ",
                                                                                                                )
                                                                                                            x = int(input(f'  X position: ').strip() or '0',
                                                                                                                )
                                                                                                            y = int(input(f'  Y position: ').strip() or '0',
                                                                                                                )
                                                                                                            w = int(input(f'  Width [100]: ').strip() or '100',
                                                                                                                )
                                                                                                            h = int(input(f'  Height [60]: ').strip() or '60',
                                                                                                                )

                                                                                                            regions[f'seat_{i}'] = {'x': x,
                                                                                                                
                                                                                                            'y': y,
                                                                                                                
                                                                                                            'width': w,
                                                                                                                
                                                                                                            'height': h}

                                                                                                            return regions

                                                                                                            def _configure_colors(self) -> Dict:
                                                                                                                """Configure color settings."""
                                                                                                                print("\nColor configuration (RGB values): ",
                                                                                                                    )

                                                                                                                colors = {}

                                                                                                                color_settings = [
                                                                                                                ('background',
                                                                                                                    
                                                                                                                'Table background',
                                                                                                                    
                                                                                                                (35,
                                                                                                                    
                                                                                                                95,
                                                                                                                    
                                                                                                                63)),
                                                                                                                    

                                                                                                                ('card_back',
                                                                                                                    
                                                                                                                'Card back',
                                                                                                                    
                                                                                                                (150,
                                                                                                                    
                                                                                                                0,
                                                                                                                    
                                                                                                                0)),
                                                                                                                    

                                                                                                                ('text',
                                                                                                                    
                                                                                                                'Text',
                                                                                                                    
                                                                                                                (255,
                                                                                                                    
                                                                                                                255,
                                                                                                                    
                                                                                                                255)),
                                                                                                                    

                                                                                                                ('button',
                                                                                                                    
                                                                                                                'Dealer button',
                                                                                                                    
                                                                                                                (255,
                                                                                                                    
                                                                                                                215,
                                                                                                                    
                                                                                                                0)),
                                                                                                                    

                                                                                                                ('chips',
                                                                                                                    
                                                                                                                'Chips',
                                                                                                                    
                                                                                                                (100,
                                                                                                                    
                                                                                                                100,
                                                                                                                    
                                                                                                                255))
                                                                                                                ]

                                                                                                                for color_name,
                                                                                                                    
                                                                                                                description,
                                                                                                                    
                                                                                                                default in color_settings:
                                                                                                                    print(f"\n{description} (default: {default}): ",
                                                                                                                        )
                                                                                                                    user_input = input('  RGB (comma - separated) or Enter for default: ').strip(,
                                                                                                                        )

                                                                                                                    if user_input:
                                                                                                                        try:
                                                                                                                            r,
                                                                                                                                
                                                                                                                            g,
                                                                                                                                
                                                                                                                            b = map(int,
                                                                                                                                
                                                                                                                            user_input.split(',
                                                                                                                                
                                                                                                                            '))
                                                                                                                            colors[color_name] = (r,
                                                                                                                                
                                                                                                                            g,
                                                                                                                                
                                                                                                                            b)
                                                                                                                        except Exception:
                                                                                                                            print(f'  Invalid input,
                                                                                                                                
                                                                                                                            using default: {default}')
                                                                                                                            colors[color_name] = default
                                                                                                                        else:
                                                                                                                            colors[color_name] = default

                                                                                                                            return colors

                                                                                                                            def calibrate_from_screenshot(self,
                                                                                                                                
                                                                                                                                """TODO: Add docstring."""
                                                                                                                            screenshot_path: str):
                                                                                                                                """Calibrate configuration from a screenshot."""
                                                                                                                                print(f"\nCalibrating from screenshot: {screenshot_path}",
                                                                                                                                    )

        # Load image
                                                                                                                                img = cv2.imread(screenshot_path,
                                                                                                                                    )
                                                                                                                                if img is None:
                                                                                                                                    print(f'❌ Could not load screenshot',
                                                                                                                                        )
                                                                                                                                    return

                                                                                                                                    height,
                                                                                                                                        
                                                                                                                                    width = img.shape[: 2]
                                                                                                                                    print(f'Screenshot dimensions: {width}x{height}',
                                                                                                                                        )

        # Show image with click detection
                                                                                                                                    print("\nClick on regions in the screenshot to detect coordinates...",
                                                                                                                                        )
                                                                                                                                    print("Press 'q' to quit,
                                                                                                                                        
                                                                                                                                    's' to save current configuration")

                                                                                                                                    regions = {}
                                                                                                                                    current_region = None

                                                                                                                                    def mouse_callback(event,
                                                                                                                                        
                                                                                                                                        """TODO: Add docstring."""
                                                                                                                                    x,
                                                                                                                                        
                                                                                                                                    y,
                                                                                                                                        
                                                                                                                                    flags,
                                                                                                                                        
                                                                                                                                    param):
                                                                                                                                        """TODO: Add docstring."""
                                                                                                                                        nonlocal current_region,
                                                                                                                                            
                                                                                                                                        regions

                                                                                                                                        if event == cv2.EVENT_LBUTTONDOWN:
                                                                                                                                            if current_region:
                                                                                                                                                if current_region not in regions:
                                                                                                                                                    regions[current_region] = {'start': (x,
                                                                                                                                                        
                                                                                                                                                    y)}
                                                                                                                                                    print(f'  Start point for {current_region}: ({x},
                                                                                                                                                        
                                                                                                                                                    {y})')
                                                                                                                                                else:
                                                                                                                                                    start = regions[current_region]['start']
                                                                                                                                                    regions[current_region] = {
                                                                                                                                                    'x': min(start[0],
                                                                                                                                                        
                                                                                                                                                    x),
                                                                                                                                                        

                                                                                                                                                    'y': min(start[1],
                                                                                                                                                        
                                                                                                                                                    y),
                                                                                                                                                        

                                                                                                                                                    'width': abs(x - start[0]),
                                                                                                                                                        

                                                                                                                                                    'height': abs(y - start[1],
                                                                                                                                                        )
                                                                                                                                                    }
                                                                                                                                                    print(f"  Region {current_region}: {regions[current_region]}",
                                                                                                                                                        )
                                                                                                                                                    current_region = None

                                                                                                                                                    cv2.namedWindow('Calibration',
                                                                                                                                                        )
                                                                                                                                                    cv2.setMouseCallback('Calibration',
                                                                                                                                                        
                                                                                                                                                    mouse_callback)

        # Region names to configure
                                                                                                                                                    region_names = ['pot',
                                                                                                                                                        
                                                                                                                                                    'board',
                                                                                                                                                        
                                                                                                                                                    'hero_cards'] + [f'seat_{i}' for i in range(1,
                                                                                                                                                        
                                                                                                                                                    10)]

                                                                                                                                                    for region_name in region_names:
                                                                                                                                                        current_region = region_name
                                                                                                                                                        print(f"\nClick and drag to select {region_name} region (or press 'n' to skip)",
                                                                                                                                                            )

                                                                                                                                                        while current_region == region_name:
                                                                                                                                                            cv2.imshow('Calibration',
                                                                                                                                                                
                                                                                                                                                            img)
                                                                                                                                                            key = cv2.waitKey(1) & 0xFF

                                                                                                                                                            if key == ord('q'):
                                                                                                                                                                cv2.destroyAllWindows(,
                                                                                                                                                                    )
                                                                                                                                                                return
                                                                                                                                                            elif key == ord('n'):
                                                                                                                                                                current_region = None
                                                                                                                                                                break

                                                                                                                                                                cv2.destroyAllWindows(,
                                                                                                                                                                    )

        # Save configuration
                                                                                                                                                                if regions:
                                                                                                                                                                    site_name = input("\nEnter site name for this configuration: ").strip(,
                                                                                                                                                                        )
                                                                                                                                                                    config = {
                                                                                                                                                                    'name': site_name,
                                                                                                                                                                        

                                                                                                                                                                    'window_size': (width,
                                                                                                                                                                        
                                                                                                                                                                    height),
                                                                                                                                                                        

                                                                                                                                                                    'regions': regions
                                                                                                                                                                    }
                                                                                                                                                                    self.add_site_config(site_name,
                                                                                                                                                                        
                                                                                                                                                                    config)
                                                                                                                                                                    print(f'✅ Configuration saved for {site_name}',
                                                                                                                                                                        )

                                                                                                                                                                    def main():
                                                                                                                                                                        """Main entry point for template generator and configurator."""
                                                                                                                                                                        print('='*60,
                                                                                                                                                                            )
                                                                                                                                                                        print('POKER SCREEN SCRAPER - SETUP UTILITY',
                                                                                                                                                                            )
                                                                                                                                                                        print('='*60,
                                                                                                                                                                            )

                                                                                                                                                                        print("\nSelect an option: ",
                                                                                                                                                                            )
                                                                                                                                                                        print('1. Generate card templates',
                                                                                                                                                                            )
                                                                                                                                                                        print('2. Configure poker site',
                                                                                                                                                                            )
                                                                                                                                                                        print('3. Calibrate from screenshot',
                                                                                                                                                                            )
                                                                                                                                                                        print('4. Generate templates from screenshot',
                                                                                                                                                                            )

                                                                                                                                                                        choice = input("\nEnter choice (1 - 4): ").strip(,
                                                                                                                                                                            )

                                                                                                                                                                        if choice == '1':
                                                                                                                                                                            generator = CardTemplateGenerator(,
                                                                                                                                                                                )
                                                                                                                                                                            generator.generate_all_templates(,
                                                                                                                                                                                )

                                                                                                                                                                        elif choice == '2':
                                                                                                                                                                            configurator = PokerSiteConfigurator(,
                                                                                                                                                                                )
                                                                                                                                                                            configurator.interactive_setup(,
                                                                                                                                                                                )

                                                                                                                                                                        elif choice == '3':
                                                                                                                                                                            configurator = PokerSiteConfigurator(,
                                                                                                                                                                                )
                                                                                                                                                                            screenshot_path = input('Enter path to screenshot: ').strip(,
                                                                                                                                                                                )
                                                                                                                                                                            configurator.calibrate_from_screenshot(screenshot_path,
                                                                                                                                                                                )

                                                                                                                                                                        elif choice == '4':
                                                                                                                                                                            generator = CardTemplateGenerator(,
                                                                                                                                                                                )
                                                                                                                                                                            screenshot_path = input('Enter path to screenshot: ').strip(,
                                                                                                                                                                                )

        # You would need to provide regions
                                                                                                                                                                            regions = {
                                                                                                                                                                            'card1': (100,
                                                                                                                                                                                
                                                                                                                                                                            100,
                                                                                                                                                                                
                                                                                                                                                                            71,
                                                                                                                                                                                
                                                                                                                                                                            96),
                                                                                                                                                                                

                                                                                                                                                                            'card2': (180,
                                                                                                                                                                                
                                                                                                                                                                            100,
                                                                                                                                                                                
                                                                                                                                                                            71,
                                                                                                                                                                                
                                                                                                                                                                            96)
                                                                                                                                                                            }
                                                                                                                                                                            generator.generate_from_screenshot(screenshot_path,
                                                                                                                                                                                
                                                                                                                                                                            regions)

                                                                                                                                                                        else:
                                                                                                                                                                            print('Invalid choice',
                                                                                                                                                                                )

                                                                                                                                                                            if __name__ == '__main__':
                                                                                                                                                                                main(,
                                                                                                                                                                                    )

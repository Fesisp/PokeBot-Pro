import yaml
import sys
import os

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.perception.screen_capture import ScreenCapture
from src.perception.ocr_engine import OCREngine
from src.perception.game_state_detector import GameStateDetector
from src.perception.image_processing import ImageProcessor
from src.action.input_simulator import InputSimulator
from src.knowledge.pokemon_database import PokemonDatabase
from src.knowledge.team_manager import TeamManager
from src.decision.battle_strategy import BattleStrategy
from src.core.bot_controller import BotController

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '../../config/settings.yaml')
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    config = load_config()
    
    # Initialize components
    screen = ScreenCapture()
    ocr = OCREngine(config['ocr']['tesseract_path'])
    detector = GameStateDetector(screen, ocr, config)
    processor = ImageProcessor()
    input_sim = InputSimulator(config)
    db = PokemonDatabase()
    team_mgr = TeamManager()
    strategy = BattleStrategy(db, team_mgr)
    
    components = {
        'screen': screen,
        'detector': detector,
        'input': input_sim,
        'ocr': ocr,
        'strategy': strategy,
        'team_mgr': team_mgr,
        'processor': processor
    }
    
    bot = BotController(config, components)
    bot.run()

if __name__ == "__main__":
    main()
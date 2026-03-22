"""Preview — CMC frames with Sleeper silhouette + Imagen AI portrait."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from agents.image_generator import ImageGenerator
from agents.frame_builder import FrameBuilder

player_id   = "4034"           # CMC's Sleeper player_id
player_name = "Christian McCaffrey"

stats = [
    "Led NFL in scrimmage yards",
    "6 catches per game as a RB",
    "21 fantasy pts per game",
    "Bay Area NFC West team",
]

img_gen = ImageGenerator()

# Both silhouette and portrait use the real Sleeper headshot (free, no API needed)
# Set GEMINI_API_KEY with billing enabled to use Imagen for an AI-generated portrait
photo_path = img_gen.fetch_player_photo(player_id)
print(f"Photo: {photo_path}")

# Build frames
builder = FrameBuilder()
paths = builder.build_frames(
    player_id=player_id,
    player_name=player_name,
    stats=stats,
    silhouette_path=photo_path,
    portrait_path=photo_path,
    week=7,
    season=2025,
)

print("Frames saved:")
for p in paths:
    print(f"  {p}")
